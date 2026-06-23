__author__ = 'aluex'

import os
import base64
from gevent import monkey

from gevent import Greenlet
from gevent.queue import Queue
from .bkr_acs import acs
from .utils import mylog, MonitoredInt, callBackWrap, greenletFunction, \
    greenletPacker, getEncKeys, Transaction, getECDSAKeys, sha1hash
from collections import defaultdict
import zfec
import hashlib

from ..sgx.cryptor import Cryptor
from .utils import deserializeEnc, ENC_SERIALIZED_LENGTH
import random
import itertools
import gevent

monkey.patch_all()

_SGX_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SGX_DATA_DIR = os.path.join(_SGX_BASE_DIR, 'sgx')
_TR_SIZE = 250

_sgx_tx_cryptor = Cryptor()


def calcSum(dd):
    return sum([x for _, x in dd.items()])


def calcMajority(dd):
    maxvalue = -1
    maxkey = dd.values()[0]
    for key, value in dd.items():
        if value > maxvalue:
            maxvalue = value
            maxkey = key
    return maxkey


Pubkeys = defaultdict(lambda: Queue(1))


class dummyPKI(object):
    @staticmethod
    def get_verifying_key():
        return None


class ECDSASignatureError(Exception):
    pass


import math


def ceil(x):
    return int(math.ceil(x))


def dummyHash(x):  # TODO: replace this guy with good ones
    if isinstance(x, str):
        return int(x.encode().hex(), 16)
    return x + 1


def coolSHA256Hash(x):
    if isinstance(x, int): x = str(x)
    return hashlib.sha256(x).digest()


#####################
#    Merkle tree    #
#####################
def hash(x):
    assert isinstance(x, (str, bytes))
    try:
        x = x.encode()
    except AttributeError:
        pass
    return hashlib.sha256(x).digest()


@greenletFunction
def multiSigBr(pid, N, t, msg, broadcast, receive, outputs, send):
    # Since all the parties we have are symmetric, so I implement this function for N instances of A-cast as a whole
    # Here msg is a set of transactions
    assert (isinstance(outputs, list))
    for i in outputs:
        assert (isinstance(i, Queue))

    keys = getECDSAKeys()
    K = Threshold = N - 2 * t
    Threshold2 = N - t
    zfecEncoder = zfec.Encoder(Threshold, N)
    zfecDecoder = zfec.Decoder(Threshold, N)

    # Merkle Tree
    def merkleTree(strList):
        N = len(strList)
        assert N >= 1
        bottomrow = 2 ** ceil(math.log(N, 2))
        mt = [b''] * (2 * bottomrow)
        for i in range(N):
            mt[bottomrow + i] = hash(strList[i])
        for i in range(bottomrow - 1, 0, -1):
            mt[i] = hash(mt[i * 2] + mt[i * 2 + 1])
        return mt

    def getMerkleBranch(index, mt):
        """
        Computes a merkle tree from a list of leaves.
        """
        res = []
        t = index + (len(mt) >> 1)
        while t > 1:
            res.append(mt[t ^ 1])  # we are picking up the sibling
            t //= 2
        return res

    def merkleVerify(val, roothash, branch, index):
        """
        Verify a merkle tree branch proof
        """
        assert 0 <= index < N
        # XXX Python 3 related issue, for now let's tolerate both bytes and
        # strings
        assert isinstance(val, (str, bytes))
        assert len(branch) == ceil(math.log(N, 2))
        # Index has information on whether we are facing a left sibling or a right sibling
        tmp = hash(val)
        tindex = index
        for br in branch:
            tmp = hash((tindex & 1) and br + tmp or tmp + br)
            tindex >>= 1
        if tmp != roothash:
            print("Verification failed with", hash(val), roothash, branch, tmp == roothash)
            return False
        # print("Verified successfully.")

        return True

    def Listener():
        opinions = [defaultdict(lambda: 0) for _ in range(N)]
        rootHashes = dict()
        readyCounter = [defaultdict(lambda: 0) for _ in range(N)]
        signed = [False] * N
        readySent = [False] * N
        reconstDone = [False] * N
        while True:  # main loop
            sender, msgBundle = receive()
            if isinstance(msgBundle, tuple) and len(msgBundle) > 0 and msgBundle[0] == 'i' and not signed[sender]:

                if keys[sender].verify(
                        sha1hash(b''.join([msgBundle[1][0], msgBundle[1][1], b''.join(msgBundle[1][2])])),
                        msgBundle[2]):
                    assert isinstance(msgBundle[1], tuple)
                    if not merkleVerify(msgBundle[1][0], msgBundle[1][1], msgBundle[1][2], pid):
                        continue
                    if sender in rootHashes:
                        if rootHashes[sender] != msgBundle[1][1]:
                            print("Cheating caught, exiting")
                            sys.exit(0)
                    else:
                        rootHashes[sender] = msgBundle[1][1]
                    newBundle = (
                        sender, msgBundle[1][0], msgBundle[1][1],
                        msgBundle[1][2])  # assert each frag has a length of step
                    # print(type(newBundle[1]))
                    # print(newBundle[3])
                    # print(type(newBundle[3]))
                    broadcast(('e', newBundle, keys[pid].sign(
                        sha1hash(b''.join([bytes(newBundle[0]), newBundle[1], newBundle[2], b''.join(newBundle[3])]))
                    )))
                    signed[sender] = True
                else:
                    raise ECDSASignatureError()
            elif msgBundle[0] == 'e':

                if keys[sender].verify(sha1hash(b''.join(
                        [bytes(msgBundle[1][0]), msgBundle[1][1], msgBundle[1][2], b''.join(msgBundle[1][3])])),
                        msgBundle[2]):
                    originBundle = msgBundle[1]
                    if not merkleVerify(originBundle[1], originBundle[2], originBundle[3], sender):
                        continue
                    if originBundle[0] in rootHashes:
                        if rootHashes[originBundle[0]] != originBundle[2]:
                            print("Cheating caught, exiting")
                            sys.exit(0)
                    else:
                        rootHashes[originBundle[0]] = originBundle[2]
                    opinions[originBundle[0]][sender] = originBundle[
                        1]  # We are going to move this part to kekeketktktktk
                    if len(opinions[originBundle[0]]) >= Threshold2 and not readySent[originBundle[0]]:
                        readySent[originBundle[0]] = True
                        broadcast(('r', originBundle[0], originBundle[2]))  # We are broadcasting its hash
                else:
                    raise ECDSASignatureError()
            elif msgBundle[0] == 'r':
                readyCounter[msgBundle[1]][msgBundle[2]] += 1
                tmp = readyCounter[msgBundle[1]][msgBundle[2]]
                if tmp >= t + 1:
                    result = 1
                elif tmp >= Threshold2:
                    result = 2
                else:
                    result = 0

                if result == 1 and not readySent[msgBundle[1]]:  # Aux message
                    readySent[msgBundle[1]] = True
                    broadcast(('r', msgBundle[1], msgBundle[2]))
                if (result == 1 or result == 2 and
                        not outputs[msgBundle[1]].full() and
                        not reconstDone[msgBundle[1]] and
                        len(opinions[msgBundle[1]]) >= Threshold):
                    reconstDone[msgBundle[1]] = True
                    if msgBundle[1] in rootHashes:
                        if rootHashes[msgBundle[1]] != msgBundle[2]:
                            print("Cheating caught, exiting")
                            sys.exit(0)
                    else:
                        rootHashes[msgBundle[1]] = msgBundle[2]
                    if list(opinions[msgBundle[1]].values())[0] == '':
                        reconstruction = ['']
                    else:
                        reconstruction = zfecDecoder.decode(list(opinions[msgBundle[1]].values())[:Threshold],
                                                            list(opinions[msgBundle[1]].keys())[
                                                            :Threshold])  # We only take the first [Threshold] fragments
                        gevent.sleep(0)  # yield after zfec decode

                    m = b''.join(reconstruction)
                    padlen = m[-1]
                    m = m[:-padlen]
                    unpadded = m
                    buf = m

                    assert K <= 256  # TODO: Record this assumption!
                    # re-pad for merkle verification (same as sender)
                    repadlen = K - (len(buf) % K)
                    buf = buf + repadlen * chr(repadlen).encode()
                    step = len(buf) // K
                    blocks = [buf[i * step: (i + 1) * step] for i in range(K)]
                    encodedFragList = zfecEncoder.encode(blocks)
                    mt = merkleTree(encodedFragList)
                    gevent.sleep(0)  # yield after zfec encode

                    assert rootHashes[msgBundle[1]] == mt[1]  # full binary tree
                    if outputs[msgBundle[1]].empty():
                        outputs[msgBundle[1]].put(unpadded)

    greenletPacker(Greenlet(Listener), 'multiSigBr.Listener', (pid, N, t, msg, broadcast, receive, outputs)).start()
    buf = msg  # We already assumed the proposals are byte strings

    assert K <= 256  # TODO: Record this assumption!
    # pad m to a multiple of K bytes
    padlen = K - (len(buf) % K)
    buf += padlen * chr(padlen).encode()
    step = len(buf) // K

    blocks = [buf[i * step: (i + 1) * step] for i in range(K)]
    encodedFragList = zfecEncoder.encode(blocks)

    # 构建 Merkle 树
    mt = merkleTree(encodedFragList)
    rootHash = mt[1]  # full binary tree
    for i in range(N):
        mb = getMerkleBranch(i, mt)  # notice that index starts from 1 and pid starts from 0
        newBundle = (encodedFragList[i], rootHash, mb)
        # 签名发送
        send(i,
             ('i', newBundle, keys[pid].sign(sha1hash(b''.join([newBundle[0], newBundle[1], b''.join(newBundle[2])])))))
        gevent.sleep(0)  # yield to allow socket handlers to run


@greenletFunction
def consensusBroadcast(pid, N, t, msg, broadcast, receive, outputs, send, method=multiSigBr):
    return method(pid, N, t, msg, broadcast, receive, outputs, send)


def union(listOfTXSet):
    result = set()  # Informal Union: actually we don't know how it compares ...
    for s in listOfTXSet:
        result = result.union(s)
    return result


# tx is the transaction we are going to include
@greenletFunction
def includeTransaction(pid, N, t, setToInclude, broadcast, receive, send):
    CBChannel = Queue()
    ACSChannel = Queue()
    TXSet = [{} for _ in range(N)]

    def make_bc_br(i):
        def _bc_br(m):
            broadcast(('B', m))

        return _bc_br

    def make_acs_br(i):
        def _acs_br(m):
            broadcast(('A', m))

        return _acs_br

    def make_bc_send(i):
        def _layer_send(j, m):
            send(j, ('B', m))

        return _layer_send

    def _listener():
        while True:
            sender, (tag, m) = receive()
            if tag == 'B':
                CBChannel.put((sender, m))
            elif tag == 'A':
                ACSChannel.put((sender, m))

    outputChannel = [Queue(1) for _ in range(N)]

    def outputCallBack(i):
        TXSet[i] = outputChannel[i].get()
        monitoredIntList[i].data = 1

    for i in range(N):
        greenletPacker(Greenlet(outputCallBack, i),
                       'includeTransaction.outputCallBack', (pid, N, t, setToInclude, broadcast, receive)).start()

    def callbackFactoryACS():
        def _callback(commonSet):  # now I know player j has succeeded in broadcasting
            locker.put(commonSet)

        return _callback

    greenletPacker(Greenlet(_listener),
                   'includeTransaction._listener', (pid, N, t, setToInclude, broadcast, receive)).start()

    locker = Queue(1)
    includeTransaction.callbackCounter = 0
    monitoredIntList = [MonitoredInt() for _ in range(N)]

    greenletPacker(Greenlet(consensusBroadcast, pid, N, t, setToInclude, make_bc_br(pid), CBChannel.get, outputChannel,
                            make_bc_send(pid)),
                   'includeTransaction.consensusBroadcast', (pid, N, t, setToInclude, broadcast, receive)).start()
    greenletPacker(Greenlet(callBackWrap(acs, callbackFactoryACS()), pid, N, t, monitoredIntList, make_acs_br(pid),
                            ACSChannel.get),
                   'includeTransaction.callBackWrap(acs, callbackFactoryACS())',
                   (pid, N, t, setToInclude, broadcast, receive)).start()

    commonSet = locker.get()

    # print("TXSet ---> ", TXSet)
    return commonSet, TXSet


HONEST_PARTY_TIMEOUT = 1

import time, sys

lock = Queue()
finishcount = 0
lock.put(1)

cryptor = Cryptor()
aes_key = _sgx_tx_cryptor.load_aes_key_from_file(
    os.path.join(_SGX_DATA_DIR, "aes.key")
)


@greenletFunction
def honestParty(pid, N, t, controlChannel, broadcast, receive, send, B=-1):
    # RequestChannel is called by the client, and it is the client's duty to broadcast the tx it wants to include
    if B < 0:
        B = int(math.ceil(N * math.log(N)))
    transactionCache = []
    finishedTx = set()
    proposals = []
    receivedProposals = False
    commonSet = []
    locks = defaultdict(lambda: Queue(1))
    doneCombination = defaultdict(lambda: False)
    ENC_THRESHOLD = N - 2 * t
    global finishcount
    encPK, encSKs = getEncKeys()
    encCounter = defaultdict(lambda: {})
    includeTransactionChannel = Queue()

    def probe(i):
        # by == this part only executes once.
        if len(encCounter[i]) >= ENC_THRESHOLD and receivedProposals and not locks[i].full() and not doneCombination[i]:
            one, two, three, four, five, six = deserializeEnc(proposals[i][:ENC_SERIALIZED_LENGTH])

            '''oriM = encPK.combine_shares(deserializeEnc(proposals[i][:ENC_SERIALIZED_LENGTH]),
                                        dict(itertools.islice(encCounter[i].items() , ENC_THRESHOLD))
                                        )'''
            oriM = encPK.combine_shares(one, two, three, four, five, six,
                                        dict(itertools.islice(encCounter[i].items(), ENC_THRESHOLD)))
            doneCombination[i] = True
            # print(type(oriM))
            # time.sleep(60)
            locks[i].put(oriM)

    def listener():
        while True:
            sender, msgBundle = receive()

            if msgBundle[0] == 'O':
                encCounter[msgBundle[1]][sender] = msgBundle[2]
                probe(msgBundle[1])
            else:
                includeTransactionChannel.put((sender, msgBundle))  # redirect to includeTransaction

    Greenlet(listener).start()

    while True:
        op, msg = controlChannel.get()

        if op == "IncludeTransaction":
            if isinstance(msg, Transaction):
                transactionCache.append(msg)
            elif isinstance(msg, set):
                for tx in msg:
                    transactionCache.append(tx)
            elif isinstance(msg, list):
                transactionCache.extend(msg)
        elif op == "Halt":
            break
        elif op == "Msg":
            broadcast(eval(msg))

        mylog("timestampB (%d, %lf)" % (pid, time.time()), verboseLevel=-2)

        if len(transactionCache) < B:
            time.sleep(0.5)
            print("Not enough transactions", len(transactionCache))
            continue

        # 随机提案
        oldest_B = transactionCache[:B]
        selected_B = random.sample(oldest_B, int(min(B / N, len(oldest_B))))

        # RSA 加密
        encrypted_B = cryptor.encrypt_aes(b''.join(selected_B), aes_key)
        encryptedAESKey = cryptor.encrypt_rsa(aes_key)
        proposal = encryptedAESKey + encrypted_B

        # 门限加密
        # encrypted_B = encrypt(aesKey, b''.join(selected_B))
        # encryptedAESKey = encPK.encrypt(aesKey, label)
        # proposal = serializeEnc(encryptedAESKey).encode("ISO-8859-1") + encrypted_B

        # print("aes_key ---> ", aes_key)
        # print("encrypted_B ---> ", encrypted_B)
        # print("encryptedAESKey ---> ", encryptedAESKey)
        # print("proposal ---> ", proposal)
        # print("len(proposal) ---> ", len(proposal))
        # print("len(encrypted_B) ---> ", len(encrypted_B))

        # mylog("timestampIB (%d, %lf)" % (pid, time.time()), verboseLevel=-2)

        tb1 = time.time()  # beginning of the protocol

        commonSet, proposals = includeTransaction(pid, N, t, proposal, broadcast, includeTransactionChannel.get, send)
        # print("proposals ---> ", proposals)
        # mylog("timestampIE (%d, %lf)" % (pid, time.time()), verboseLevel=-2)
        receivedProposals = True

        ### todo: None-SGX
        # for i in range(N):
        #     probe(i)
        # mylog("timestampIE2 (%d, %lf)" % (pid, time.time()), verboseLevel=-2)
        recoveredSyncedTxList = []

        def prepareTx(i, c):
            if c != 1:
                recoveredSyncedTx = []
            else:
                aesKeyFromEncrypted = _sgx_tx_cryptor.decrypt_rsa(proposals[i][:256])
                encodedTxSet = _sgx_tx_cryptor.decrypt_aes(proposals[i][256:].rstrip(b'\x01'), aesKeyFromEncrypted)
                assert len(encodedTxSet) % _TR_SIZE == 0
                recoveredSyncedTx = [encodedTxSet[j:j + _TR_SIZE] for j in range(0, len(encodedTxSet), _TR_SIZE)]
            recoveredSyncedTxList.append(recoveredSyncedTx)

        thList = []
        for i, c in enumerate(commonSet):  # stx is the same for every party
            if c:
                s = Greenlet(prepareTx, i, c)
                thList.append(s)
                s.start()

        gevent.joinall(thList)

        # mylog("timestampE (%d, %lf)" % (pid, time.time()), verboseLevel=-2)

        for rtx in recoveredSyncedTxList:
            # print("rtx ----> ", rtx)
            finishedTx.update(set(rtx))

        mylog("[%d] %d distinct tx synced and %d tx left in the pool." % (
            pid, len(finishedTx), len(transactionCache) - len(finishedTx)), verboseLevel=-2)

        tb2 = time.time()
        print("[Finishing Time", str(pid) + "], ", tb2 - tb1)

        lock.get()
        finishcount += 1
        lock.put(1)
        # print '---finishcount %d'%(finishcount)
        if finishcount >= N - t:  # convenient for local experiments
            sys.exit()
    mylog("[%d] Now halting..." % (pid))

#!/usr/bin/python
"""
拜占庭节点测试 - 投票阶段始终投 0

与 honest_party_test_EC2.py 相同的分布式架构，但拜占庭节点：
- 正常参与协议（不崩溃、不掉线）
- 正常提案、正常广播、正常解密
- 在 ACS 二元共识投票时始终投 0（试图排除所有交易）

用法:
    # 拜占庭节点（运行这个脚本）
    python3 -m adaptive.test.byzantine_vote_test \\
        -k thsig4_1.keys -e ecdsa.keys -c thenc4_1.keys \\
        -s hosts -n 4 -t 1 -b 100 -v 1 -a 50 --my-id 3

    # 诚实节点（用原版脚本）
    python3 -m adaptive.test.honest_party_test_EC2 \\
        -k thsig4_1.keys -e ecdsa.keys -c thenc4_1.keys \\
        -s hosts -n 4 -t 1 -b 100 -v 1 -a 50 --my-id 0
"""

from gevent import monkey
monkey.patch_all()

import os
import sys
import math
import time
import struct
import socket
import base64
from collections import defaultdict
from random import Random
from optparse import OptionParser
from os.path import expanduser

import gevent
from gevent import Greenlet
from gevent.queue import Queue
from gevent.server import StreamServer
from socket import error as SocketError

from ..core.utils import (
    bcolors, mylog, initiateThresholdSig, initiateECDSAKeys, initiateThresholdEnc,
    getKeys, deepEncode, deepDecode, encodeTransaction, randomTransaction,
    ACSException, checkExceptionPerGreenlet, finishTransactionLeap, initiateRND,
    MonitoredInt, greenletPacker, getEncKeys, deserializeEnc, ENC_SERIALIZED_LENGTH,
    Transaction,
)
from ..core.bkr_acs import initBeforeBinaryConsensus
from ..core.broadcasts import local_binary_consensus
from ..core.includeTransaction import (
    honestParty, multiSigBr, consensusBroadcast,
    lock, finishcount as _finishcount_ref, _sgx_tx_cryptor, _TR_SIZE,
)
from ..sgx.cryptor import Cryptor
from ..commoncoin.thresprf_gipc import initialize as initializeGIPC

_SGX_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SGX_DATA_DIR = os.path.join(_SGX_BASE_DIR, 'sgx')
_aes_key = _sgx_tx_cryptor.load_aes_key_from_file(os.path.join(_SGX_DATA_DIR, "aes.key"))

# ============================================================================
# 网络层（与 honest_party_test_EC2.py 完全一致）
# ============================================================================

BASE_PORT = 49500
WAITING_SETUP_TIME_IN_SEC = 3

msgCounter = 0
totalMessageSize = 0
starting_time = defaultdict(lambda: 0.0)
ending_time = defaultdict(lambda: 0.0)
msgSize = defaultdict(lambda: 0)
msgFrom = defaultdict(lambda: 0)
msgTo = defaultdict(lambda: 0)
msgContent = defaultdict(lambda: '')
msgTypeCounter = [[0, 0] for _ in range(9)]
logChannel = Queue()


def goodread(f, length):
    ltmp = length
    buf = []
    while ltmp > 0:
        buf.append(f.read(ltmp))
        ltmp -= len(buf[-1])
    return b''.join(buf)


def listen_to_channel(port):
    mylog('Preparing server on %d...' % port)
    q = Queue()

    def _handle(socket, address):
        f = socket.makefile('rb')
        while True:
            msglength, = struct.unpack('<I', goodread(f, 4))
            line = goodread(f, msglength)
            obj = decode(line)
            q.put(obj[1:])

    server = StreamServer(('0.0.0.0', port), _handle)
    server.start()
    return q


def connect_to_channel(hostname, port, party):
    mylog('Trying to connect to %s for party %d' % (repr((hostname, port)), party), verboseLevel=-1)
    retry = True
    s = None
    while retry:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((hostname, port))
            retry = False
        except Exception as e:
            retry = True
            gevent.sleep(1)
            if s:
                s.close()
            mylog('retrying (%s, %d) caused by %s...' % (hostname, port, str(e)), verboseLevel=-1)
    q = Queue()

    def _handle():
        while True:
            obj = q.get()
            content = encode(obj)
            try:
                s.sendall(struct.pack('<I', len(content)) + content)
            except SocketError:
                print('!! [to %d] sending %d bytes' % (party, len(content)))

    gtemp = Greenlet(_handle)
    gtemp.parent_args = (hostname, port, party)
    gtemp.name = 'connect_to_channel._handle'
    gtemp.start()
    return q


def logWriter(fileHandler):
    while True:
        msgCounter, msgSize, msgFrom, msgTo, st, et, content = logChannel.get()
        fileHandler.write("%d:%d(%d->%d)[%s]-[%s]%s\n" % (msgCounter, msgSize, msgFrom, msgTo, st, et, content))
        fileHandler.flush()


def encode(m):
    global msgCounter
    msgCounter += 1
    starting_time[msgCounter] = str(time.time())
    result = deepEncode(msgCounter, m)
    msgSize[msgCounter] = len(result)
    msgFrom[msgCounter] = m[1]
    msgTo[msgCounter] = m[0]
    msgContent[msgCounter] = m
    if m[2][0] == 'A' and m[2][1][0] == 0:
        logChannel.put((msgCounter, len(result), m[1], m[0], starting_time[msgCounter], -1, 'i' + repr(m)))
    return result


def decode(s):
    result = deepDecode(s, msgTypeCounter)
    assert (isinstance(result, tuple))
    ending_time[result[0]] = str(time.time())
    msgContent[result[0]] = None
    msgFrom[result[0]] = result[1][1]
    msgTo[result[0]] = result[1][0]
    global totalMessageSize
    totalMessageSize += msgSize[result[0]]
    if result[1][2][0] == 'A' and result[1][2][1][0] == 0:
        logChannel.put((result[0], msgSize[result[0]], msgFrom[result[0]], msgTo[result[0]], -1, ending_time[result[0]],
                        'o' + repr(result[1])))
    return result[1]


# ============================================================================
# 拜占庭 ACS — 投票始终为 0
# ============================================================================

_cryptor_inst = Cryptor()


def byzantine_acs(pid, N, t, Q, broadcast, receive):
    """
    拜占庭版 ACS：与原版 bkr_acs.acs() 逻辑完全相同，
    唯一区别：callbackFactory 中投票值始终为 0。

    直接复制自 bkr_acs.py，修改了 callbackFactory 第54行：
        原版: encrypt_rsa((1).to_bytes(1, "big"))   → 投票 1
        拜占庭: encrypt_rsa((0).to_bytes(1, "big"))  → 投票 0
    """
    version = 1
    assert isinstance(Q, list) and len(Q) == N

    decideChannel = [Queue(1) for _ in range(N)]
    receivedChannelsFlags = []
    BA = [0] * N
    locker = Queue(1)
    locker2 = Queue(1)
    callbackCounter = [0]

    def callbackFactory(i):
        def _callback(val):
            if i not in receivedChannelsFlags:
                receivedChannelsFlags.append(i)
                if len(receivedChannelsFlags) >= N - t:
                    locker2.put("Key")
                if version == 1:
                    # ★ 拜占庭：始终投 0（原版这里是 (1)）
                    encrypted_vote = base64.b16encode(
                        _cryptor_inst.encrypt_rsa((0).to_bytes(1, "big"))
                    ).decode("utf-8")
                    greenletPacker(
                        Greenlet(local_binary_consensus, i, pid, N, t, encrypted_vote,
                                 decideChannel[i], make_bc(i), reliableBroadcastReceiveQueue[i].get),
                        'byzantine_acs.binary_consensus', (pid, N, t, Q, broadcast, receive)
                    ).start()
        return _callback

    for i, q in enumerate(Q):
        assert isinstance(q, MonitoredInt)
        q.registerSetCallBack(callbackFactory(i))

    def make_bc(i):
        def _bc(m):
            broadcast((i, m))
        return _bc

    reliableBroadcastReceiveQueue = [Queue() for _ in range(N)]

    def _listener():
        while True:
            sender, (instance, m) = receive()
            reliableBroadcastReceiveQueue[instance].put((sender, m))

    greenletPacker(Greenlet(_listener), 'byzantine_acs._listener', (pid, N, t, Q, broadcast, receive)).start()
    locker2.get()

    # 未收到提案的 slot 也投 0（与原版一致）
    for i in range(N):
        if i not in receivedChannelsFlags:
            receivedChannelsFlags.append(i)
            encrypted_vote = base64.b16encode(
                _cryptor_inst.encrypt_rsa((0).to_bytes(1, "big"))
            ).decode("utf-8")
            greenletPacker(
                Greenlet(local_binary_consensus, i, pid, N, t, encrypted_vote,
                         decideChannel[i], make_bc(i), reliableBroadcastReceiveQueue[i].get),
                'byzantine_acs.binary_consensus', (pid, N, t, Q, broadcast, receive)
            ).start()

    def listenerFactory(i, channel):
        def _listener():
            BA[i] = channel.get()
            callbackCounter[0] += 1
            if callbackCounter[0] >= N - t and not locker.full():
                locker.put("Key")
        return _listener

    for i in range(N):
        greenletPacker(
            Greenlet(listenerFactory(i, decideChannel[i])),
            'byzantine_acs.listenerFactory', (pid, N, t, Q, broadcast, receive)
        ).start()

    locker.get()
    return BA


# ============================================================================
# 拜占庭 honestParty — 调用 byzantine_acs 替代 acs
# ============================================================================
#
# 为什么不能简单猴子补丁：
#   includeTransaction.py 第9行: from .bkr_acs import acs
#   Python 的 import 机制将 acs 绑定为 includeTransaction 模块的本地变量。
#   即使我们修改 bkr_acs.acs，includeTransaction 内部调用的 acs 仍然指向
#   原始函数（因为局部变量在 import 时已经绑定）。
#
# 因此我们复制 honestParty 的逻辑，将 includeTransaction() 替换为内联的
# consensusBroadcast + byzantine_acs 调用。

import itertools
from ..core.includeTransaction import (
    CBChannel as _CB, ACSChannel as _ACS,
)


def byzantineVoteParty(pid, N, t, controlChannel, broadcast, receive, send, B=-1):
    """
    拜占庭节点 — 与 honestParty 逻辑完全相同，唯一区别：
    调用 byzantine_acs（投票始终为 0）替代原版 acs。
    """
    if B < 0:
        B = int(math.ceil(N * math.log(N)))

    transactionCache = []
    finishedTx = set()
    proposals = []
    receivedProposals = False
    commonSet = []

    from collections import defaultdict as dd
    locks = dd(lambda: Queue(1))
    doneCombination = dd(lambda: False)
    ENC_THRESHOLD = N - 2 * t

    import includeTransaction as _it_module
    global _finishcount
    _finishcount = 0

    encPK, encSKs = getEncKeys()
    encCounter = dd(lambda: {})
    includeTransactionChannel = Queue()

    def probe(i):
        if len(encCounter[i]) >= ENC_THRESHOLD and receivedProposals and not locks[i].full() and not doneCombination[i]:
            one, two, three, four, five, six = deserializeEnc(proposals[i][:ENC_SERIALIZED_LENGTH])
            oriM = encPK.combine_shares(one, two, three, four, five, six,
                                        dict(list(encCounter[i].items())[:ENC_THRESHOLD]))
            doneCombination[i] = True
            locks[i].put(oriM)

    def listener():
        while True:
            sender, msgBundle = receive()
            if msgBundle[0] == 'O':
                encCounter[msgBundle[1]][sender] = msgBundle[2]
                probe(msgBundle[1])
            else:
                includeTransactionChannel.put((sender, msgBundle))

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

        import random as _rnd
        oldest_B = transactionCache[:B]
        selected_B = _rnd.sample(oldest_B, int(min(B / N, len(oldest_B))))

        encrypted_B = _sgx_tx_cryptor.encrypt_aes(b''.join(selected_B), _aes_key)
        encryptedAESKey = _sgx_tx_cryptor.encrypt_rsa(_aes_key)
        proposal = encryptedAESKey + encrypted_B

        tb1 = time.time()

        # --- 内联 includeTransaction 逻辑，使用 byzantine_acs ---
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

        def _inner_listener():
            while True:
                sender, (tag, m) = receive()
                if tag == 'B':
                    greenletPacker(Greenlet(CBChannel.put, (sender, m)),
                                   'byzantineVoteParty.CBChannel.put', (pid, N, t)).start()
                elif tag == 'A':
                    greenletPacker(Greenlet(ACSChannel.put, (sender, m)),
                                   'byzantineVoteParty.ACSChannel.put', (pid, N, t)).start()

        outputChannel = [Queue(1) for _ in range(N)]

        def outputCallBack(i):
            TXSet[i] = outputChannel[i].get()
            monitoredIntList[i].data = 1

        for i in range(N):
            greenletPacker(Greenlet(outputCallBack, i),
                           'byzantineVoteParty.outputCallBack', (pid, N, t)).start()

        locker2 = Queue(1)

        def callbackFactoryACS():
            def _callback(commonSet):
                locker2.put(commonSet)
            return _callback

        greenletPacker(Greenlet(_inner_listener),
                       'byzantineVoteParty._inner_listener', (pid, N, t)).start()

        monitoredIntList = [MonitoredInt() for _ in range(N)]

        # 广播提案（正常）
        greenletPacker(Greenlet(consensusBroadcast, pid, N, t, proposal,
                                make_bc_br(pid), CBChannel.get, outputChannel,
                                make_bc_send(pid)),
                       'byzantineVoteParty.consensusBroadcast', (pid, N, t)).start()

        # ★ 拜占庭：使用 byzantine_acs（投票始终为 0）
        greenletPacker(Greenlet(byzantine_acs, pid, N, t, monitoredIntList,
                                make_acs_br(pid), ACSChannel.get),
                       'byzantineVoteParty.byzantine_acs', (pid, N, t)).start()

        commonSet = locker2.get()
        receivedProposals = True

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
        for i, c in enumerate(commonSet):
            if c:
                s = Greenlet(prepareTx, i, c)
                thList.append(s)
                s.start()

        gevent.joinall(thList)

        for rtx in recoveredSyncedTxList:
            finishedTx.update(set(rtx))

        mylog("[%d] %d distinct tx synced and %d tx left in the pool." % (
            pid, len(finishedTx), len(transactionCache) - len(finishedTx)), verboseLevel=-2)

        tb2 = time.time()
        print("[Finishing Time", str(pid) + "], ", tb2 - tb1)

        lock.get()
        _it_module.finishcount += 1
        lock.put(1)
        if _it_module.finishcount >= N - t:
            sys.exit()

    mylog("[%d] Now halting..." % (pid))


# ============================================================================
# 主测试逻辑
# ============================================================================

IP_LIST = None
IP_MAPPINGS = None


def prepareIPList(content):
    global IP_LIST, IP_MAPPINGS
    IP_LIST = content.strip().split('\n')
    IP_MAPPINGS = [(host, BASE_PORT) for host in IP_LIST if host]


def client_test_freenet(N, t, version, options):
    initiateThresholdSig(options.threshold_keys)
    initiateECDSAKeys(options.ecdsa)
    initiateThresholdEnc(options.threshold_encs)
    initializeGIPC(PK=getKeys()[0])

    global logGreenlet
    logGreenlet = Greenlet(logWriter, open('msglog.ByzantineVote', 'w'))
    logGreenlet.parent_args = (N, t)
    logGreenlet.name = 'client_test_freenet.logWriter'
    logGreenlet.start()

    print("================== Byzantine Vote Test ================")

    myID = options.myid
    N = len(IP_LIST)
    initiateRND(options.tx)

    def makeBroadcast(i):
        chans = []
        for j in range(N):
            host, port = IP_MAPPINGS[j]
            chans.append(connect_to_channel(host, port, i))

        def _broadcast(v):
            for j in range(N):
                chans[j].put((j, i, v))

        def _send(j, v):
            chans[j].put((j, i, v))

        return _broadcast, _send

    iterList = [myID]
    servers = []
    for i in iterList:
        _, port = IP_MAPPINGS[i]
        servers.append(listen_to_channel(port))
    print('servers started')

    gevent.sleep(WAITING_SETUP_TIME_IN_SEC)
    print('sleep over')

    initBeforeBinaryConsensus()
    ts = []
    controlChannels = [Queue() for _ in range(N)]
    bcList = dict()
    sdList = dict()
    tList = []

    def _makeBroadcast(x):
        bc, sd = makeBroadcast(x)
        bcList[x] = bc
        sdList[x] = sd

    for i in iterList:
        tmp_t = Greenlet(_makeBroadcast, i)
        tmp_t.parent_args = (N, t)
        tmp_t.name = 'client_test_freenet._makeBroadcast(%d)' % i
        tmp_t.start()
        tList.append(tmp_t)

    gevent.joinall(tList)

    rnd = Random()
    rnd.seed(123123)
    transactionSet = set([encodeTransaction(randomTransaction(rnd), randomGenerator=rnd)
                          for trC in range(int(options.tx))])

    def toBeScheduled():
        for i in iterList:
            bc = bcList[i]
            sd = sdList[i]
            recv = servers[0].get

            th = Greenlet(byzantineVoteParty, i, N, t, controlChannels[i], bc, recv, sd, options.B)
            th.parent_args = (N, t)
            th.name = 'client_test_freenet.byzantineVoteParty(%d)' % i
            controlChannels[i].put(('IncludeTransaction', transactionSet))
            th.start()
            mylog('Summoned party %i at time %f' % (i, time.time()), verboseLevel=-1)
            ts.append(th)

        try:
            gevent.joinall(ts)
        except ACSException:
            gevent.killall(ts)
        except finishTransactionLeap:
            print('msgCounter', msgCounter)
            print('msgTypeCounter', msgTypeCounter)
            logChannel.put(StopIteration)
            mylog("=====", verboseLevel=-1)
            for item in logChannel:
                mylog(item, verboseLevel=-1)
            mylog("=====", verboseLevel=-1)
        except gevent.hub.LoopExit:
            while True:
                gevent.sleep(1)
            checkExceptionPerGreenlet()
        finally:
            print("Consensus Finished")

    import sched as _sched
    s = _sched.scheduler(time.time, time.sleep)
    time_now = time.time()
    delay = options.delaytime - time_now
    s.enter(delay, 1, toBeScheduled, ())
    s.run()


# ============================================================================
# CLI
# ============================================================================

import atexit


def exit():
    print("Entering atexit()")
    print('msgCounter', msgCounter)
    print('msgTypeCounter', msgTypeCounter)
    nums, lens = zip(*msgTypeCounter)
    print('    Init      Echo      Val       Aux      Coin     Ready    Share   Cobalt')
    print('%8d %8d %9d %9d %9d %9d %9d %9d ' % nums[1:])
    print('%8d %8d %9d %9d %9d %9d %9d %9d' % lens[1:])
    mylog("Total Message size %d" % totalMessageSize, verboseLevel=-2)


if __name__ == '__main__':
    atexit.register(exit)

    parser = OptionParser()
    parser.add_option("-e", "--ecdsa-keys", dest="ecdsa",
                      help="Location of ECDSA keys", metavar="KEYS")
    parser.add_option("-k", "--threshold-keys", dest="threshold_keys",
                      help="Location of threshold signature keys", metavar="KEYS")
    parser.add_option("-c", "--threshold-enc", dest="threshold_encs",
                      help="Location of threshold encryption keys", metavar="KEYS")
    parser.add_option("-s", "--hosts", dest="hosts",
                      help="Host list file", metavar="HOSTS", default="~/hosts")
    parser.add_option("-n", "--number", dest="n",
                      help="Number of parties", metavar="N", type="int")
    parser.add_option("-p", "--tx-path", dest="txpath",
                      help="File path of the transaction set", metavar="FILE", default='tx')
    parser.add_option("-a", "--negotiated-time", dest="delaytime",
                      help="will start the protocol at some multiple of c", metavar="C", type="int", default=50)
    parser.add_option("-b", "--propose-size", dest="B",
                      help="Number of transactions to propose", metavar="B", type="int")
    parser.add_option("-t", "--tolerance", dest="t",
                      help="Tolerance of adversaries", metavar="T", type="int")
    parser.add_option("-x", "--transactions", dest="tx",
                      help="Number of transactions proposed by each party", metavar="TX", type="int", default=-1)
    parser.add_option("-v", "--version", dest="v",
                      help="Binary Consensus Version", metavar="V", type="int")
    parser.add_option("--my-id", dest="myid",
                      help="Byzantine node's party ID", metavar="ID", type="int", default=0)
    (options, args) = parser.parse_args()
    prepareIPList(open(expanduser(options.hosts), 'r').read())
    if (options.ecdsa and options.threshold_keys and options.threshold_encs and options.n and options.t and options.v):
        if not options.B:
            options.B = int(math.ceil(options.n * math.log(options.n)))
        if options.tx < 0:
            options.tx = options.B
        client_test_freenet(options.n, options.t, options.v, options)
    else:
        parser.error('Please specify the arguments')

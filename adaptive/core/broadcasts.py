# coding=utf-8
import base64

import gevent
from gevent import Greenlet, socket, monkey
from gevent.queue import Queue
from collections import defaultdict
from .utils import greenletPacker, getKeys
from ..commoncoin.thresprf_gipc import serialize, serialize1, deserialize, combine_and_verify
import random
import time
import pickle

from ..sgx.cryptor import Cryptor

verbose = 0
from .utils import makeCallOnce, \
    makeBroadcastWithTag, makeBroadcastWithTagAndRound, garbageCleaner, loopWrapper

monkey.patch_all()


def get_est1_from_sgx(host='127.0.0.1', port=65430, obj=None):
    """
    使用 gevent socket + pickle 发送任意 Python 对象到 SGX 服务器
    """
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))

    try:
        # 1. 序列化对象
        serialized_data = pickle.dumps(obj)

        # 2. 发送数据
        client_socket.sendall(serialized_data)
        client_socket.shutdown(socket.SHUT_WR)  # 通知服务端数据已发完

        # 3. 接收完整响应（直到服务端关闭连接）
        response_data = bytearray()
        while True:
            chunk = client_socket.recv(4096)
            if not chunk:
                break
            response_data.extend(chunk)

        # 4. 反序列化响应对象
        return pickle.loads(response_data)

    finally:
        client_socket.close()


def get_est2_from_sgx(host='127.0.0.1', port=65431, obj=None):
    """
    使用 gevent socket + pickle 发送任意 Python 对象到 SGX 服务器
    """
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))

    try:
        # 1. 序列化对象
        serialized_data = pickle.dumps(obj)

        # 2. 发送数据
        client_socket.sendall(serialized_data)
        client_socket.shutdown(socket.SHUT_WR)  # 通知服务端数据已发完

        # 3. 接收完整响应（直到服务端关闭连接）
        response_data = bytearray()
        while True:
            chunk = client_socket.recv(4096)
            if not chunk:
                break
            response_data.extend(chunk)

        # 4. 反序列化响应对象
        return pickle.loads(response_data)

    finally:
        client_socket.close()


def get_est3_from_sgx(host='127.0.0.1', port=65432, obj=None):
    """
    使用 gevent socket + pickle 发送任意 Python 对象到 SGX 服务器
    """
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))

    try:
        # 1. 序列化对象
        serialized_data = pickle.dumps(obj)

        # 2. 发送数据
        client_socket.sendall(serialized_data)
        client_socket.shutdown(socket.SHUT_WR)  # 通知服务端数据已发完

        # 3. 接收完整响应（直到服务端关闭连接）
        response_data = bytearray()
        while True:
            chunk = client_socket.recv(4096)
            if not chunk:
                break
            response_data.extend(chunk)

        # 4. 反序列化响应对象
        return pickle.loads(response_data)

    finally:
        client_socket.close()


def get_counter_result_from_sgx_broadcast(host='127.0.0.1', port=65433, obj=None):
    """
    使用 gevent socket + pickle 发送任意 Python 对象到 SGX 服务器
    """
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))

    try:
        # 1. 序列化对象
        serialized_data = pickle.dumps(obj)

        # 2. 发送数据
        client_socket.sendall(serialized_data)
        client_socket.shutdown(socket.SHUT_WR)  # 通知服务端数据已发完

        # 3. 接收完整响应（直到服务端关闭连接）
        response_data = bytearray()
        while True:
            chunk = client_socket.recv(4096)
            if not chunk:
                break
            response_data.extend(chunk)

        # 4. 反序列化响应对象
        return pickle.loads(response_data)

    finally:
        client_socket.close()


def get_counter_result_from_sgx_broadcast1(host='127.0.0.1', port=65434, obj=None):
    """
    使用 gevent socket + pickle 发送任意 Python 对象到 SGX 服务器（不使用长度头）
    """
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))

    try:
        # 1. 序列化对象
        serialized_data = pickle.dumps(obj)

        # 2. 发送数据
        client_socket.sendall(serialized_data)
        client_socket.shutdown(socket.SHUT_WR)  # 通知服务端数据已发完

        # 3. 接收完整响应（直到服务端关闭连接）
        response_data = bytearray()
        while True:
            chunk = client_socket.recv(4096)
            if not chunk:
                break
            response_data.extend(chunk)

        # 4. 反序列化响应对象
        return pickle.loads(response_data)

    finally:
        client_socket.close()


def get_counter_result_from_sgx_broadcast2(host='127.0.0.1', port=65435, obj=None):
    """
    使用 gevent socket + pickle 发送任意 Python 对象到 SGX 服务器（不使用长度头）
    """
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))

    try:
        # 1. 序列化对象
        serialized_data = pickle.dumps(obj)

        # 2. 发送数据
        client_socket.sendall(serialized_data)
        client_socket.shutdown(socket.SHUT_WR)  # 通知服务端数据已发完

        # 3. 接收完整响应（直到服务端关闭连接）
        response_data = bytearray()
        while True:
            chunk = client_socket.recv(4096)
            if not chunk:
                break
            response_data.extend(chunk)

        # 4. 反序列化响应对象
        return pickle.loads(response_data)

    finally:
        client_socket.close()


def get_coin_from_sgx():
    SGX_HOST = 'localhost'
    SGX_PORT = 65432

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as so:
        get_coin_timer_start = time.time()
        so.connect((SGX_HOST, SGX_PORT))
        so.sendall(b"1")  # 发送任意数据触发服务器响应

        # 接收 1 字节（0 或 1）
        data = so.recv(1)

        coin = int.from_bytes(data, byteorder='little')  # 字节转整数

        get_coin_timer_end = time.time()

        print(
            f"[ SGX SERVER ] SGX 决定硬币为 -> {coin}, 执行时间: {get_coin_timer_end - get_coin_timer_start:.4f} 秒")  # 输出 0 或 1

        return coin


def default_zero():
    return 0


def reliable_broadcast(pid, N, t, broadcast, receive, output):
    assert N > 3 * t
    Threshold2 = N - t

    def Listener(my_v):
        broadcast(('i', pid, my_v))  # send phase / send tuple

        echos = [defaultdict(lambda: 0) for _ in range(N)]
        readyCounter = [defaultdict(default_zero) for _ in range(N)]
        readySent = [False] * N
        sentEcho = [False] * N
        result = {}

        while True:  # main loop
            msgBundle = receive()
            # print("msgBundle", msgBundle)
            if msgBundle[0] == 'i' and not sentEcho[msgBundle[1]]:
                sentEcho[msgBundle[1]] = True
                broadcast(('e', msgBundle[1], pid, msgBundle[2]))

            elif msgBundle[0] == 'e':  # echo phase
                echos[msgBundle[1]][msgBundle[2]] = msgBundle[3]
                if len(echos[msgBundle[1]]) >= Threshold2 and not readySent[msgBundle[1]]:
                    readySent[msgBundle[1]] = True
                    broadcast(('r', msgBundle[1], msgBundle[3]))

            elif msgBundle[0] == 'r':  # ready phase
                ### todo: SGX
                msgObj = {
                    "t": t,
                    "msgBundle": msgBundle,
                    "Threshold2": Threshold2
                }

                sgx_result = get_counter_result_from_sgx_broadcast(obj=msgObj)

                if sgx_result == 1 and not readySent[msgBundle[1]]:
                    readySent[msgBundle[1]] = True
                    broadcast(('r', msgBundle[1], msgBundle[2]))
                elif sgx_result == 2:
                    result[msgBundle[1]] = msgBundle[2]
                    if len(result) == N:
                        output(result)
                        break

                ### todo: None-SGX
                # readyCounter[msgBundle[1]][msgBundle[2]] += 1
                # tmp = readyCounter[msgBundle[1]][msgBundle[2]]
                #
                # if tmp >= t + 1 and not readySent[msgBundle[1]]:
                #     readySent[msgBundle[1]] = True
                #     broadcast(('r', msgBundle[1], msgBundle[2]))
                #
                # if tmp >= Threshold2:
                #     result[msgBundle[1]] = msgBundle[2]
                #     if len(result) == N:
                #         output(result)
                #         break

    return Listener


def reliable_broadcast1(pid, N, t, broadcast, receive, output):
    assert N > 3 * t
    Threshold2 = N - t

    def Listener(my_v):
        broadcast(('i', pid, my_v))  # send phase

        echos = [defaultdict(lambda: 0) for _ in range(N)]
        readyCounter = [defaultdict(lambda: 0) for _ in range(N)]
        readySent = [False] * N
        sentEcho = [False] * N
        result = {}

        while True:  # main loop
            msgBundle = receive()
            # print("msgBundle", msgBundle)  # msgBundle 0
            if msgBundle[0] == 'i' and not sentEcho[msgBundle[1]]:  # 整数不可索引
                sentEcho[msgBundle[1]] = True
                broadcast(('e', msgBundle[1], pid, msgBundle[2]))

            elif msgBundle[0] == 'e':  # echo phase
                echos[msgBundle[1]][msgBundle[2]] = msgBundle[3]
                if len(echos[msgBundle[1]]) >= Threshold2 and not readySent[msgBundle[1]]:
                    readySent[msgBundle[1]] = True
                    broadcast(('r', msgBundle[1], msgBundle[3]))

            elif msgBundle[0] == 'r':  # ready phase
                ### todo: SGX
                msgObj = {
                    "t": t,
                    "msgBundle": msgBundle,
                    "Threshold2": Threshold2
                }

                sgx_result = get_counter_result_from_sgx_broadcast1(obj=msgObj)

                if sgx_result == 1 and not readySent[msgBundle[1]]:
                    readySent[msgBundle[1]] = True
                    broadcast(('r', msgBundle[1], msgBundle[2]))
                elif sgx_result == 2:
                    result[msgBundle[1]] = msgBundle[2]
                    if len(result) == N:
                        output(result)
                        break

                ### todo: None-SGX
                # readyCounter[msgBundle[1]][msgBundle[2]] += 1
                # tmp = readyCounter[msgBundle[1]][msgBundle[2]]
                #
                # if tmp >= t + 1 and not readySent[msgBundle[1]]:
                #     readySent[msgBundle[1]] = True
                #     broadcast(('r', msgBundle[1], msgBundle[2]))
                #
                # if tmp >= Threshold2:
                #     result[msgBundle[1]] = msgBundle[2]
                #     if len(result) == N:
                #         output(result)
                #         break

    return Listener


def reliable_broadcast2(pid, N, t, broadcast, receive, output):
    assert N > 3 * t
    Threshold2 = N - t

    def Listener(my_v):
        broadcast(('i', pid, my_v))  # send phase

        echos = [defaultdict(lambda: 0) for _ in range(N)]
        readyCounter = [defaultdict(lambda: 0) for _ in range(N)]
        readySent = [False] * N
        sentEcho = [False] * N
        result = {}

        while True:  # main loop

            msgBundle = receive()
            if msgBundle[0] == 'i' and not sentEcho[msgBundle[1]]:
                sentEcho[msgBundle[1]] = True
                broadcast(('e', msgBundle[1], pid, msgBundle[2]))

            elif msgBundle[0] == 'e':  # echo phase
                echos[msgBundle[1]][msgBundle[2]] = msgBundle[3]
                if len(echos[msgBundle[1]]) >= Threshold2 and not readySent[msgBundle[1]]:
                    readySent[msgBundle[1]] = True
                    broadcast(('r', msgBundle[1], msgBundle[3]))

            elif msgBundle[0] == 'r':  # ready phase
                ### todo: SGX
                msgObj = {
                    "t": t,
                    "msgBundle": msgBundle,
                    "Threshold2": Threshold2
                }

                sgx_result = get_counter_result_from_sgx_broadcast2(obj=msgObj)

                if sgx_result == 1 and not readySent[msgBundle[1]]:
                    readySent[msgBundle[1]] = True
                    broadcast(('r', msgBundle[1], msgBundle[2]))
                elif sgx_result == 2:
                    result[msgBundle[1]] = msgBundle[2]
                    if len(result) == N:
                        output(result)
                        break

                ### todo: None-SGX
                # readyCounter[msgBundle[1]][msgBundle[2]] += 1
                # tmp = readyCounter[msgBundle[1]][msgBundle[2]]
                #
                # if tmp >= t + 1 and not readySent[msgBundle[1]]:
                #     readySent[msgBundle[1]] = True
                #     broadcast(('r', msgBundle[1], msgBundle[2]))
                #
                # if tmp >= Threshold2:
                #     result[msgBundle[1]] = msgBundle[2]
                #     if len(result) == N:
                #         output(result)
                #         break

    return Listener


# Input: a binary value
# Output: outputs one binary value, and thereafter possibly a second
# - If at least (t+1) of the honest parties input v, then v will be output by all honest parties
# (Note: it requires up to 2*t honest parties to deliver their messages. At the highest tolerance setting, this means *all* the honest parties)
# - If any honest party outputs a value, then it must have been input by some honest party. If only corrupted parties propose a value, it will never be output.
def bv_broadcast(pid, N, t, broadcast, receive, output, release=lambda: None):
    assert N > 3 * t

    def input(my_v):
        # my_v : input valuef

        # My initial input value is v in (0,1)
        # assert my_v in (0, 1)

        # We'll output each of (0,1) at most once
        out = (makeCallOnce(lambda: output(0)),
               makeCallOnce(lambda: output(1)))

        # We'll relay each of (0,1) at most once
        received = defaultdict(set)

        def _bc(v):
            broadcast(v)

        relay = (makeCallOnce(lambda: _bc(0)),
                 makeCallOnce(lambda: _bc(1)))

        # Start by relaying my value
        relay[my_v]()
        outputed = []
        while True:
            (sender, v) = receive()

            assert v in (0, 1)
            assert sender in range(N)
            received[v].add(sender)
            # Relay after reaching first threshold
            if len(received[v]) >= t + 1:
                relay[v]()

            # Output after reaching second threshold
            if len(received[v]) >= 2 * t + 1:
                out[v]()
                if not v in outputed:
                    outputed.append(v)
                if len(outputed) == 2:
                    release()  # Release Channel
                    return  # We don't have to wait more

    return input


def fast_bv_broadcast(round, pid, N, t, broadcast, receive, output, release=lambda: None):
    '''
    The BV_Broadcast algorithm [RMR2004]
    :param pid: my id number
    :param N: the number of parties
    :param t: the number of byzantine parties
    :param broadcast: broadcast channel
    :param receive: receive channel
    :param output: output channel
    :return: None
    '''
    assert N > 5 * t

    def input(my_v):
        # my_v : input valuef

        out = (makeCallOnce(lambda: output(0)),
               makeCallOnce(lambda: output(1)),
               makeCallOnce(lambda: output(2)),
               makeCallOnce(lambda: output(3)),
               makeCallOnce(lambda: output(4)))

        # We'll relay each of (0,1) at most once
        received = defaultdict(set)
        received_msg = set()

        def _bc(v):
            broadcast(v)

        relay = (makeCallOnce(lambda: _bc(0)),
                 makeCallOnce(lambda: _bc(1)))

        # Start by relaying my value
        relay[my_v]()
        while True:
            (sender, v) = receive()
            assert v in (0, 1)
            assert sender in range(N)
            received[v].add(sender)
            received_msg.add(sender)

            # Output after reaching the threshold
            if len(received_msg) >= N - t:
                if round == 1:
                    # if pid == 0:
                    #    print received_msg
                    #    print received[0]
                    #    print received[1]
                    if len(received[0]) >= N - t:
                        out[3]()
                    elif len(received[1]) >= N - t:
                        out[4]()
                    elif len(received[0]) >= N - 3 * t:
                        out[0]()
                    elif len(received[1]) >= N - 3 * t:
                        out[1]()
                    else:
                        out[2]()
                else:
                    if len(received[0]) >= N - 2 * t:
                        out[0]()
                    elif len(received[1]) >= N - 2 * t:
                        out[1]()
                    else:
                        out[2]()
                return

    return input


class CommonCoinFailureException(Exception):
    pass


def shared_coin(instance, pid, N, t, broadcast, receive):
    received = defaultdict(set)
    outputQueue = defaultdict(lambda: Queue(1))
    PK, SKs, gg = getKeys()

    def _recv():
        while True:
            # New shares for some round r
            (i, (r, sig, proof_c, proof_z)) = receive()
            assert i in range(N)
            assert r >= 0
            received[r].add((i, serialize1(sig), serialize1(proof_c), serialize1(proof_z)))

            # After reaching the threshold, compute the output and
            # make it available locally
            if len(received[r]) == t + 1:
                h = PK.hash_message(str((r, instance)))

                def tmpFunc(r, t):
                    combine_and_verify(h, dict(
                        tuple((t, deserialize(sig)) for t, sig, proof_c, proof_z in received[r])[:t + 1]), dict(
                        tuple((t, deserialize(proof_c)) for t, sig, proof_c, proof_z in received[r])[:t + 1]), dict(
                        tuple((t, deserialize(proof_z)) for t, sig, proof_c, proof_z in received[r])[:t + 1]), gg)
                    outputQueue[r].put(serialize(h)[0] & 1)  # explicitly convert to int

                Greenlet(tmpFunc, r, t).start()

    greenletPacker(Greenlet(_recv), 'shared_coin_dummy', (pid, N, t, broadcast, receive)).start()

    def getCoin(round):
        broadcast((round, SKs[pid].sign(PK.hash_message(str((round, instance))), gg)))  # I have to do mapping to 1..l
        return outputQueue[round].get()

    return getCoin


def arbitary_adversary(pid, N, t, vi, broadcast, receive):
    pass  # TODO: implement our arbitrary adversaries


globalState = defaultdict(str)  # Just for debugging
decision = defaultdict(bool)
currentrounds = defaultdict(int)


def initBeforeBinaryConsensus():  # A dummy function now
    pass


def mv84consensus(pid, N, t, vi, broadcast, receive):
    # initialize v and p (same meaning as in the paper)
    mv84v = defaultdict(lambda: 'Empty')
    mv84p = defaultdict(lambda: False)
    # Initialize the locks and local variables
    mv84WaiterLock = Queue()
    mv84WaiterLock2 = Queue()
    mv84ReceiveDiff = set()
    mv84GetPerplex = set()
    reliableBroadcastReceiveQueue = Queue()

    def _listener():  # Hard-working Router for this layer
        while True:
            sender, (tag, m) = receive()
            if tag == 'V':
                mv84v[sender] = m
                if m != vi:
                    mv84ReceiveDiff.add(sender)
                    if len(mv84ReceiveDiff) >= (N - t) / 2.0:
                        mv84WaiterLock.put(True)
                # Fast-Stop: We don't need to wait for the rest (possibly)
                # malicious parties.
                if len(mv84v.keys()) >= N - t:
                    mv84WaiterLock.put(False)
            elif tag == 'B':
                mv84p[sender] = m
                if m:
                    mv84GetPerplex.add(sender)
                    if len(mv84GetPerplex) >= N - 2 * t:
                        mv84WaiterLock2.put(True)
                # Fast-Stop: We don't need to wait for the rest (possibly)
                # malicious parties.
                if len(mv84p.keys()) >= N - t:
                    mv84WaiterLock2.put(False)
            else:  # Re-route the msg to inner layer
                reliableBroadcastReceiveQueue.put(
                    (sender, (tag, m))
                )

    greenletPacker(Greenlet(_listener), 'mv84consensus._listener', (pid, N, t, vi, broadcast, receive)).start()

    makeBroadcastWithTag('V', broadcast)(vi)
    perplexed = mv84WaiterLock.get()  # See if I am perplexed

    makeBroadcastWithTag('B', broadcast)(perplexed)
    alert = mv84WaiterLock2.get() and 1 or 0  # See if we should alert

    decideChannel = Queue(1)
    greenletPacker(
        Greenlet(binary_consensus, pid, N, t, alert, decideChannel, broadcast, reliableBroadcastReceiveQueue.get),
        'mv84consensus.binary_consensus', (pid, N, t, vi, broadcast, receive)).start()
    agreedAlert = decideChannel.get()

    if agreedAlert:
        return 0  # some pre-defined default consensus value
    else:
        return vi


def checkFinishedWithGlobalState(N):
    '''
    Check if binary consensus is finished
    :param N: the number of parties
    :return: True if not finished, False if finished
    '''
    if len(globalState.keys()) < N:
        return True
    for i in globalState:
        if not globalState[i]:
            return True
    return False


cryptor = Cryptor()
aes_key = cryptor.load_aes_key_from_file(
    "/mnt/c/Users/yorky/Desktop/Project/Beat-LocalCoin-SGX/adaptive/sgx/aes.key"
)


def local_binary_consensus(instance, pid, N, t, vi, decide, broadcast, receive):
    """
    :param instance:
    :param pid:
    :param N:
    :param t:
    :param vi: VOTE
    :param decide:
    :param broadcast:
    :param receive:
    :return:
    """
    bcQB = defaultdict(lambda: Queue(1))
    bcQA = defaultdict(lambda: Queue(1))
    bcQC = defaultdict(lambda: Queue(1))

    def _recv():
        while True:
            (i, (tag, m)) = receive()
            if tag == 'B':
                # Broadcast message
                r, msg = m
                # print("local:m",m) # m (1, 0)
                # print("local:r",r, "msg",msg) #:r 1 msg 0
                greenletPacker(Greenlet(bcQB[r].put, msg),
                               'local_binary_consensus.bcQB[%d].put' % r,
                               (pid, N, t, vi, decide, broadcast, receive)).start()  # In case they block the router
            elif tag == 'A':
                r, msg = m
                greenletPacker(Greenlet(bcQA[r].put, msg),
                               'local_binary_consensus.bcQA[%d].put' % r,
                               (pid, N, t, vi, decide, broadcast, receive)).start()  # In case they block the router
            elif tag == 'C':
                r, msg = m
                greenletPacker(Greenlet(bcQC[r].put, msg),
                               'local_binary_consensus.bcQC[%d].put' % r,
                               (pid, N, t, vi, decide, broadcast, receive)).start()  # In case they block the router
                pass

    greenletPacker(Greenlet(_recv), 'local_binary_consensus._recv', (pid, N, t, vi, decide, broadcast, receive)).start()

    def brcast_getA(r):
        def _recv(*args, **kargs):
            test = bcQA[r].get(*args, **kargs)
            return test

        return _recv

    def brcast_getB(r):
        def _recv(*args, **kargs):
            return bcQB[r].get(*args, **kargs)

        return _recv

    def brcast_getC(r):
        def _recv(*args, **kargs):
            return bcQC[r].get(*args, **kargs)

        return _recv

    round = 0
    est = vi
    decided = False
    decidedNum = 0
    null = 2

    while True:
        round += 1
        currentrounds[pid] = round

        bvOutputHolder = Queue(1)

        ### todo: SGX
        # coin_greenlet = gevent.spawn(get_coin_from_sgx)
        # s = coin_greenlet.get()

        # todo: None-SGX
        # s = random.choice([0, 1])
        # print(f'[SGX] JUDGE COIN -> {s}')

        if decided:
            break

        def bvOutput(m):
            bvOutputHolder.put(m)

        ##########################################
        #################Step 1###################
        ##########################################
        br1 = greenletPacker(Greenlet(
            reliable_broadcast(
                pid, N, t, makeBroadcastWithTagAndRound('B', broadcast, round),
                brcast_getB(round), bvOutput),
            est), 'local_binary_consensus.reliable_broadcast(%d, %d, %d)' % (pid, N, t),
            (pid, N, t, vi, decide, broadcast, receive))

        br1.start()
        w = bvOutputHolder.get()
        print(type(w))

        ### todo: None-SGX
        # count_0 = 0
        # count_1 = 0
        # for key in w:
        #     # 强行决定并解密 VOTE
        #     # vote = cryptor.decrypt_aes_b64(w[key], aes_key)
        #     vote = int.from_bytes(cryptor.decrypt_rsa(base64.b16decode(w[key])), byteorder='big')
        #     # print("w[key] ----> ", vote)
        #     if vote == 0:
        #         count_0 += 1
        #     else:
        #         count_1 += 1
        #
        # if count_0 > count_1:
        #     est1 = 0
        # elif count_1 > count_0:
        #     est1 = 1
        # else:
        #     est1 = random.choice([0, 1])
        # print("1--------------This is the est1--------", pid, est1)

        ### todo: SGX
        voteObj1 = {
            'voteObj1': w
        }

        est1 = get_est1_from_sgx(obj=voteObj1)

        ##########################################
        #################Step 2###################
        ##########################################
        bvOutputHolder2 = Queue(1)

        def bvOutput2(m):
            bvOutputHolder2.put(m)

        br2 = greenletPacker(Greenlet(
            reliable_broadcast1(pid, N, t, makeBroadcastWithTagAndRound('A', broadcast, round), brcast_getA(round),
                                bvOutput2), est1),
            'local_binary_consensus.reliable_broadcast(%d, %d, %d)' % (pid, N, t),
            (pid, N, t, vi, decide, broadcast, receive))

        br2.start()
        w2 = bvOutputHolder2.get()

        ### todo: None-SGX
        # print("2----------------This the w2-------", pid, w2)
        # count_0_2 = 0
        # count_1_2 = 0
        # for key in w2:
        #     if w2[key] == 0:
        #         count_0_2 += 1
        #     else:
        #         count_1_2 += 1
        #
        # if count_0_2 > N / 2:
        #     est2 = 0
        # elif count_1_2 > N / 2:
        #     est2 = 1
        # else:
        #     est2 = null
        #
        # print("3------------This is the est2--------", pid, est2)

        ### todo: SGX
        voteObj2 = {
            'n': N,
            'voteObj2': w2
        }

        est2 = get_est2_from_sgx(obj=voteObj2)

        ##########################################
        #################Step 3###################
        ##########################################
        bvOutputHolder3 = Queue(1)

        def bvOutput3(m):
            bvOutputHolder3.put(m)

        br3 = greenletPacker(Greenlet(
            reliable_broadcast2(
                pid, N, t, makeBroadcastWithTagAndRound('C', broadcast, round),
                brcast_getC(round), bvOutput3),
            est2), 'local_binary_consensus.reliable_broadcast(%d, %d, %d)' % (pid, N, t),
            (pid, N, t, vi, decide, broadcast, receive))

        br3.start()
        w3 = bvOutputHolder3.get()

        ### todo: None-SGX
        # count_0_3 = 0
        # count_1_3 = 0
        # for key in w3:
        #     if w3[key] == 0:
        #         v = w3[key]
        #         count_0_3 += 1
        #     else:
        #         v = w3[key]
        #         count_1_3 += 1
        #
        # if count_1_3 >= 2 * t + 1 and v != null:
        #     globalState[pid] = "%d" % v
        #     decide.put(v)
        #     decided = True
        #     decidedNum = v
        #     if pid == 0:
        #         print("[PID: %d] Decided on value: %d, round: %d" % (pid, v, round))
        # elif count_0_3 >= 2 * t + 1 and v != null:
        #     globalState[pid] = "%d" % v
        #     decide.put(v)
        #     decided = True
        #     decidedNum = v
        #     if pid == 0:
        #         print("[PID: %d] Decided on value: %d, round: %d" % (pid, v, round))
        # elif count_0_3 >= t + 1 and v != null:
        #     est = v
        # elif count_1_3 >= t + 1 and v != null:
        #     est = v
        # else:
        #     # gevent.sleep(1)
        #     est = random.choice([0, 1])
        #     # est = coin_greenlet.get()  # 从 SGX 取得随机值

        ### todo: SGX
        voteObj3 = {
            'voteObj3': w3,
            't': t
        }

        countResultFromSGX = get_est3_from_sgx(obj=voteObj3)
        v = countResultFromSGX['v']

        if countResultFromSGX['result'] == 1 and v != null:
            globalState[pid] = "%d" % v
            decide.put(v)
            decided = True
            decidedNum = v
            if pid == 0:
                print("[PID: %d] Decided on value: %d, round: %d" % (pid, v, round))
        elif countResultFromSGX['result'] == 2 and v != null:
            globalState[pid] = "%d" % v
            decide.put(v)
            decided = True
            decidedNum = v
            if pid == 0:
                print("[PID: %d] Decided on value: %d, round: %d" % (pid, v, round))
        elif countResultFromSGX['result'] == 3 and v != null:
            est = v
        elif countResultFromSGX['result'] == 4 and v != null:
            est = v
        else:
            # gevent.sleep(1)
            # est = random.choice([0, 1])
            est = countResultFromSGX['coin']  # 从 SGX 取得随机值


def binary_consensus(instance, pid, N, t, vi, decide, broadcast, receive):
    # print "********************Sisi step 5: BA,pid: %s, instance: %d******************"%(pid, instance)
    # Messages received are routed to either a shared coin, the broadcast, or AUX
    coinQ = Queue(1)
    bcQ = defaultdict(lambda: Queue(1))
    auxQ = defaultdict(lambda: Queue(1))

    def _recv():
        while True:  # not finished[pid]:
            (i, (tag, m)) = receive()
            if tag == 'B':
                # Broadcast message
                r, msg = m
                greenletPacker(Greenlet(bcQ[r].put, (i, msg)),
                               'binary_consensus.bcQ[%d].put' % r,
                               (pid, N, t, vi, decide, broadcast, receive)).start()  # In case they block the router
            elif tag == 'C':
                # A share of a coin
                greenletPacker(Greenlet(coinQ.put, (i, m)),
                               'binary_consensus.coinQ.put', (pid, N, t, vi, decide, broadcast, receive)).start()
            elif tag == 'A':
                # Aux message
                r, msg = m
                greenletPacker(Greenlet(auxQ[r].put, (i, msg)),
                               'binary_consensus.auxQ[%d].put' % r, (pid, N, t, vi, decide, broadcast, receive)).start()
                pass

    greenletPacker(Greenlet(_recv), 'binary_consensus._recv', (pid, N, t, vi, decide, broadcast, receive)).start()

    def brcast_get(r):
        def _recv(*args, **kargs):
            return bcQ[r].get(*args, **kargs)

        return _recv

    received = [defaultdict(set), defaultdict(set)]

    coin = shared_coin(instance, pid, N, t, makeBroadcastWithTag('C', broadcast), coinQ.get)

    # print coin(1)

    def getWithProcessing(r, binValues, callBackWaiter):
        def _recv(*args, **kargs):
            sender, v = auxQ[r].get(*args, **kargs)
            assert v in (0, 1)
            assert sender in range(N)
            received[v][r].add(sender)
            # Check if conditions are satisfied
            threshold = N - t  # 2*t + 1 # N - t
            if True:  # not finished[pid]:
                if len(binValues) == 1:

                    if len(received[binValues[0]][r]) >= threshold and not callBackWaiter[r].full():
                        # Check passed
                        callBackWaiter[r].put(binValues)
                elif len(binValues) == 2:

                    if len(received[0][r].union(received[1][r])) >= threshold and not callBackWaiter[r].full():
                        callBackWaiter[r].put(binValues)
                    elif len(received[0][r]) >= threshold and not callBackWaiter[r].full():
                        callBackWaiter[r].put([0])
                    elif len(received[1][r]) >= threshold and not callBackWaiter[r].full():
                        callBackWaiter[r].put([1])
            return sender, v

        return _recv

    round = 0
    est = vi
    decided = False
    decidedNum = 0

    callBackWaiter = defaultdict(lambda: Queue(1))

    while True:  # checkFinishedWithGlobalState(N): <- for distributed experiment we don't need this
        round += 1
        currentrounds[pid] = round
        # print "round %d"%round
        # Broadcast EST
        # TODO: let bv_broadcast receive
        bvOutputHolder = Queue(2)  # 2 possible values
        binValues = []

        def bvOutput(m):
            if not m in binValues:
                binValues.append(m)
                bvOutputHolder.put(m)

        def getRelease(channel):
            def _release():
                greenletPacker(Greenlet(garbageCleaner, channel),
                               'binary_consensus.garbageCleaner', (pid, N, t, vi, decide, broadcast, receive)).start()

            return _release

        br1 = greenletPacker(Greenlet(
            bv_broadcast(
                pid, N, t, makeBroadcastWithTagAndRound('B', broadcast, round),
                brcast_get(round), bvOutput, getRelease(bcQ[round])),
            est), 'binary_consensus.bv_broadcast(%d, %d, %d)' % (pid, N, t),
            (pid, N, t, vi, decide, broadcast, receive))
        br1.start()
        w = bvOutputHolder.get()  # Wait until output is not empty

        broadcast(('A', (round, w)))
        greenletPacker(Greenlet(loopWrapper(getWithProcessing(round, binValues, callBackWaiter))),
                       'binary_consensus.loopWrapper(getWithProcessing(round, binValues, callBackWaiter))',
                       (pid, N, t, vi, decide, broadcast, receive)).start()

        values = callBackWaiter[round].get()  # wait until the conditions are satisfied
        s = coin(round)

        if decided and decidedNum == s:  # infinite-message fix
            break
        if len(values) == 1:
            if values[0] == s:
                # decide s
                if not decided:
                    globalState[pid] = "%d" % s
                    decide.put(s)
                    decided = True
                    decidedNum = s
                    if pid == 0:
                        print("[PID: %d] Decided on value: %d, round: %d" % (pid, s, round))


            else:
                # print ('[%d] advances rounds from %d caused by values[0](%d)!=s(%d)' % (pid, round, values[0], s))
                pass
                # mylog('[%d] advances rounds from %d caused by values[0](%d)!=s(%d)' % (pid, round, values[0], s), verboseLevel=-1)
            est = values[0]
        else:
            # print ('[%d] advances rounds from %d caused by len(values)>1 where values=%s' % (pid, round, repr(values)))
            # mylog('[%d] advances rounds from %d caused by len(values)>1 where values=%s' % (pid, round, repr(values)), verboseLevel=-1)
            est = s

    # mylog("[%d]b exits binary consensus" % pid)


def fast_binary_consensus(instance, pid, N, t, vi, decide, broadcast, receive):
    assert N > 5 * t

    # Messages received are routed to either a shared coin, the broadcast, or AUX
    coinQ = Queue(1)
    bcQ = defaultdict(lambda: Queue(1))
    auxQ = defaultdict(lambda: Queue(1))

    def _recv():
        while True:  # not finished[pid]:
            (i, (tag, m)) = receive()
            if tag == 'B':
                # Broadcast message
                r, msg = m
                greenletPacker(Greenlet(bcQ[r].put, (i, msg)),
                               'binary_consensus.bcQ[%d].put' % r,
                               (pid, N, t, vi, decide, broadcast, receive)).start()  # In case they block the router
            elif tag == 'C':
                # A share of a coin
                greenletPacker(Greenlet(coinQ.put, (i, m)),
                               'binary_consensus.coinQ.put', (pid, N, t, vi, decide, broadcast, receive)).start()

    greenletPacker(Greenlet(_recv), 'binary_consensus._recv', (pid, N, t, vi, decide, broadcast, receive)).start()

    def brcast_get(r):
        def _recv(*args, **kargs):
            return bcQ[r].get(*args, **kargs)

        return _recv

    received = [defaultdict(set), defaultdict(set)]

    coin = shared_coin(instance, pid, N, t, makeBroadcastWithTag('C', broadcast), coinQ.get)
    # print coin(1)

    round = 0
    est = vi
    decided = False
    decidedNum = 0

    callBackWaiter = defaultdict(lambda: Queue(1))

    while True:  # checkFinishedWithGlobalState(N): <- for distributed experiment we don't need this
        round += 1
        currentrounds[pid] = round
        # print "round %d"%round
        # Broadcast EST
        # TODO: let bv_broadcast receive
        bvOutputHolder = Queue(1)  # 1 possible value

        def bvOutput(m):
            bvOutputHolder.put(m)

        def getRelease(channel):
            def _release():
                greenletPacker(Greenlet(garbageCleaner, channel),
                               'binary_consensus.garbageCleaner', (pid, N, t, vi, decide, broadcast, receive)).start()

            return _release

        br1 = greenletPacker(Greenlet(
            fast_bv_broadcast(
                round, pid, N, t, makeBroadcastWithTagAndRound('B', broadcast, round),
                brcast_get(round), bvOutput, getRelease(bcQ[round])),
            est), 'fast_binary_consensus.fast_bv_broadcast(%d, %d, %d)' % (pid, N, t),
            (round, pid, N, t, vi, decide, broadcast, receive))
        br1.start()
        w = bvOutputHolder.get()  # Wait until output is not empty

        s = coin(round)

        if decided and decidedNum == s:  # infinite-message fix
            break

        # print (w)
        if w == 0 or w == 1 or w == 3 or w == 4:
            est = w
            if round == 1:
                if w == 3:
                    est = 0
                elif w == 4:
                    est = 1
                if w == 3 or w == 4:
                    # decide s
                    if not decided:
                        globalState[pid] = "%d" % est
                        decide.put(est)
                        decided = True
                        decidedNum = s
                        if pid == 0:
                            print("[PID: %d] Decided on value: %d, round: %d" % (pid, est, round))

                else:
                    pass
            else:
                if w == s:
                    # decide s
                    if not decided:
                        globalState[pid] = "%d" % s
                        decide.put(s)
                        decided = True
                        decidedNum = s
                        if pid == 0:
                            print("[PID: %d] Decided on value: %d, round: %d" % (pid, s, round))

                else:
                    # print ('[%d] advances rounds from %d caused by values[0](%d)!=s(%d)' % (pid, round, values[0], s))
                    pass

        else:
            est = s


def cobalt_binary_consensus(instance, pid, N, t, vi, decide, broadcast, receive):
    '''
    Binary consensus from [MMR 13]. It takes an input vi and will finally write the decided value into _decide_ channel.
    :param pid: my id number
    :param N: the number of parties
    :param t: the number of byzantine parties
    :param vi: input value, an integer
    :param decide: deciding channel
    :param broadcast: broadcast channel
    :param receive: receive channel
    :return:
    '''

    # print "********************Sisi step 5: BA,pid: %s, instance: %d******************"%(pid, instance)
    # Messages received are routed to either a shared coin, the broadcast, or AUX
    coinQ = Queue(1)
    bcQ = defaultdict(lambda: Queue(1))
    auxQ = defaultdict(lambda: Queue(1))
    confQ = defaultdict(lambda: Queue(1))

    def _recv():
        while True:  # not finished[pid]:
            (i, (tag, m)) = receive()
            if tag == 'B':
                # Broadcast message
                r, msg = m
                greenletPacker(Greenlet(bcQ[r].put, (i, msg)),
                               'cobalt_binary_consensus.bcQ[%d].put' % r,
                               (pid, N, t, vi, decide, broadcast, receive)).start()  # In case they block the router
            elif tag == 'C':
                # A share of a coin
                greenletPacker(Greenlet(coinQ.put, (i, m)),
                               'cobalt_binary_consensus.coinQ.put', (pid, N, t, vi, decide, broadcast, receive)).start()
            elif tag == 'A':
                # Aux message
                r, msg = m
                greenletPacker(Greenlet(auxQ[r].put, (i, msg)),
                               'cobalt_binary_consensus.auxQ[%d].put' % r,
                               (pid, N, t, vi, decide, broadcast, receive)).start()
                pass
            elif tag == 'F':
                # Aux message
                r, msg = m
                greenletPacker(Greenlet(confQ[r].put, (i, msg)),
                               'cobalt_binary_consensus.confQ[%d].put' % r,
                               (pid, N, t, vi, decide, broadcast, receive)).start()
                pass

    greenletPacker(Greenlet(_recv), 'cobalt_binary_consensus._recv',
                   (pid, N, t, vi, decide, broadcast, receive)).start()

    def brcast_get(r):
        def _recv(*args, **kargs):
            return bcQ[r].get(*args, **kargs)

        return _recv

    received = [defaultdict(set), defaultdict(set)]
    conf_values = defaultdict(lambda: {(0,): set(), (1,): set(), (0, 1): set()})

    coin = shared_coin(instance, pid, N, t, makeBroadcastWithTag('C', broadcast), coinQ.get)

    # print coin(1)

    def getWithProcessing(r, binValues, callBackWaiter):
        def _recv(*args, **kargs):
            sender, v = auxQ[r].get(*args, **kargs)
            assert v in (0, 1)
            assert sender in range(N)
            received[v][r].add(sender)
            # Check if conditions are satisfied
            threshold = N - t  # 2*t + 1 # N - t
            if True:  # not finished[pid]:
                if len(binValues) == 1:
                    if len(received[binValues[0]][r]) >= threshold and not callBackWaiter[r].full():
                        # Check passed
                        callBackWaiter[r].put(binValues)
                elif len(binValues) == 2:
                    if len(received[0][r].union(received[1][r])) >= threshold and not callBackWaiter[r].full():
                        callBackWaiter[r].put(binValues)
                    elif len(received[0][r]) >= threshold and not callBackWaiter[r].full():
                        callBackWaiter[r].put([0])
                    elif len(received[1][r]) >= threshold and not callBackWaiter[r].full():
                        callBackWaiter[r].put([1])
            return sender, v

        return _recv

    def finalProcessing(r, binValues, finalWaiter):
        def _recv(*args, **kargs):
            sender, val = confQ[r].get(*args, **kargs)
            v = tuple()
            if 0 in val:
                v += (0,)
            if 1 in val:
                v += (1,)

            assert v in ((0,), (1,), (0, 1))
            assert sender in range(N)
            # try:
            conf_values[r][v].add(sender)
            # except:
            #    print "what?"
            # Check if conditions are satisfied
            threshold = N - t  # 2*t + 1 # N - t
            # print "conf", conf_values
            if True:  # not finished[pid]:

                if len(binValues) == 1:
                    if len(conf_values[r][(binValues[0],)]) >= threshold and not finalWaiter[r].full():
                        # Check passed
                        finalWaiter[r].put(binValues)
                elif len(binValues) == 2:
                    if len(conf_values[r][(0,)]) >= threshold and not finalWaiter[r].full():
                        finalWaiter[r].put([0])
                    elif len(conf_values[r][(1,)]) >= threshold and not finalWaiter[r].full():
                        finalWaiter[r].put([1])
                    elif (sum(len(senders) for conf_value, senders in
                              conf_values[r].items()) >= N - t):
                        finalWaiter[r].put(binValues)
            return sender, v

        return _recv

    round = 0
    est = vi
    decided = False
    decidedNum = 0

    callBackWaiter = defaultdict(lambda: Queue(1))
    finalWaiter = defaultdict(lambda: Queue(1))

    while True:  # checkFinishedWithGlobalState(N): <- for distributed experiment we don't need this
        round += 1
        currentrounds[pid] = round
        # print "round %d"%round
        # Broadcast EST
        # TODO: let bv_broadcast receive
        bvOutputHolder = Queue(2)  # 2 possible values
        binValues = []

        def bvOutput(m):
            if not m in binValues:
                binValues.append(m)
                bvOutputHolder.put(m)

        def getRelease(channel):
            def _release():
                greenletPacker(Greenlet(garbageCleaner, channel),
                               'cobalt_binary_consensus.garbageCleaner',
                               (pid, N, t, vi, decide, broadcast, receive)).start()

            return _release

        br1 = greenletPacker(Greenlet(
            bv_broadcast(
                pid, N, t, makeBroadcastWithTagAndRound('B', broadcast, round),
                brcast_get(round), bvOutput, getRelease(bcQ[round])),
            est), 'cobalt_binary_consensus.bv_broadcast(%d, %d, %d)' % (pid, N, t),
            (pid, N, t, vi, decide, broadcast, receive))
        br1.start()
        w = bvOutputHolder.get()  # Wait until output is not empty

        broadcast(('A', (round, w)))
        greenletPacker(Greenlet(loopWrapper(getWithProcessing(round, binValues, callBackWaiter))),
                       'cobalt_binary_consensus.loopWrapper(getWithProcessing(round, binValues, callBackWaiter))',
                       (pid, N, t, vi, decide, broadcast, receive)).start()

        values = callBackWaiter[round].get()  # wait until the conditions are satisfied

        broadcast(('F', (round, values)))

        greenletPacker(Greenlet(loopWrapper(finalProcessing(round, binValues, finalWaiter))),
                       'cobalt_binary_consensus.loopWrapper(finalProcessing(round, binValues, finalWaiter))',
                       (pid, N, t, vi, decide, broadcast, receive)).start()

        values = finalWaiter[round].get()

        s = coin(round)
        # Here corresponds to a proof that if one party decides at round r,
        # then in all the following rounds, everybody will propose r as an estimation. (Lemma 2, Lemma 1)
        # An abandoned party is a party who has decided but no enough peers to help him end the loop.
        # Lemma: # of abandoned party <= t
        if decided and decidedNum == s:  # infinite-message fix
            break
        if len(values) == 1:
            if values[0] == s:
                # decide s
                if not decided:
                    globalState[pid] = "%d" % s
                    decide.put(s)
                    decided = True
                    decidedNum = s
                    if pid == 0:
                        print("[PID: %d] Cobalt decided on value: %d, round: %d" % (pid, s, round))

            else:
                # print ('[%d] advances rounds from %d caused by values[0](%d)!=s(%d)' % (pid, round, values[0], s))
                pass
                # mylog('[%d] advances rounds from %d caused by values[0](%d)!=s(%d)' % (pid, round, values[0], s), verboseLevel=-1)
            est = values[0]
        else:
            print('[%d] advances rounds from %d caused by len(values)>1 where values=%s' % (pid, round, repr(values)))
            # mylog('[%d] advances rounds from %d caused by len(values)>1 where values=%s' % (pid, round, repr(values)), verboseLevel=-1)
            est = s

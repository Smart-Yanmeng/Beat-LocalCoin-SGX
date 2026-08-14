#!/usr/bin/python
"""
拜占庭节点测试脚本

模拟一个拜占庭节点：完成所有 TCP 握手后立即退出进程。
用于测试 TruBFT 协议在 N=4, t=1 配置下容忍 1 个崩溃节点的能力。

用法:
    python3 -m adaptive.test.byzantine_party_test \
        -k thsig4_1.keys \
        -e ecdsa.keys \
        -c thenc4_1.keys \
        -s hosts \
        -n 4 \
        --my-id <BYZANTINE_NODE_ID>
"""

from gevent import monkey
monkey.patch_all()

import socket
import struct
import time
import os
import sys
import pickle as cPickle

import gevent
from gevent.queue import Queue
from gevent import Greenlet
from gevent.server import StreamServer
from optparse import OptionParser
from os.path import expanduser
from socket import error as SocketError

from ..core.utils import mylog, initiateThresholdSig, initiateECDSAKeys, initiateThresholdEnc


BASE_PORT = 49500


def goodread(f, length):
    ltmp = length
    buf = []
    while ltmp > 0:
        buf.append(f.read(ltmp))
        ltmp -= len(buf[-1])
    return b''.join(buf)


def listen_to_channel(port):
    mylog('[Byzantine] Preparing server on %d...' % port)

    def _handle(socket, address):
        # 接受连接但不处理任何消息，保持 socket 存活直到进程退出
        f = socket.makefile('rb')
        try:
            while True:
                msglength, = struct.unpack('<I', goodread(f, 4))
                goodread(f, msglength)
        except Exception:
            pass

    server = StreamServer(('0.0.0.0', port), _handle)
    server.start()
    return server


def connect_to_channel(hostname, port, party):
    mylog('[Byzantine] Connecting to %s for party %d' % (repr((hostname, port)), party), verboseLevel=-1)
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
            mylog('[Byzantine] retrying (%s, %d) caused by %s...' % (hostname, port, str(e)), verboseLevel=-1)
    return s


def prepareIPList(content):
    ip_list = content.strip().split('\n')
    return [(host, BASE_PORT) for host in ip_list if host]


def byzantine_test(options):
    """
    拜占庭节点主流程:
    1. 加载密钥（与其他诚实节点相同的密钥文件）
    2. 启动 TCP 服务器，接受其他节点的连接
    3. 连接到所有其他节点
    4. 等待所有节点完成握手
    5. 立即退出进程
    """
    print("=" * 60)
    print("  Byzantine Node - ID: %d" % options.myid)
    print("  Behavior: Connect all peers, then crash immediately")
    print("=" * 60)

    # 加载密钥（拜占庭节点需要相同的密钥以完成握手）
    initiateThresholdSig(options.threshold_keys)
    initiateECDSAKeys(options.ecdsa)
    initiateThresholdEnc(options.threshold_encs)

    # 解析主机列表
    ip_mappings = prepareIPList(open(expanduser(options.hosts), 'r').read())
    N = len(ip_mappings)
    myID = options.myid

    print("[Byzantine] N=%d, myID=%d" % (N, myID))

    # Step 1: 启动 TCP 服务器（接受其他节点的传入连接）
    _, port = ip_mappings[myID]
    server = listen_to_channel(port)

    # Step 2: 连接到所有其他节点
    connections = []
    for j in range(N):
        if j == myID:
            continue  # 跳过自身
        host, p = ip_mappings[j]
        conn = connect_to_channel(host, p, myID)
        connections.append((j, conn))
        print("[Byzantine] -> Connected to node %d (%s:%d)" % (j, host, p))

    print("[Byzantine] All %d outgoing connections established" % len(connections))

    # Step 3: 等待其他节点完成连入
    # 其他诚实节点会重试连接直到成功，给它们足够时间
    wait_time = 10
    print("[Byzantine] Waiting %d seconds for all peers to connect..." % wait_time)
    time.sleep(wait_time)

    # Step 4: 报告状态后退出
    print("[Byzantine] Handshake complete. %d connections active." % (len(connections) + 1))
    print("[Byzantine] Byzantine behavior: CRASHING NOW!")
    print("[Byzantine] (Process will exit. Remaining honest nodes should continue consensus.)")
    print("=" * 60)

    # 关闭所有连接
    for j, conn in connections:
        try:
            conn.close()
        except Exception:
            pass
    server.stop()

    # 退出进程
    sys.exit(0)


if __name__ == '__main__':
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
    parser.add_option("--my-id", dest="myid",
                      help="Byzantine node's party ID", metavar="ID", type="int", default=0)
    (options, args) = parser.parse_args()

    if options.ecdsa and options.threshold_keys and options.threshold_encs and options.n:
        byzantine_test(options)
    else:
        parser.error('Please specify the arguments')

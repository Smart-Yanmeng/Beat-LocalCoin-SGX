#!/bin/bash
# Deploy and run 16-node BEAT distributed test
PASS='York@233'
SSH="sshpass -p $PASS ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10"

ALL_IPS=(
    "120.27.215.50"   # node 0
    "116.62.149.8"    # node 1
    "47.98.121.97"    # node 2
    "116.62.240.167"  # node 3
    "121.43.234.253"  # node 4
    "121.199.72.252"  # node 5
    "121.40.130.83"   # node 6
    "121.40.94.52"    # node 7
    "120.26.46.218"   # node 8
    "120.55.86.74"    # node 9
    "121.40.255.201"  # node 10
    "121.43.148.183"  # node 11
    "121.40.158.250"  # node 12
    "121.40.117.123"  # node 13
    "121.40.88.101"   # node 14
    "121.40.118.7"    # node 15
)

N=16
T=4  # N/4 for BEAT
RESULTS="/home/charlotte/MyWorkSpace/PROJECT/dumbo/beat_16node_results.csv"

echo "=== Step 1: Create 16-node hosts file ==="
# Generate hosts file
for i in $(seq 0 15); do
    echo "${ALL_IPS[$i]}"
done > /tmp/beat_hosts_16

echo "Hosts file created:"
cat /tmp/beat_hosts_16

echo ""
echo "=== Step 2: Update honest_party_test_EC2.py for 16 nodes ==="
# Create updated Python script with 16-node IP mapping
cat > /tmp/honest_party_test_EC2_16node.py << 'PYTHON_EOF'
#!/usr/bin/python
__author__ = 'aluex'

from gevent import monkey

monkey.patch_all()

from gevent.queue import *
from gevent import Greenlet
from ..core.utils import bcolors, mylog, initiateThresholdSig
from ..core.includeTransaction import honestParty
from collections import defaultdict
from ..core.bkr_acs import initBeforeBinaryConsensus
import gevent
import os
from ..core.utils import ACSException, checkExceptionPerGreenlet, encodeTransaction, getKeys, \
    deepEncode, deepDecode, randomTransaction, initiateECDSAKeys, initiateThresholdEnc, finishTransactionLeap, \
    initiateRND
from gevent.server import StreamServer
import time

import socks
import struct
import math

from subprocess import check_output
from os.path import expanduser
from random import Random
import sched
from socket import error as SocketError
from ..commoncoin.thresprf_gipc import initialize as initializeGIPC

TOR_SOCKSPORT = range(9050, 9150)
WAITING_SETUP_TIME_IN_SEC = 3


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
    s = socks.socksocket()
    while retry:
        try:
            s = socks.socksocket()
            s.connect((hostname, port))
            retry = False
        except Exception as e:  # socks.SOCKS5Error:
            retry = True
            gevent.sleep(1)
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


BASE_PORT = 49500


def prepareIPList(content):
    global IP_LIST, IP_MAPPINGS
    IP_LIST = content.strip().split('\n')
    IP_MAPPINGS = [(host, BASE_PORT) for host in IP_LIST if host]


IP_LIST = None
IP_MAPPINGS = None


mylog("[INIT] IP_MAPPINGS: %s" % repr(IP_MAPPINGS))


def client_test_freenet(N, t, version, options):
    """
    Test for the client with random delay channels
    """
    maxdelay = 0.01

    initiateThresholdSig(options.threshold_keys)
    initiateECDSAKeys(options.ecdsa)
    initiateThresholdEnc(options.threshold_encs)
    initializeGIPC(getKeys()[0])

    buffers = list(map(lambda _: Queue(1), range(N)))

    # 16-node IP to ID mapping
    IP_TO_ID = {
        "120.27.215.50": 0,
        "116.62.149.8": 1,
        "47.98.121.97": 2,
        "116.62.240.167": 3,
        "121.43.234.253": 4,
        "121.199.72.252": 5,
        "121.40.130.83": 6,
        "121.40.94.52": 7,
        "120.26.46.218": 8,
        "120.55.86.74": 9,
        "121.40.255.201": 10,
        "121.43.148.183": 11,
        "121.40.158.250": 12,
        "121.40.117.123": 13,
        "121.40.88.101": 14,
        "121.40.118.7": 15
    }
    
    local_ip = check_output(['curl', '-s', '--connect-timeout', '5', 'ifconfig.me']).decode().strip()
    
    if local_ip in IP_TO_ID:
        myID = IP_TO_ID[local_ip]
    else:
        print("ERROR: IP %s not found in IP_TO_ID mapping" % local_ip)
        return
    
    N = len(IP_LIST)
    print("localIP %s, myID %s" % (local_ip, myID))
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

    transactionSet = set([encodeTransaction(randomTransaction()) for trC in range(int(options.tx))])

    for i in iterList:
        bc, sd = makeBroadcast(i)
        bcList[i] = bc
        sdList[i] = sd

        def makeRecv(ii):
            def recv():
                s = buffers[ii].get()
                return decode(s)[1:]
            return recv

        th = Greenlet(honestParty, i, N, t, controlChannels[i], bcList[i], makeRecv(i), sdList[i], options.B)
        controlChannels[i].put(('IncludeTransaction', transactionSet))
        th.start_later(random.random() * maxdelay)
        ts.append(th)

    try:
        gevent.joinall(ts)
    except ACSException:
        print('ACSException')
        gevent.killall(ts)
    except finishTransactionLeap:
        print('msgCounter', msgCounter)
        print('msgTypeCounter', msgTypeCounter)
        logChannel.put(StopIteration)
        mylog("=====", verboseLevel=-1)
        for item in logChannel:
            mylog(item, verboseLevel=-1)
        mylog("=====", verboseLevel=-1)
        continue
    except gevent.hub.LoopExit:
        print('LoopExit')
        while True:
            gevent.sleep(1)
        checkExceptionPerGreenlet()
    finally:
        print('Concensus Finished')

    print('End?!')


if __name__ == '__main__':
    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option("-e", "--ecdsa-keys", dest="ecdsa",
                      help="Location of ECDSA keys", metavar="KEYS")
    parser.add_option("-k", "--threshold-keys", dest="threshold_keys",
                      help="Location of threshold signature keys", metavar="KEYS")
    parser.add_option("-c", "--threshold-enc", dest="threshold_encs",
                      help="Location of threshold encryption keys", metavar="KEYS")
    parser.add_option("-s", "--hosts", dest="hosts",
                      help="Location of hosts file", metavar="HOSTS")
    parser.add_option("-n", "--number", dest="n",
                      help="Number of parties", metavar="N", type="int")
    parser.add_option("-p", "--tx-path", dest="txpath",
                      help="Path to transactions", metavar="TXPATH")
    parser.add_option("-a", "--negotiated-time", dest="delaytime",
                      help="Negotiated time for experiments", metavar="DELAY", type="float")
    parser.add_option("-b", "--propose-size", dest="B",
                      help="Number of transactions to propose", metavar="B", type="int")
    parser.add_option("-t", "--tolerance", dest="t",
                      help="Tolerance of adversaries", metavar="T", type="int")
    parser.add_option("-x", "--transactions", dest="tx",
                      help="Number of transactions proposed by each party", metavar="TX", type="int", default=-1)
    parser.add_option("-v", "--version", dest="v",
                      help="Version of the code to use", metavar="VERSION")
    parser.add_option("-i", "--id", dest="id",
                      help="Manual override for party id", metavar="ID")
    (options, args) = parser.parse_args()
    prepareIPList(open(expanduser(options.hosts), 'r').read())
    if (options.ecdsa and options.threshold_keys and options.threshold_encs and options.n and options.t and options.v):
        if not options.B:
            options.B = int(math.ceil(options.n * math.log(options.n)))
        if options.tx < 0:
            options.tx = options.B
        client_test_freenet(options.n, options.t, options.v, options)
PYTHON_EOF

echo "Updated script created"

#!/bin/bash
# beat-localcoin 7节点分布式测试启动脚本
# 用法: bash run_beat7.sh <B值> <节点ID>

B=$1
NODE_ID=$2

cd /root/beat-localcoin
export PYTHONPATH=/usr/local/lib/python3.10/dist-packages:/root/beat-localcoin

exec python3 -c "
import sys
sys.argv = ['honest_party_test_EC2', '-k', 'thsig7_2.keys', '-e', 'ecdsa2.keys', '-c', 'thenc7_2.keys', '-s', 'hosts', '-b', '$B', '-n', '7', '-t', '2', '-v', '1', '-a', '50']
from adaptive.test.honest_party_test_EC2 import *
" 2>&1

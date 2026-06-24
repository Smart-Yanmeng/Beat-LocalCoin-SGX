#!/bin/bash
# Simple BEAT test on single node
PASS='York@233'
SSH="sshpass -p $PASS ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10"

NODE0="120.27.215.50"

echo "=== Simple BEAT Test on Single Node ==="

$SSH root@$NODE0 "cd /root/BEAT/BEAT0 && \
    export LIBRARY_PATH=/usr/local/lib:\$LIBRARY_PATH && \
    export LD_LIBRARY_PATH=/usr/local/lib:\$LD_LIBRARY_PATH && \
    python3 -m BEAT.test.honest_party_test \
        -k thsig4_1.keys \
        -e ecdsa.keys \
        -c thenc4_1.keys \
        -n 4 \
        -t 1 \
        -b 1 2>&1 | head -50"

echo ""
echo "Test completed"

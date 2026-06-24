#!/bin/bash
# Simple 2-node BEAT test
PASS='York@233'
SSH="sshpass -p $PASS ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10"

NODE0="120.27.215.50"
NODE1="116.62.149.8"

N=2
T=0  # For 2 nodes, t=0

echo "=== 2-node BEAT Test ==="

# Create hosts file
echo "$NODE0" > /tmp/beat_hosts_2
echo "$NODE1" >> /tmp/beat_hosts_2

# Deploy hosts
cat /tmp/beat_hosts_2 | $SSH root@$NODE0 "cat > /root/BEAT/BEAT0/hosts"
cat /tmp/beat_hosts_2 | $SSH root@$NODE1 "cat > /root/BEAT/BEAT0/hosts"

# Generate keys
$SSH root@$NODE0 "cd /root/BEAT/BEAT0 && \
    export LIBRARY_PATH=/usr/local/lib:\$LIBRARY_PATH && \
    export LD_LIBRARY_PATH=/usr/local/lib:\$LD_LIBRARY_PATH && \
    python3 -m BEAT.commoncoin.prf_generate_keys $N $((T+1)) thsig${N}_${T}.keys && \
    python3 -m BEAT.threshenc.generate_keys $N $((N-2*T)) thenc${N}_${T}.keys"

# Distribute keys
$SSH root@$NODE0 "scp -o StrictHostKeyChecking=no /root/BEAT/BEAT0/thsig${N}_${T}.keys root@${NODE1}:/root/BEAT/BEAT0/"
$SSH root@$NODE0 "scp -o StrictHostKeyChecking=no /root/BEAT/BEAT0/thenc${N}_${T}.keys root@${NODE1}:/root/BEAT/BEAT0/"
$SSH root@$NODE0 "scp -o StrictHostKeyChecking=no /root/BEAT/BEAT0/ecdsa.keys root@${NODE1}:/root/BEAT/BEAT0/"

# Run on both nodes
$SSH -f root@$NODE0 "cd /root/BEAT/BEAT0 && \
    export LIBRARY_PATH=/usr/local/lib:\$LIBRARY_PATH && \
    export LD_LIBRARY_PATH=/usr/local/lib:\$LD_LIBRARY_PATH && \
    python3 -m BEAT.test.honest_party_test_EC2 \
        -k thsig${N}_${T}.keys \
        -e ecdsa.keys \
        -c thenc${N}_${T}.keys \
        -s hosts \
        -n $N \
        -t $T \
        -b 10 \
        -x 10 \
        -v 1 > /tmp/beat-test-0.log 2>&1 &"

$SSH -f root@$NODE1 "cd /root/BEAT/BEAT0 && \
    export LIBRARY_PATH=/usr/local/lib:\$LIBRARY_PATH && \
    export LD_LIBRARY_PATH=/usr/local/lib:\$LD_LIBRARY_PATH && \
    python3 -m BEAT.test.honest_party_test_EC2 \
        -k thsig${N}_${T}.keys \
        -e ecdsa.keys \
        -c thenc${N}_${T}.keys \
        -s hosts \
        -n $N \
        -t $T \
        -b 10 \
        -x 10 \
        -v 1 > /tmp/beat-test-1.log 2>&1 &"

echo "Waiting for test to complete..."
sleep 30

echo "=== Node 0 log ==="
$SSH root@$NODE0 "tail -20 /tmp/beat-test-0.log"

echo ""
echo "=== Node 1 log ==="
$SSH root@$NODE1 "tail -20 /tmp/beat-test-1.log"

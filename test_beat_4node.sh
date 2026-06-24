#!/bin/bash
# Simple 4-node BEAT test
PASS='York@233'
SSH="sshpass -p $PASS ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10"

NODES=("120.27.215.50" "116.62.149.8" "47.98.121.97" "116.62.240.167")

N=4
T=1

echo "=== 4-node BEAT Test ==="

# Create hosts file
for ip in "${NODES[@]}"; do
    echo "$ip"
done > /tmp/beat_hosts_4

# Deploy hosts
for ip in "${NODES[@]}"; do
    cat /tmp/beat_hosts_4 | $SSH root@$ip "cat > /root/BEAT/BEAT0/hosts"
done

# Generate keys on first node
$SSH root@${NODES[0]} "cd /root/BEAT/BEAT0 && \
    export LIBRARY_PATH=/usr/local/lib:\$LIBRARY_PATH && \
    export LD_LIBRARY_PATH=/usr/local/lib:\$LD_LIBRARY_PATH && \
    python3 -m BEAT.commoncoin.prf_generate_keys $N $((T+1)) thsig${N}_${T}.keys && \
    python3 -m BEAT.threshenc.generate_keys $N $((N-2*T)) thenc${N}_${T}.keys"

# Distribute keys
for i in 1 2 3; do
    $SSH root@${NODES[0]} "scp -o StrictHostKeyChecking=no /root/BEAT/BEAT0/thsig${N}_${T}.keys root@${NODES[$i]}:/root/BEAT/BEAT0/"
    $SSH root@${NODES[0]} "scp -o StrictHostKeyChecking=no /root/BEAT/BEAT0/thenc${N}_${T}.keys root@${NODES[$i]}:/root/BEAT/BEAT0/"
    $SSH root@${NODES[0]} "scp -o StrictHostKeyChecking=no /root/BEAT/BEAT0/ecdsa.keys root@${NODES[$i]}:/root/BEAT/BEAT0/"
done

# Run on all nodes
for i in 0 1 2 3; do
    $SSH -f root@${NODES[$i]} "cd /root/BEAT/BEAT0 && \
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
            -v 1 > /tmp/beat-test-${i}.log 2>&1 &"
done

echo "Waiting for test to complete (60 seconds)..."
sleep 60

echo ""
echo "=== Results ==="
for i in 0 1 2 3; do
    echo "Node $i (${NODES[$i]}):"
    $SSH root@${NODES[$i]} "tail -10 /tmp/beat-test-${i}.log"
    echo ""
done

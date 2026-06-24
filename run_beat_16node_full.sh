#!/bin/bash
# 16-node BEAT distributed test - Full deployment and execution
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

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  16-node BEAT Distributed Test                         ║"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║  N=$N, T=$T                                            ║"
echo "║  Nodes: ${#ALL_IPS[@]} servers                          ║"
echo "╚══════════════════════════════════════════════════════════╝"

# Step 1: Generate hosts file
echo ""
echo "[Step 1] Generating hosts file..."
for i in $(seq 0 15); do
    echo "${ALL_IPS[$i]}"
done > /tmp/beat_hosts_16
echo "  Created /tmp/beat_hosts_16"

# Step 2: Deploy hosts file to all nodes
echo ""
echo "[Step 2] Deploying hosts file to all nodes..."
for ip in "${ALL_IPS[@]}"; do
    $SSH root@$ip "cp /root/BEAT/BEAT0/hosts /root/BEAT/BEAT0/hosts.bak 2>/dev/null; true" 2>/dev/null
    cat /tmp/beat_hosts_16 | $SSH root@$ip "cat > /root/BEAT/BEAT0/hosts" 2>/dev/null &
done
wait
echo "  Hosts file deployed to all nodes"

# Step 3: Generate threshold keys on first node
echo ""
echo "[Step 3] Generating threshold keys on node 0..."
$SSH root@${ALL_IPS[0]} "cd /root/BEAT/BEAT0 && \
    export LIBRARY_PATH=/usr/local/lib:\$LIBRARY_PATH && \
    export LD_LIBRARY_PATH=/usr/local/lib:\$LD_LIBRARY_PATH && \
    python3 -m BEAT.commoncoin.prf_generate_keys $N $((T+1)) > thsig${N}_${T}.keys && \
    python3 -m BEAT.threshenc.generate_keys $N $((N-2*T)) > thenc${N}_${T}.keys && \
    echo 'Keys generated successfully'" 2>&1
sleep 2

# Step 4: Distribute keys to all nodes
echo ""
echo "[Step 4] Distributing keys to all nodes..."
for i in $(seq 1 15); do
    ip=${ALL_IPS[$i]}
    $SSH root@${ALL_IPS[0]} "scp -o StrictHostKeyChecking=no /root/BEAT/BEAT0/thsig${N}_${T}.keys root@${ip}:/root/BEAT/BEAT0/" 2>/dev/null &
    $SSH root@${ALL_IPS[0]} "scp -o StrictHostKeyChecking=no /root/BEAT/BEAT0/thenc${N}_${T}.keys root@${ip}:/root/BEAT/BEAT0/" 2>/dev/null &
    $SSH root@${ALL_IPS[0]} "scp -o StrictHostKeyChecking=no /root/BEAT/BEAT0/ecdsa.keys root@${ip}:/root/BEAT/BEAT0/" 2>/dev/null &
done
wait
echo "  Keys distributed to all nodes"

# Step 5: Update honest_party_test_EC2.py on all nodes
echo ""
echo "[Step 5] Deploying updated honest_party_test_EC2.py..."
# The updated script is already in /tmp/honest_party_test_EC2_16node.py
# We need to deploy it to all nodes
for ip in "${ALL_IPS[@]}"; do
    $SSH root@$ip "cp /root/BEAT/BEAT0/BEAT/test/honest_party_test_EC2.py /root/BEAT/BEAT0/BEAT/test/honest_party_test_EC2.py.bak" 2>/dev/null
done

# Step 6: Run experiments with different B values
B_LIST=(10 50 100 250 500 1000)
echo ""
echo "B,node0,node1,node2,node3,node4,node5,node6,node7,node8,node9,node10,node11,node12,node13,node14,node15" > "$RESULTS"

for B in "${B_LIST[@]}"; do
    echo ""
    echo "=== B=$B ==="
    
    # Kill all existing processes
    for ip in "${ALL_IPS[@]}"; do
        $SSH root@$ip "pkill -9 -f honest_party_test 2>/dev/null; rm -f /root/BEAT/BEAT0/beat-node-*.log /tmp/beat-node-*.out; true" 2>/dev/null &
    done
    wait
    sleep 3
    
    # Launch all 16 nodes
    echo "  Launching 16 nodes..."
    for i in $(seq 0 15); do
        ip=${ALL_IPS[$i]}
        $SSH -f root@$ip "cd /root/BEAT/BEAT0 && \
            export LIBRARY_PATH=/usr/local/lib:\$LIBRARY_PATH && \
            export LD_LIBRARY_PATH=/usr/local/lib:\$LD_LIBRARY_PATH && \
            nohup python3 -m BEAT.test.honest_party_test_EC2 \
                -k thsig${N}_${T}.keys \
                -e ecdsa.keys \
                -c thenc${N}_${T}.keys \
                -s hosts \
                -n $N \
                -t $T \
                -b $B \
                -x $B \
                -v 1 \
                > /tmp/beat-node-${i}.out 2>&1 &"
    done
    
    # Wait for completion (max 300s)
    done=0
    for t in $(seq 10 10 300); do
        done=0
        for i in $(seq 0 15); do
            ip=${ALL_IPS[$i]}
            result=$($SSH root@$ip "grep -c 'Consensus Finished' /tmp/beat-node-${i}.out 2>/dev/null || echo 0" 2>&1)
            if [ "$result" -ge 1 ] 2>/dev/null; then
                done=$((done+1))
            fi
        done
        if [ "$done" -ge 16 ]; then
            break
        fi
        echo "  waiting... ${t}s, $done/16"
    done
    
    # Collect results
    row="$B"
    for i in $(seq 0 15); do
        ip=${ALL_IPS[$i]}
        result=$($SSH root@$ip "grep 'Total Time' /tmp/beat-node-${i}.out 2>/dev/null | grep -oP 'Total Time: \K[0-9.]+' || echo ''" 2>&1)
        row="$row,${result:-}"
    done
    echo "$row" >> "$RESULTS"
    echo "  $row"
done

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  All done! Results saved to:                           ║"
echo "║  $RESULTS"
echo "╚══════════════════════════════════════════════════════════╝"

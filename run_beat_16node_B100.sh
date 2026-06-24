#!/bin/bash
# 16-node BEAT test with B=100
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
T=4
B=100
RESULTS="/home/charlotte/MyWorkSpace/PROJECT/dumbo/beat_16node_B100.csv"

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  16-node BEAT Test (B=$B, Python 3.8)                  ║"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║  N=$N, T=$T, B=$B                                      ║"
echo "╚══════════════════════════════════════════════════════════╝"

# Step 1: Kill existing processes
echo ""
echo "[Step 1] Killing existing BEAT processes..."
for ip in "${ALL_IPS[@]}"; do
    $SSH root@$ip "pkill -9 -f honest_party_test 2>/dev/null; rm -f /root/BEAT/BEAT0/beat-node-*.log /tmp/beat-node-*.out; true" 2>/dev/null &
done
wait
sleep 3
echo "  Processes cleaned"

# Step 2: Launch all 16 nodes
echo ""
echo "[Step 2] Launching 16 nodes with B=$B..."
for i in $(seq 0 15); do
    ip=${ALL_IPS[$i]}
    $SSH -f root@$ip "cd /root/BEAT/BEAT0 && \
        export LIBRARY_PATH=/usr/local/lib:\$LIBRARY_PATH && \
        export LD_LIBRARY_PATH=/usr/local/lib:\$LD_LIBRARY_PATH && \
        nohup python3.8 -m BEAT.test.honest_party_test_EC2 \
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
echo "  All 16 nodes launched"

# Step 3: Wait for completion (max 600s)
echo ""
echo "[Step 3] Waiting for consensus to complete..."
done=0
for t in $(seq 10 10 600); do
    done=0
    for i in $(seq 0 15); do
        ip=${ALL_IPS[$i]}
        result=$($SSH root@$ip "grep -c 'Consensus Finished' /tmp/beat-node-${i}.out 2>/dev/null || echo 0" 2>&1)
        if [ "$result" -ge 1 ] 2>/dev/null; then
            done=$((done+1))
        fi
    done
    if [ "$done" -ge 16 ]; then
        echo "  All 16 nodes completed at ${t}s"
        break
    fi
    if [ $((t % 30)) -eq 0 ]; then
        echo "  ${t}s elapsed, $done/16 nodes completed"
    fi
done

# Step 4: Collect results
echo ""
echo "[Step 4] Collecting results..."
echo "B,node0,node1,node2,node3,node4,node5,node6,node7,node8,node9,node10,node11,node12,node13,node14,node15" > "$RESULTS"

row="$B"
for i in $(seq 0 15); do
    ip=${ALL_IPS[$i]}
    result=$($SSH root@$ip "grep 'Total Time' /tmp/beat-node-${i}.out 2>/dev/null | grep -oP 'Total Time: \K[0-9.]+' || echo ''" 2>&1)
    row="$row,${result:-}"
done
echo "$row" >> "$RESULTS"
echo "  $row"

# Step 5: Show summary
echo ""
echo "[Step 5] Summary..."
times=()
for i in $(seq 0 15); do
    ip=${ALL_IPS[$i]}
    result=$($SSH root@$ip "grep 'Total Time' /tmp/beat-node-${i}.out 2>/dev/null | grep -oP 'Total Time: \K[0-9.]+' || echo ''" 2>&1)
    if [ -n "$result" ]; then
        times+=($result)
    fi
done

if [ ${#times[@]} -gt 0 ]; then
    min=$(printf '%s\n' "${times[@]}" | sort -n | head -1)
    max=$(printf '%s\n' "${times[@]}" | sort -n | tail -1)
    avg=$(echo "${times[@]}" | tr ' ' '\n' | awk '{sum+=$1} END {print sum/NR}')
    echo "  Min time: ${min}s"
    echo "  Max time: ${max}s"
    echo "  Avg time: ${avg}s"
fi

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  Test completed! Results saved to:                     ║"
echo "║  $RESULTS"
echo "╚══════════════════════════════════════════════════════════╝"

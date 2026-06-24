#!/bin/bash
# Batch experiment runner: N=4, f=1, varying B(k)

PASS='York@233'
IPS=("8.160.188.185" "8.160.188.178" "8.160.180.163" "8.160.187.104")
PORT=7001
N=4
T=1
B_VALUES=(10 100 250 500 750 1000 2500 5000 7500 10000 25000 50000 75000 100000)

RESULTS_DIR="/home/charlotte/MyWorkSpace/PROJECT/acs/results"
mkdir -p "$RESULTS_DIR"

SSH_CMD="sshpass -p $PASS ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no -o ServerAliveInterval=30"
SCP_CMD="sshpass -p $PASS scp -o StrictHostKeyChecking=no"

for B in "${B_VALUES[@]}"; do
    echo ""
    echo "=============================================="
    echo "  Running B=$B (N=$N, f=$T)"
    echo "=============================================="

    # 1. Generate config files
    for i in 0 1 2 3; do
        cat > /tmp/config-${i}.json <<EOF
{
  "N": $N,
  "t": $T,
  "k": $B,
  "my_id": $i,
  "peers": [
    "${IPS[0]}:$PORT",
    "${IPS[1]}:$PORT",
    "${IPS[2]}:$PORT",
    "${IPS[3]}:$PORT"
  ]
}
EOF
    done

    # 2. Upload configs to all servers
    for i in 0 1 2 3; do
        $SCP_CMD /tmp/config-${i}.json root@${IPS[$i]}:/root/acs/conf/adkg_4_remote/config-${i}.json &
    done
    wait

    # 3. Kill any leftover processes
    for i in 0 1 2 3; do
        $SSH_CMD root@${IPS[$i]} 'pkill -f vaba_run 2>/dev/null; rm -f /root/acs/benchmark-logs/node-*.log' &
    done
    wait
    sleep 2

    # 4. Get synchronized start time
    CURRENT_TIME=$($SSH_CMD root@${IPS[0]} 'date +%s')
    START_TIME=$((CURRENT_TIME + 15))
    echo "  Start time: $START_TIME"

    # 5. Launch all 4 nodes
    for i in 0 1 2 3; do
        $SSH_CMD root@${IPS[$i]} "cd /root/acs && nohup python3 -m scripts.vaba_run -d -f conf/adkg_4_remote/config-${i}.json -time $START_TIME > benchmark-logs/node-${i}.log 2>&1 &" &
    done
    wait
    echo "  Nodes launched, waiting..."

    # 6. Wait for completion
    if [ $B -le 1000 ]; then
        TIMEOUT=120
    elif [ $B -le 10000 ]; then
        TIMEOUT=300
    elif [ $B -le 50000 ]; then
        TIMEOUT=600
    else
        TIMEOUT=1200
    fi

    ELAPSED=0
    COMPLETED=0
    while [ $ELAPSED -lt $TIMEOUT ]; do
        sleep 5
        ELAPSED=$((ELAPSED + 5))
        DONE=$($SSH_CMD root@${IPS[0]} 'grep -c "Total bytes sent" /root/acs/benchmark-logs/node-0.log 2>/dev/null' 2>/dev/null)
        if [ "$DONE" = "1" ]; then
            COMPLETED=1
            sleep 3
            break
        fi
    done

    if [ $COMPLETED -eq 0 ]; then
        echo "  WARNING: Timeout after ${TIMEOUT}s for B=$B"
    fi

    # 7. Collect results
    mkdir -p "$RESULTS_DIR/B_${B}"
    for i in 0 1 2 3; do
        $SCP_CMD root@${IPS[$i]}:/root/acs/benchmark-logs/node-${i}.log "$RESULTS_DIR/B_${B}/node-${i}.log" 2>/dev/null
    done

    # 8. Print summary
    echo "  --- Results for B=$B ---"
    for i in 0 1 2 3; do
        if [ -f "$RESULTS_DIR/B_${B}/node-${i}.log" ]; then
            ADKG_LINE=$(grep "ADKG time" "$RESULTS_DIR/B_${B}/node-${i}.log" 2>/dev/null)
            BYTES_LINE=$(grep "Total bytes sent" "$RESULTS_DIR/B_${B}/node-${i}.log" 2>/dev/null | sed 's/.*\[INFO\]: //')
            if [ -n "$ADKG_LINE" ]; then
                TIME=$(echo "$ADKG_LINE" | grep -oP 'ADKG time:\s+\K[0-9.]+')
                echo "  Node $i: ADKG=${TIME}s | $BYTES_LINE"
            else
                echo "  Node $i: (no timing data)"
            fi
        else
            echo "  Node $i: (no log)"
        fi
    done
done

echo ""
echo "=============================================="
echo "  ALL EXPERIMENTS COMPLETE"
echo "=============================================="

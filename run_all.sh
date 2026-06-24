#!/bin/bash
PASS='York@233'
IPS=("8.160.188.185" "8.160.188.178" "8.160.180.163" "8.160.187.104")
PORT=7001
N=4
T=1
B_VALUES=(10 100 250 500 750 1000 2500 5000 7500 10000 25000 50000 75000 100000)

RESULTS_DIR="/home/charlotte/MyWorkSpace/PROJECT/acs/results"
mkdir -p "$RESULTS_DIR"

run_one() {
    local B=$1
    echo "=== B=$B ==="

    # Generate and upload configs
    for i in 0 1 2 3; do
        echo "{\"N\":$N,\"t\":$T,\"k\":$B,\"my_id\":$i,\"peers\":[\"${IPS[0]}:$PORT\",\"${IPS[1]}:$PORT\",\"${IPS[2]}:$PORT\",\"${IPS[3]}:$PORT\"]}" > /tmp/config-${i}.json
        sshpass -p "$PASS" scp -o StrictHostKeyChecking=no /tmp/config-${i}.json root@${IPS[$i]}:/root/acs/conf/adkg_4_remote/config-${i}.json 2>/dev/null &
    done
    wait

    # Kill old processes
    for i in 0 1 2 3; do
        sshpass -p "$PASS" ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no root@${IPS[$i]} 'pkill -f vaba_run 2>/dev/null; rm -f /root/acs/benchmark-logs/node-*.log' 2>/dev/null &
    done
    wait
    sleep 2

    # Get start time
    local CURRENT_TIME=$(sshpass -p "$PASS" ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no root@${IPS[0]} 'date +%s' 2>/dev/null)
    local START_TIME=$((CURRENT_TIME + 15))

    # Launch nodes
    for i in 0 1 2 3; do
        sshpass -p "$PASS" ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no root@${IPS[$i]} "cd /root/acs && nohup python3 -m scripts.vaba_run -d -f conf/adkg_4_remote/config-${i}.json -time $START_TIME > benchmark-logs/node-${i}.log 2>&1 &" 2>/dev/null &
    done
    wait

    # Wait for completion
    local TIMEOUT=1200
    local ELAPSED=0
    while [ $ELAPSED -lt $TIMEOUT ]; do
        sleep 5
        ELAPSED=$((ELAPSED + 5))
        local DONE=$(sshpass -p "$PASS" ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no root@${IPS[0]} 'grep -c "Total bytes sent" /root/acs/benchmark-logs/node-0.log 2>/dev/null' 2>/dev/null)
        if [ "$DONE" = "1" ]; then
            sleep 3
            break
        fi
    done

    if [ $ELAPSED -ge $TIMEOUT ]; then
        echo "  TIMEOUT for B=$B"
    fi

    # Collect
    mkdir -p "$RESULTS_DIR/B_${B}"
    for i in 0 1 2 3; do
        sshpass -p "$PASS" scp -o StrictHostKeyChecking=no root@${IPS[$i]}:/root/acs/benchmark-logs/node-${i}.log "$RESULTS_DIR/B_${B}/node-${i}.log" 2>/dev/null
    done

    # Print
    grep "ADKG time" "$RESULTS_DIR/B_${B}/node-0.log" 2>/dev/null || echo "  No ADKG time for node 0"
    grep "Total bytes" "$RESULTS_DIR/B_${B}/node-0.log" 2>/dev/null
    echo ""
}

for B in "${B_VALUES[@]}"; do
    run_one $B
done

echo "=== ALL DONE ==="

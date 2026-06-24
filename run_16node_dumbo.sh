#!/bin/bash
# 16-node Dumbo B sweep with public IPs
PASS='York@233'
SSH="sshpass -p $PASS ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10"

ALL_IPS=("120.27.215.50" "116.62.149.8" "47.98.121.97" "116.62.240.167" "121.43.234.253" "121.199.72.252" "121.40.130.83" "121.40.94.52" "120.26.46.218" "120.55.86.74" "121.40.255.201" "121.43.148.183" "121.40.158.250" "121.40.117.123" "121.40.88.101" "121.40.118.7")
B_LIST=(10 100 250 500 750 1000 2500 5000 7500 10000 25000 50000 75000 100000)
N=16
K=1
RESULTS="/home/charlotte/MyWorkSpace/PROJECT/dumbo/dumbo_16node_results_public.csv"

echo "B,node0,node1,node2,node3,node4,node5,node6,node7,node8,node9,node10,node11,node12,node13,node14,node15" > "$RESULTS"

for B in "${B_LIST[@]}"; do
    echo "=== B=$B ==="

    # Kill all
    for ip in "${ALL_IPS[@]}"; do
        $SSH root@$ip "pkill -9 -f run_socket_node 2>/dev/null; pkill -9 -f start_node 2>/dev/null; rm -f /root/dumbo/log/consensus-node-*.log /tmp/node-*.out; true" 2>/dev/null &
    done
    wait
    sleep 5

    # Launch all 16
    for i in $(seq 0 15); do
        ip=${ALL_IPS[$i]}
        $SSH -f root@$ip "cd /root/dumbo && export LD_LIBRARY_PATH=/usr/local/lib:\$LD_LIBRARY_PATH && nohup ./start_node.sh $i dumbo $B $K > /tmp/node-$i.out 2>&1 &"
    done

    # Wait for completion (max 600s)
    done=0
    for t in $(seq 30 30 600); do
        done=0
        for i in $(seq 0 15); do
            ip=${ALL_IPS[$i]}
            result=$($SSH root@$ip "grep -c 'breaks in' /root/dumbo/log/consensus-node-$i.log 2>/dev/null || echo 0" 2>&1)
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
        result=$($SSH root@$ip "grep 'breaks in' /root/dumbo/log/consensus-node-$i.log 2>/dev/null | grep -oP 'breaks in \K[0-9.]+'" 2>&1)
        row="$row,${result:-}"
    done
    echo "$row" >> "$RESULTS"
    echo "  $row"
done

echo "All done! Results in $RESULTS"

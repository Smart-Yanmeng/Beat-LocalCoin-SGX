#!/bin/bash
#
# Dumbo 批量实验：依次跑所有 B 值，4 节点并行启动，结果写入 dumbo_wide.csv
# 用法: ./run_dumbo_batch.sh
#
set -u

PASS='York@233'
SSH="sshpass -p $PASS ssh -o StrictHostKeyChecking=no -o ConnectTimeout=15"

# 节点 IP（公网）
declare -a IPS=("120.27.215.50" "116.62.149.8" "47.98.121.97" "116.62.240.167")
N=4
K=1

B_LIST=(10 100 250 500 750 1000 2500 5000 7500 10000 25000 50000 75000 100000)

OUT_CSV="/home/charlotte/MyWorkSpace/PROJECT/dumbo/dumbo_wide.csv"
KILL="pkill -9 -f '[r]un_socket_node.py'"

# CSV header
echo "B,node0,node1,node2,node3" > "$OUT_CSV"

clean_all() {
    for ip in "${IPS[@]}"; do
        $SSH root@$ip "$KILL 2>/dev/null; rm -f /root/dumbo/log/consensus-node-*.log /tmp/node-*.out" 2>/dev/null
    done
}

launch_node() {
    local ip=$1 id=$2 B=$3
    sshpass -p $PASS ssh -o StrictHostKeyChecking=no -f -o ConnectTimeout=15 root@$ip \
        "export LD_LIBRARY_PATH=/usr/local/lib:\$LD_LIBRARY_PATH && cd /root/dumbo && nohup ./start_node.sh $id dumbo $B $K </dev/null > /tmp/node-$id.out 2>&1 &"
}

verify_launched() {
    # Re-launch any node whose /tmp/node-$id.out is missing/empty
    local B=$1
    for i in 0 1 2 3; do
        local has=$($SSH root@${IPS[$i]} "test -s /tmp/node-$i.out && echo 1 || echo 0" 2>/dev/null)
        if [ "${has:-0}" != "1" ]; then
            echo "  re-launching node $i (was not started)"
            launch_node "${IPS[$i]}" "$i" "$B"
        fi
    done
}

get_time() {
    local ip=$1 id=$2
    $SSH root@$ip "grep 'breaks in' /root/dumbo/log/consensus-node-$id.log 2>/dev/null | grep -oP 'breaks in \K[0-9.]+' | head -1" 2>/dev/null
}

for B in "${B_LIST[@]}"; do
    echo "=== B=$B ==="
    clean_all
    sleep 4

    # 4 节点真正并行启动
    for i in 0 1 2 3; do
        launch_node "${IPS[$i]}" "$i" "$B" &
    done
    wait
    sleep 5
    # 检查是否都启动了，没启动的补launch
    verify_launched "$B"
    echo "  launched, waiting for consensus..."

    # 轮询，等够 N-f=3 节点完成即可（dumbo K=1 下第4个节点可能永远等待，属正常）
    # 3 节点完成后再给 30s 宽限，看第4个能否也完成
    MAX=600
    ELAPSED=0
    grace_start=0
    while [ $ELAPSED -lt $MAX ]; do
        sleep 8
        ELAPSED=$((ELAPSED+8))
        done_count=0
        for i in 0 1 2 3; do
            c=$($SSH root@${IPS[$i]} "grep -c 'breaks in' /root/dumbo/log/consensus-node-$i.log 2>/dev/null || echo 0" 2>/dev/null)
            [ "${c:-0}" -ge 1 ] 2>/dev/null && done_count=$((done_count+1))
        done
        echo "  ${ELAPSED}s: $done_count/4 done"
        [ $done_count -ge 4 ] && break
        if [ $done_count -ge 3 ]; then
            if [ $grace_start -eq 0 ]; then
                grace_start=$ELAPSED
            elif [ $((ELAPSED - grace_start)) -ge 30 ]; then
                echo "  3/4 done + grace elapsed, recording (4th node waiting is normal for dumbo K=1)"
                break
            fi
        fi
    done

    # 收集时间
    t0=$(get_time "${IPS[0]}" 0)
    t1=$(get_time "${IPS[1]}" 1)
    t2=$(get_time "${IPS[2]}" 2)
    t3=$(get_time "${IPS[3]}" 3)
    echo "$B,${t0:-NA},${t1:-NA},${t2:-NA},${t3:-NA}" >> "$OUT_CSV"
    echo "  -> $B: $t0 $t1 $t2 $t3"
done

# 收尾清理
clean_all
echo ""
echo "=== DONE. Results: $OUT_CSV ==="
cat "$OUT_CSV"

#!/bin/bash
#
# WaterBear-QS-Q 批量实验：4 台远程服务器常驻 server，对每个 B 发一个 client batch，
# 记录每个节点该 epoch 的 latency(ms) 到 waterbear_wide.csv
#
# 格式: B,node0,node1,node2,node3   (latency in ms)
#
set -u

PASS='York@233'
SSH="sshpass -p $PASS ssh -o StrictHostKeyChecking=no -o ConnectTimeout=15"

declare -a IPS=("120.27.215.50" "116.62.149.8" "47.98.121.97" "116.62.240.167")
WB=/root/waterbear
CLIENT_HOST="120.27.215.50"   # 从 node0 发 client

B_LIST=(10 100 250 500 750 1000 2500 5000 7500 10000 25000 50000 75000 100000)

OUT_CSV="/home/charlotte/MyWorkSpace/PROJECT/dumbo/waterbear_wide.csv"
echo "B,node0,node1,node2,node3" > "$OUT_CSV"

KILL="pkill -9 -f '[b]in/server'"

start_servers() {
    for i in 0 1 2 3; do
        $SSH root@${IPS[$i]} "$KILL 2>/dev/null; rm -rf $WB/var/log/*" 2>/dev/null
    done
    sleep 2
    for i in 0 1 2 3; do
        sshpass -p $PASS ssh -o StrictHostKeyChecking=no -f -o ConnectTimeout=15 root@${IPS[$i]} \
            "cd $WB && nohup ./bin/server $i </dev/null > /tmp/wb-server-$i.out 2>&1 &"
    done
    sleep 8
}

stop_servers() {
    for i in 0 1 2 3; do
        $SSH root@${IPS[$i]} "$KILL 2>/dev/null" 2>/dev/null
    done
}

# latency for a node = 5th numeric field of last Eva.log line
get_latency() {
    local ip=$1 id=$2
    $SSH root@$ip "tail -1 $WB/var/log/$id/*_Eva.log 2>/dev/null | awk '{print \$7}'" 2>/dev/null
}

# count epochs recorded so far on node id
count_epochs() {
    local ip=$1 id=$2
    $SSH root@$ip "cat $WB/var/log/$id/*_Eva.log 2>/dev/null | wc -l" 2>/dev/null
}

echo ">> starting 4 waterbear servers (QS-Q)"
start_servers

# verify listening
ok=0
for i in 0 1 2 3; do
    c=$($SSH root@${IPS[$i]} "ss -tnl | grep -c 11000" 2>/dev/null)
    [ "${c:-0}" -ge 1 ] && ok=$((ok+1))
done
echo "   $ok/4 servers listening"

for B in "${B_LIST[@]}"; do
    echo "=== B=$B ==="
    # epoch counts before this batch
    declare -a before=()
    for i in 0 1 2 3; do before[$i]=$(count_epochs "${IPS[$i]}" $i); done

    # send client batch (type 1 = write batch), wait for replies
    $SSH root@$CLIENT_HOST "cd $WB && timeout 300 ./bin/client 100 1 $B hello 1 >/tmp/wb-client.out 2>&1" 2>/dev/null

    # wait for all 4 nodes to record a new epoch line (max 120s)
    waited=0
    while [ $waited -lt 120 ]; do
        sleep 4; waited=$((waited+4))
        done_count=0
        for i in 0 1 2 3; do
            now=$(count_epochs "${IPS[$i]}" $i)
            [ "${now:-0}" -gt "${before[$i]:-0}" ] 2>/dev/null && done_count=$((done_count+1))
        done
        [ $done_count -ge 4 ] && break
    done

    l0=$(get_latency "${IPS[0]}" 0)
    l1=$(get_latency "${IPS[1]}" 1)
    l2=$(get_latency "${IPS[2]}" 2)
    l3=$(get_latency "${IPS[3]}" 3)
    echo "$B,${l0:-NA},${l1:-NA},${l2:-NA},${l3:-NA}" >> "$OUT_CSV"
    echo "  -> $B: $l0 $l1 $l2 $l3 ms"
done

echo ">> stopping servers"
stop_servers

echo ""
echo "=== DONE: $OUT_CSV ==="
cat "$OUT_CSV"

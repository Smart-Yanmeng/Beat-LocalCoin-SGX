#!/bin/bash
# 假设 4 个 waterbear server 已经用 ssh -f 稳定运行。
# 对每个 B 发一个 client batch，读各节点 Eva.log 最新 epoch 的 latency(ms)。
set -u
PASS='York@233'
SSH="sshpass -p $PASS ssh -o StrictHostKeyChecking=no -o ConnectTimeout=12"
declare -a IPS=("120.27.215.50" "116.62.149.8" "47.98.121.97" "116.62.240.167")
WB=/root/waterbear
CLIENT_HOST="120.27.215.50"
B_LIST=(10 100 250 500 750 1000 2500 5000 7500 10000 25000 50000 75000 100000)
OUT="/home/charlotte/MyWorkSpace/PROJECT/dumbo/waterbear_wide.csv"
echo "B,node0,node1,node2,node3" > "$OUT"

cid=400
epochs() { $SSH root@${IPS[$1]} "cat $WB/var/log/$1/*_Eva.log 2>/dev/null | wc -l" 2>/dev/null; }
lat()    { $SSH root@${IPS[$1]} "tail -1 $WB/var/log/$1/*_Eva.log 2>/dev/null | awk '{print \$7}'" 2>/dev/null; }

for B in "${B_LIST[@]}"; do
  echo "=== B=$B ==="
  declare -a before=()
  for i in 0 1 2 3; do before[$i]=$(epochs $i); done

  cid=$((cid+1))
  # client：大 batch 给更长超时
  to=120; [ "$B" -ge 25000 ] && to=300
  $SSH root@$CLIENT_HOST "cd $WB && timeout $to ./bin/client $cid 1 $B hello 1 >/tmp/wb-cli.out 2>&1" 2>/dev/null

  # 等所有节点记录新 epoch（最多 300s）
  waited=0
  while [ $waited -lt 300 ]; do
    sleep 5; waited=$((waited+5))
    dc=0
    for i in 0 1 2 3; do
      now=$(epochs $i)
      [ "${now:-0}" -gt "${before[$i]:-0}" ] 2>/dev/null && dc=$((dc+1))
    done
    [ $dc -ge 4 ] && break
    # 3/4 也接受（容许1节点掉队），多等15s
    if [ $dc -ge 3 ]; then sleep 15; break; fi
  done

  l0=$(lat 0); l1=$(lat 1); l2=$(lat 2); l3=$(lat 3)
  echo "$B,${l0:-NA},${l1:-NA},${l2:-NA},${l3:-NA}" >> "$OUT"
  echo "  -> $B: $l0 $l1 $l2 $l3 ms"
done

echo "=== DONE: $OUT ==="
cat "$OUT"

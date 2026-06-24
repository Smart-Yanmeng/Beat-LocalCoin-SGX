#!/bin/bash
# ACS (VABA) 实验编排 - 宽表输出
# 输出: B, replica1, replica2, replica3, replica4 (ADKG time)
# 用法: bash acs_wide.sh           (全序列)
#       bash acs_wide.sh 10 100    (指定 B)

PASS='York@233'
IPS=("120.27.215.50" "116.62.149.8" "47.98.121.97" "116.62.240.167")

if [ $# -gt 0 ]; then
    B_VALUES=("$@")
else
    B_VALUES=(10 100 250 500 750 1000 2500 5000 7500 10000 25000 50000 75000 100000)
fi

RESULTS_DIR="/home/charlotte/MyWorkSpace/PROJECT/acs/results/acs_new"
mkdir -p "$RESULTS_DIR"
SUMMARY="$RESULTS_DIR/acs_wide.csv"
# 仅在文件不存在时写头, 避免重跑覆盖历史数据
if [ ! -f "$SUMMARY" ]; then
    echo "B,replica1,replica2,replica3,replica4" > "$SUMMARY"
fi

sshc() {
    timeout 30 sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=15 "root@$1" "$2" 2>/dev/null
}

# 上传最新版 acs_run_node.sh 到所有节点 (避免节点上是旧版的 buffered 版本)
upload_runner() {
    for ip in "${IPS[@]}"; do
        timeout 30 sshpass -p "$PASS" scp -o StrictHostKeyChecking=no -o ConnectTimeout=15 \
            /home/charlotte/MyWorkSpace/PROJECT/acs/acs_run_node.sh "root@$ip:/root/acs/acs_run_node.sh" >/dev/null 2>&1 &
    done
    wait
}

run_one() {
    local B=$1
    echo "=========================================="
    echo "=== B=$B 开始 ($(date '+%H:%M:%S')) ==="

    local NOW=$(date +%s)
    local START_TIME=$((NOW + 60))

    for i in 0 1 2 3; do
        sshc "${IPS[$i]}" "pkill -9 -f vaba_run 2>/dev/null; rm -f /root/acs/benchmark-logs/node-${i}.log /root/acs/benchmark-logs/result-${i}.txt" &
    done
    wait
    sleep 1

    for i in 0 1 2 3; do
        sshc "${IPS[$i]}" "cd /root/acs && setsid bash acs_run_node.sh $i $B $START_TIME > /tmp/acs_${i}.out 2>&1 < /dev/null &" &
    done
    wait
    echo "  4 节点已启动 (START_TIME=$START_TIME)，轮询小结果文件..."

    # 轮询节点0的 result-0.txt 是否非空 (这个文件由 acs_run_node.sh 在 ADKG time 出现后写)
    # 但因为 vaba 进程不会自然退出, result-${i}.txt 永远不会被 acs_run_node.sh 主动写
    # 所以直接 poll node-0.log 中的 ADKG time
    local TIMEOUT=1800 ELAPSED=0 DONE=0
    while [ $ELAPSED -lt $TIMEOUT ]; do
        sleep 10
        ELAPSED=$((ELAPSED + 10))
        local c=$(sshc "${IPS[0]}" "grep -c 'ADKG time' /root/acs/benchmark-logs/node-0.log 2>/dev/null")
        if [ "$c" -ge 1 ] 2>/dev/null; then
            DONE=1
            sleep 6
            break
        fi
    done
    if [ $DONE -eq 0 ]; then
        echo "  !! B=$B 超时 (${TIMEOUT}s)"
    fi

    local times=()
    for i in 0 1 2 3; do
        local T=$(sshc "${IPS[$i]}" "grep 'ADKG time' /root/acs/benchmark-logs/node-${i}.log 2>/dev/null | grep -oP 'ADKG time:\s+\K[0-9.]+' | tail -1")
        [ -z "$T" ] && T="NA"
        times[$i]=$T
        echo "  replica $((i+1)): ${T}s"
    done
    echo "$B,${times[0]},${times[1]},${times[2]},${times[3]}" >> "$SUMMARY"

    for i in 0 1 2 3; do
        sshc "${IPS[$i]}" "pkill -9 -f vaba_run 2>/dev/null" &
    done
    wait
    echo "=== B=$B 完成 ==="
    sleep 3
}

echo "上传最新 acs_run_node.sh 到 4 节点..."
upload_runner
echo "上传完成"

for B in "${B_VALUES[@]}"; do
    run_one "$B"
done

echo ""
echo "========== 全部完成 =========="
cat "$SUMMARY"

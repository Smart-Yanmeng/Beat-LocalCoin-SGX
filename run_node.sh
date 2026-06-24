#!/bin/bash
# 用法: bash run_node.sh <node_id> <B值> [start_time]
# 例如: bash run_node.sh 0 250
# 不传 start_time 时会自动对齐到下一个整 30 秒边界 + 30 秒
# 只要 4 台机器启动间隔小于 30 秒，会自动算出同一个 START_TIME

NODE_ID=$1
B=$2

# 自动计算 START_TIME：对齐到下一个整 30 秒边界 + 30 秒
# 原理：NTP 同步的 4 台机器在 30 秒窗口内启动，会算出同样的值
NOW=$(date +%s)
AUTO_START=$(( (NOW / 30 + 2) * 30 ))
START_TIME=${3:-$AUTO_START}

if [ -z "$NODE_ID" ] || [ -z "$B" ]; then
    echo "用法: bash run_node.sh <node_id> <B值> [start_time]"
    echo "例如: bash run_node.sh 0 250"
    exit 1
fi

N=4
T=1
PORT=7001
IPS=("8.160.188.185" "8.160.188.178" "8.160.180.163" "8.160.187.104")
RESULT_FILE="/root/acs/results.csv"

# 初始化结果文件（如果不存在则创建表头）
if [ ! -f "$RESULT_FILE" ]; then
    echo "N,B,replica,ADKG_time,ACSS_time,RBC1_time,RBC2_time,Eval_time" > "$RESULT_FILE"
fi

# 生成配置
CONFIG_FILE="/root/acs/conf/adkg_4_remote/config-${NODE_ID}.json"
cat > "$CONFIG_FILE" << EOF
{"N":$N,"t":$T,"k":$B,"my_id":$NODE_ID,"peers":["${IPS[0]}:$PORT","${IPS[1]}:$PORT","${IPS[2]}:$PORT","${IPS[3]}:$PORT"]}
EOF

echo "=== Node $NODE_ID, B=$B, START_TIME=$START_TIME ==="
echo "Config: $CONFIG_FILE"
cat "$CONFIG_FILE"
echo ""

# 杀掉旧进程
pkill -f vaba_run 2>/dev/null
sleep 1

# 清理旧日志
rm -f /root/acs/benchmark-logs/node-*.log

# 运行
cd /root/acs
echo "启动中... 等待到 $START_TIME 开始执行 (当前: $(date +%s))"
python3 -m scripts.vaba_run -d -f "$CONFIG_FILE" -time "$START_TIME" 2>&1 | tee benchmark-logs/node-${NODE_ID}.log

# 提取结果写入 CSV
ADKG_LINE=$(grep "ADKG time" benchmark-logs/node-${NODE_ID}.log)
if [ -n "$ADKG_LINE" ]; then
    ADKG_TIME=$(echo "$ADKG_LINE" | grep -oP 'ADKG time:\s+\K[0-9.]+')
    ACSS_TIME=$(echo "$ADKG_LINE" | grep -oP 'ACSS time:\s+\K[0-9.]+')
    RBC1_TIME=$(echo "$ADKG_LINE" | grep -oP 'RBC1 time:\s+\K[0-9.]+')
    RBC2_TIME=$(echo "$ADKG_LINE" | grep -oP 'RBC2 time:\s+\K[0-9.]+')
    EVAL_TIME=$(echo "$ADKG_LINE" | grep -oP 'Eval time:\s+\K[0-9.]+')
    echo "$N,$B,$NODE_ID,$ADKG_TIME,$ACSS_TIME,$RBC1_TIME,$RBC2_TIME,$EVAL_TIME" >> "$RESULT_FILE"
    echo ""
    echo "=== 结果已写入 $RESULT_FILE ==="
    echo "N=$N, B=$B, replica=$NODE_ID, ADKG_time=$ADKG_TIME"
else
    echo ""
    echo "=== 未检测到 ADKG time，实验可能失败 ==="
fi

echo "=== 完成 ==="

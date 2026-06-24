#!/bin/bash
#
# Beat-LocalCoin (non-SGX) 分布式节点启动脚本
#
# 用法: ./start_node.sh <节点ID> [batch大小]
# 示例:
#   服务器0 (8.160.188.185): ./start_node.sh 0 100
#   服务器1 (8.160.188.178): ./start_node.sh 1 100
#   服务器2 (8.160.180.163): ./start_node.sh 2 100
#   服务器3 (8.160.187.104): ./start_node.sh 3 100
#
# 跑完后结果自动写入 results.csv
# 格式: N,B,replica,time

set -e

if [ -z "$1" ]; then
    echo "用法: ./start_node.sh <节点ID> [batch大小]"
    echo ""
    echo "  节点ID:    0-3 (对应4台服务器)"
    echo "  batch大小: 默认100"
    exit 1
fi

NODE_ID=$1
B=${2:-100}
N=4
T=1
V=1

# Number of transactions in the pool. Match B so the protocol completes in 1 round.
TX=$B

export LD_LIBRARY_PATH=/usr/local/lib:${LD_LIBRARY_PATH:-}
export LIBRARY_PATH=/usr/local/lib:${LIBRARY_PATH:-}

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

CSV_FILE="${SCRIPT_DIR}/results.csv"
LOG_FILE="${SCRIPT_DIR}/beat-node-${NODE_ID}.log"

echo "╔══════════════════════════════════════════════════════╗"
echo "║  Beat-LocalCoin (Non-SGX) 节点启动                  ║"
echo "╠══════════════════════════════════════════════════════╣"
echo "║  节点ID:   $NODE_ID"
echo "║  N=$N, t=$T, B=$B, version=$V"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

echo "[$(date '+%H:%M:%S')] 启动节点 $NODE_ID ..."
echo "  请确保 4 台服务器在同一时间内启动此脚本"
echo ""

START_TIME=$(date +%s.%N)

# 跑测试，输出到日志文件
python3 -u -m adaptive.test.honest_party_test_EC2 \
    -k thsig4_1.keys \
    -e ecdsa.keys \
    -c thenc4_1.keys \
    -s hosts \
    -n $N \
    -t $T \
    -b $B \
    -x $TX \
    -v $V \
    -i $NODE_ID \
    2>&1 | tee "$LOG_FILE" || true

END_TIME=$(date +%s.%N)

echo ""
echo "[$(date '+%H:%M:%S')] 节点 $NODE_ID 已结束"

# 解析 [Finishing Time X], Y 这一行获取 time
TIME=$(grep -oP "\[Finishing Time $NODE_ID\],\s+\K[0-9.]+" "$LOG_FILE" | head -1)

if [ -z "$TIME" ]; then
    # Fallback: use wall-clock duration
    TIME=$(echo "$END_TIME - $START_TIME" | bc -l 2>/dev/null || echo "")
    echo "⚠ 未找到 [Finishing Time], 使用墙钟时间: ${TIME}s"
fi

if [ -n "$TIME" ]; then
    if [ ! -f "$CSV_FILE" ]; then
        echo "N,B,replica,time" > "$CSV_FILE"
    fi
    echo "$N,$B,$NODE_ID,$TIME" >> "$CSV_FILE"
    echo ""
    echo ">>> 结果已写入 $CSV_FILE"
    echo "    N=$N, B=$B, replica=$NODE_ID, time=${TIME}s"
fi

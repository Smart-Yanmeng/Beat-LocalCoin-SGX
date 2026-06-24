#!/bin/bash
#
# Dumbo BFT 单节点启动脚本
# 在每台服务器上手动执行此脚本启动对应节点
#
# 使用方法:
#   ./start_node.sh <节点ID> [协议] [batch大小] [轮数]
#
# 示例 (在4台服务器上分别执行):
#   服务器0 (8.160.188.185):  ./start_node.sh 0 dumbo 1000 10
#   服务器1 (8.160.188.178):  ./start_node.sh 1 dumbo 1000 10
#   服务器2 (8.160.180.163):  ./start_node.sh 2 dumbo 1000 10
#   服务器3 (8.160.187.104):  ./start_node.sh 3 dumbo 1000 10
#
# 跑完后结果自动写入 results.csv
#

set -e

# ============================================================
# 参数解析
# ============================================================
if [ -z "$1" ]; then
    echo "用法: ./start_node.sh <节点ID> [协议] [batch大小] [轮数]"
    echo ""
    echo "  节点ID:    0-3 (对应4台服务器)"
    echo "  协议:      dumbo(默认), bdt, rbc-bdt"
    echo "  batch大小: 默认1000"
    echo "  轮数:      默认10"
    echo ""
    echo "示例:"
    echo "  ./start_node.sh 0 dumbo 1000 10"
    exit 1
fi

NODE_ID=$1
PROTOCOL=${2:-dumbo}
B=${3:-1000}
K=${4:-10}

# 固定参数
N=7
F=2
S=50
T=1
FALLBACK_B=1000000
SID="sidA"

# ============================================================
# 环境设置
# ============================================================
export LIBRARY_PATH=/usr/local/lib:${LIBRARY_PATH:-}
export LD_LIBRARY_PATH=/usr/local/lib:${LD_LIBRARY_PATH:-}

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

CSV_FILE="${SCRIPT_DIR}/results.csv"

# ============================================================
# 启动节点
# ============================================================
echo "╔══════════════════════════════════════════════════════╗"
echo "║  Dumbo BFT 节点启动                                 ║"
echo "╠══════════════════════════════════════════════════════╣"
echo "║  节点ID:   $NODE_ID"
echo "║  协议:     $PROTOCOL"
echo "║  N=$N, f=$F, B=$B, K=$K"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# 清理旧日志
rm -f log/consensus-node-${NODE_ID}.log
rm -f log/node-net-client-${NODE_ID}.log
rm -f log/node-net-server-${NODE_ID}.log
mkdir -p log

echo "[$(date '+%H:%M:%S')] 启动节点 $NODE_ID ..."
echo "  等待其他节点连接中 (请确保4台服务器都已启动此脚本)"
echo "  按 Ctrl+C 停止"
echo ""

python3 run_socket_node.py \
    --sid "$SID" \
    --id $NODE_ID \
    --N $N \
    --f $F \
    --B $B \
    --K $K \
    --S $S \
    --T $T \
    --P "$PROTOCOL" \
    --F $FALLBACK_B

echo ""
echo "[$(date '+%H:%M:%S')] 节点 $NODE_ID 已结束"
echo "日志文件: log/consensus-node-${NODE_ID}.log"

# ============================================================
# 解析日志, 写入 CSV
# ============================================================
LOG_FILE="log/consensus-node-${NODE_ID}.log"

if [ -f "$LOG_FILE" ]; then
    # 提取总时间: "node X breaks in Y seconds with total delivered Txs Z"
    TIME=$(grep "breaks in" "$LOG_FILE" | grep -oP 'breaks in \K[0-9.]+')

    if [ -n "$TIME" ]; then
        # 如果 CSV 不存在, 先写表头
        if [ ! -f "$CSV_FILE" ]; then
            echo "N,B,replica,time" > "$CSV_FILE"
        fi

        # 追加本次结果
        echo "$N,$B,$NODE_ID,$TIME" >> "$CSV_FILE"

        echo ""
        echo ">>> 结果已写入 $CSV_FILE"
        echo "    N=$N, B=$B, replica=$NODE_ID, time=${TIME}s"
    else
        echo "⚠ 日志中未找到完成记录, 未写入CSV"
    fi
fi

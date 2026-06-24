#!/bin/bash
# ACS (VABA) 单节点启动脚本 - 新集群
# 用法: bash acs_run_node.sh <node_id> <B值> [start_time]
#
# 关键设计:
#   1. python 进程的 stdout 用 awk 实时过滤掉噪音并写入 LOG (line-buffered)
#   2. 一旦 LOG 出现 "ADKG time" 行, 立即 kill python 进程, 防止它继续刷垃圾日志
#      把磁盘填满 (实测 vaba 共识完成后会无限刷 "Queue ... bound to a different event loop")
#
# 退出后 LOG 仍保留, 编排器从 LOG 读 "ADKG time"

NODE_ID=$1
B=$2

NOW=$(date +%s)
AUTO_START=$(( (NOW / 30 + 2) * 30 ))
START_TIME=${3:-$AUTO_START}

if [ -z "$NODE_ID" ] || [ -z "$B" ]; then
    echo "用法: bash acs_run_node.sh <node_id> <B值> [start_time]"
    exit 1
fi

N=4
T=1
PORT=7001
IPS=("120.27.215.50" "116.62.149.8" "47.98.121.97" "116.62.240.167")
RESULT_FILE="/root/acs/results.csv"

export LIBRARY_PATH=/usr/local/lib:${LIBRARY_PATH:-}
export LD_LIBRARY_PATH=/usr/local/lib:${LD_LIBRARY_PATH:-}
export LIBRARY_INCLUDE_PATH=/usr/local/include
export PYTHONUNBUFFERED=1

if [ ! -f "$RESULT_FILE" ]; then
    echo "N,B,replica,ADKG_time,ACSS_time,RBC1_time,RBC2_time,Eval_time" > "$RESULT_FILE"
fi

mkdir -p /root/acs/conf/adkg_4_remote
CONFIG_FILE="/root/acs/conf/adkg_4_remote/config-${NODE_ID}.json"
cat > "$CONFIG_FILE" << EOF
{"N":$N,"t":$T,"k":$B,"my_id":$NODE_ID,"peers":["${IPS[0]}:$PORT","${IPS[1]}:$PORT","${IPS[2]}:$PORT","${IPS[3]}:$PORT"]}
EOF

mkdir -p /root/acs/benchmark-logs
LOG="/root/acs/benchmark-logs/node-${NODE_ID}.log"
RESULT_TXT="/root/acs/benchmark-logs/result-${NODE_ID}.txt"
rm -f "$LOG" "$RESULT_TXT"
touch "$LOG" "$RESULT_TXT"

# 清掉旧的 vaba_run
pkill -9 -f vaba_run 2>/dev/null
sleep 1

echo "=== Node $NODE_ID, B=$B, START_TIME=$START_TIME ==="
echo "启动中... 等待到 $START_TIME 开始 (当前: $(date +%s))"
cd /root/acs

# 后台启动 python, stdout/stderr 通过 awk 过滤
# awk 过滤掉指定噪音, 看到 ADKG time 就 kill 整个进程组
(
    python3 -u -m scripts.vaba_run -d -f "$CONFIG_FILE" -time "$START_TIME" 2>&1 | \
    awk -v logfile="$LOG" -v resfile="$RESULT_TXT" '
        BEGIN {
            noise = "(bound to a different event loop|Event loop is closed|Task was destroyed|task: <Task|wait_for=|coro=<Queue|^Traceback|^Exception ignored|^  File |^    [a-z]|^RuntimeError|^[ \t]*$)"
        }
        $0 !~ noise {
            print $0 >> logfile
            fflush(logfile)
            if ($0 ~ /ADKG time/) {
                print $0 > resfile
                fflush(resfile)
                system("sleep 0.2; pkill -9 -f vaba_run")
                exit
            }
        }
    '
) &

WORKER=$!

# 等待 awk 退出 (它在看到 ADKG time 后 kill python 然后 exit)
# 设置超时, 避免无限阻塞
TIMEOUT=$((START_TIME + 600 - $(date +%s)))   # 启动后最多再等 600s
[ $TIMEOUT -lt 60 ] && TIMEOUT=60

for ((i=0; i<TIMEOUT; i++)); do
    sleep 1
    if ! kill -0 "$WORKER" 2>/dev/null; then
        break
    fi
done

# 兜底: 强制 kill
pkill -9 -f vaba_run 2>/dev/null
kill -9 "$WORKER" 2>/dev/null

# 写结果 csv
ADKG_LINE=$(cat "$RESULT_TXT" 2>/dev/null)
if [ -n "$ADKG_LINE" ]; then
    ADKG_TIME=$(echo "$ADKG_LINE" | grep -oP 'ADKG time:\s+\K[0-9.]+')
    ACSS_TIME=$(echo "$ADKG_LINE" | grep -oP 'ACSS time:\s+\K[0-9.]+')
    RBC1_TIME=$(echo "$ADKG_LINE" | grep -oP 'RBC1 time:\s+\K[0-9.]+')
    RBC2_TIME=$(echo "$ADKG_LINE" | grep -oP 'RBC2 time:\s+\K[0-9.]+')
    EVAL_TIME=$(echo "$ADKG_LINE" | grep -oP 'Eval time:\s+\K[0-9.]+')
    echo "$N,$B,$NODE_ID,$ADKG_TIME,$ACSS_TIME,$RBC1_TIME,$RBC2_TIME,$EVAL_TIME" >> "$RESULT_FILE"
    echo "=== 结果: N=$N B=$B replica=$NODE_ID ADKG=$ADKG_TIME ==="
else
    echo "=== 未检测到 ADKG time, 实验失败 ==="
fi

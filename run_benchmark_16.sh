#!/bin/bash
# 16台远程服务器实验启动脚本
# 用法: bash run_benchmark_16.sh <B值>
# 例如: bash run_benchmark_16.sh 250

B=$1
SSH_OPTS="-o StrictHostKeyChecking=no -o ConnectTimeout=10"
PASS="York@233"
PORT=7001

# 16台服务器IP
SERVERS=(
    "120.27.215.50"
    "116.62.149.8"
    "47.98.121.97"
    "116.62.240.167"
    "121.43.234.253"
    "121.199.72.252"
    "121.40.130.83"
    "121.40.94.52"
    "120.26.46.218"
    "120.55.86.74"
    "121.40.255.201"
    "121.43.148.183"
    "121.40.158.250"
    "121.40.117.123"
    "121.40.88.101"
    "121.40.118.7"
)

N=16
T=4

if [ -z "$B" ]; then
    echo "用法: bash run_benchmark_16.sh <B值>"
    exit 1
fi

# 生成peers列表
PEERS=""
for i in "${!SERVERS[@]}"; do
    if [ $i -gt 0 ]; then
        PEERS="$PEERS,"
    fi
    PEERS="$PEERS\"${SERVERS[$i]}:$PORT\""
done

# 统一启动时间
START_TIME=$(sshpass -p "$PASS" ssh $SSH_OPTS root@${SERVERS[0]} "python3 -c \"import time; now=int(time.time()); print((now//30+2)*30)\"" 2>/dev/null)
echo "=== 16节点实验: B=$B, START_TIME=$START_TIME ==="
echo ""

# 启动16个节点
for i in "${!SERVERS[@]}"; do
    (
        echo "-- 启动节点 $i (${SERVERS[$i]}) --"
        sshpass -p "$PASS" ssh $SSH_OPTS root@${SERVERS[$i]} "
            cd /root/acs
            mkdir -p conf/adkg_16_remote benchmark-logs
            cat > conf/adkg_16_remote/config-$i.json << EOF
{\"N\":$N,\"t\":$T,\"k\":$B,\"my_id\":$i,\"peers\":[$PEERS]}
EOF
            pkill -9 -f vaba_run 2>/dev/null
            sleep 1
            export LIBRARY_PATH=/usr/local/lib:\${LIBRARY_PATH:-}
            export LD_LIBRARY_PATH=/usr/local/lib:\${LD_LIBRARY_PATH:-}
            export PYTHONUNBUFFERED=1
            nohup python3 -u -m scripts.vaba_run -d -f conf/adkg_16_remote/config-$i.json -time $START_TIME > benchmark-logs/node-$i.log 2>&1 &
        " 2>/dev/null
        echo "-- 节点 $i 已启动 --"
    ) &
done

wait
echo ""
echo "所有节点已启动，等待完成..."

# 等待所有节点完成
DONE=()
for i in "${!SERVERS[@]}"; do
    DONE[$i]=0
done

for ((t=0; t<600; t++)); do
    ALL_DONE=true
    for i in "${!SERVERS[@]}"; do
        if [ "${DONE[$i]}" = "0" ]; then
            HAS_LINE=$(sshpass -p "$PASS" ssh $SSH_OPTS root@${SERVERS[$i]} "grep -c 'ADKG time' /root/acs/benchmark-logs/node-$i.log 2>/dev/null" 2>/dev/null)
            if [ "$HAS_LINE" = "1" ]; then
                DONE[$i]=1
                echo "节点 $i 完成!"
            else
                ALL_DONE=false
            fi
        fi
    done
    if $ALL_DONE; then
        break
    fi
    sleep 2
done

# 收集结果
echo ""
echo "=== 收集结果 ==="
for i in "${!SERVERS[@]}"; do
    LOG=$(sshpass -p "$PASS" ssh $SSH_OPTS root@${SERVERS[$i]} "grep 'ADKG time' /root/acs/benchmark-logs/node-$i.log 2>/dev/null | tail -1" 2>/dev/null)
    if [ -n "$LOG" ]; then
        T=$(echo "$LOG" | grep -oP 'ADKG time:\s+\K[0-9.]+')
        echo "节点 $i: ${T}s"
    else
        echo "节点 $i: FAILED"
    fi
done

# 清理
echo ""
echo "清理进程..."
for i in "${!SERVERS[@]}"; do
    sshpass -p "$PASS" ssh $SSH_OPTS root@${SERVERS[$i]} "pkill -9 -f vaba_run 2>/dev/null" 2>/dev/null &
done
wait
echo "=== 完成 ==="

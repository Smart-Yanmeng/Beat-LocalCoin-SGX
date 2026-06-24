#!/bin/bash
# 逐个B值跑实验，每个B值独立执行
# 用法: bash run_benchmark.sh <B值>

B=$1
SSH_OPTS="-o StrictHostKeyChecking=no -o ConnectTimeout=10"
PASS="York@233"
SERVERS=("120.27.215.50" "116.62.149.8" "47.98.121.97" "116.62.240.167")

if [ -z "$B" ]; then
    echo "用法: bash run_benchmark.sh <B值>"
    exit 1
fi

# 统一启动时间
START_TIME=$(sshpass -p "$PASS" ssh $SSH_OPTS root@${SERVERS[0]} "python3 -c \"import time; now=int(time.time()); print((now//30+2)*30)\"" 2>/dev/null)
echo "B=$B, START_TIME=$START_TIME"

# 启动4个节点
for i in 0 1 2 3; do
    sshpass -p "$PASS" ssh $SSH_OPTS root@${SERVERS[$i]} "
        cd /root/acs
        mkdir -p conf/adkg_4_remote benchmark-logs
        cat > conf/adkg_4_remote/config-$i.json << EOF
{\"N\":4,\"t\":1,\"k\":$B,\"my_id\":$i,\"peers\":[\"120.27.215.50:7001\",\"116.62.149.8:7001\",\"47.98.121.97:7001\",\"116.62.240.167:7001\"]}
EOF
        pkill -9 -f vaba_run 2>/dev/null
        sleep 1
        export LIBRARY_PATH=/usr/local/lib:\${LIBRARY_PATH:-}
        export LD_LIBRARY_PATH=/usr/local/lib:\${LD_LIBRARY_PATH:-}
        export PYTHONUNBUFFERED=1
        nohup python3 -u -m scripts.vaba_run -d -f conf/adkg_4_remote/config-$i.json -time $START_TIME > benchmark-logs/node-$i.log 2>&1 &
    " 2>/dev/null &
done

echo "Nodes started, waiting for completion..."

# 等待所有节点完成
DONE=(0 0 0 0)
for ((t=0; t<600; t++)); do
    ALL_DONE=true
    for i in 0 1 2 3; do
        if [ "${DONE[$i]}" = "0" ]; then
            HAS_LINE=$(sshpass -p "$PASS" ssh $SSH_OPTS root@${SERVERS[$i]} "grep -c 'ADKG time' /root/acs/benchmark-logs/node-$i.log 2>/dev/null" 2>/dev/null)
            if [ "$HAS_LINE" = "1" ]; then
                DONE[$i]=1
                echo "Node $i done!"
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
echo "Collecting results..."
for i in 0 1 2 3; do
    LOG=$(sshpass -p "$PASS" ssh $SSH_OPTS root@${SERVERS[$i]} "grep 'ADKG time' /root/acs/benchmark-logs/node-$i.log 2>/dev/null | tail -1" 2>/dev/null)
    if [ -n "$LOG" ]; then
        T=$(echo "$LOG" | grep -oP 'ADKG time:\s+\K[0-9.]+')
        echo "Node $i: ${T}s"
    else
        echo "Node $i: FAILED"
    fi
done

# 清理
for i in 0 1 2 3; do
    sshpass -p "$PASS" ssh $SSH_OPTS root@${SERVERS[$i]} "pkill -9 -f vaba_run 2>/dev/null" 2>/dev/null &
done
wait

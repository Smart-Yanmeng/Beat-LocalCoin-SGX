#!/bin/bash
# 直接运行python命令，不依赖acs_run_node.sh的超时机制
# 用法: bash run_all_b.sh

SSH_OPTS="-o StrictHostKeyChecking=no -o ConnectTimeout=10"
PASS="York@233"
SERVERS=("120.27.215.50" "116.62.149.8" "47.98.121.97" "116.62.240.167")
B_VALUES=(10 100 250 500 750 1000 2500 5000 7500 10000 25000 50000 75000 100000)
OUTPUT="/home/charlotte/MyWorkSpace/PROJECT/acs/benchmark_results.csv"

# 先杀掉所有旧进程
for i in 0 1 2 3; do
    sshpass -p "$PASS" ssh $SSH_OPTS root@${SERVERS[$i]} "pkill -9 -f vaba_run 2>/dev/null" 2>/dev/null &
done
wait

echo "B,time0,time1,time2,time3" > "$OUTPUT"

for B in "${B_VALUES[@]}"; do
    echo "=== Testing B=$B ==="

    # 计算统一启动时间（30秒后，对齐到30秒边界）
    START_TIME=$(sshpass -p "$PASS" ssh $SSH_OPTS root@${SERVERS[0]} "python3 -c \"import time; now=int(time.time()); print((now//30+2)*30)\"" 2>/dev/null)
    echo "Start time: $START_TIME"

    # 在4台服务器上同时生成配置文件并启动python
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
            python3 -u -m scripts.vaba_run -d -f conf/adkg_4_remote/config-$i.json -time $START_TIME > benchmark-logs/node-$i.log 2>&1 &
        " &
    done

    # 等待所有节点完成（检查日志中是否出现ADKG time）
    echo "Waiting for all nodes to complete..."
    DONE=(0 0 0 0)
    for ((t=0; t<600; t++)); do
        ALL_DONE=true
        for i in 0 1 2 3; do
            if [ "${DONE[$i]}" = "0" ]; then
                HAS_LINE=$(sshpass -p "$PASS" ssh $SSH_OPTS root@${SERVERS[$i]} "grep -c 'ADKG time' /root/acs/benchmark-logs/node-$i.log 2>/dev/null" 2>/dev/null)
                if [ "$HAS_LINE" = "1" ]; then
                    DONE[$i]=1
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
    TIMES=()
    for i in 0 1 2 3; do
        LOG=$(sshpass -p "$PASS" ssh $SSH_OPTS root@${SERVERS[$i]} "grep 'ADKG time' /root/acs/benchmark-logs/node-$i.log 2>/dev/null | tail -1" 2>/dev/null)
        if [ -n "$LOG" ]; then
            T=$(echo "$LOG" | grep -oP 'ADKG time:\s+\K[0-9.]+')
            TIMES+=("$T")
        else
            TIMES+=("FAILED")
        fi
    done

    echo "$B,${TIMES[0]},${TIMES[1]},${TIMES[2]},${TIMES[3]}" >> "$OUTPUT"
    echo "B=$B done: ${TIMES[0]}, ${TIMES[1]}, ${TIMES[2]}, ${TIMES[3]}"

    # 清理
    for i in 0 1 2 3; do
        sshpass -p "$PASS" ssh $SSH_OPTS root@${SERVERS[$i]} "pkill -9 -f vaba_run 2>/dev/null" 2>/dev/null &
    done
    wait
done

echo "=== All done! Results saved to $OUTPUT ==="
cat "$OUTPUT"

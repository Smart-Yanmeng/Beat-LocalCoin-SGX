#!/bin/bash
# 快速批量实验脚本
PASS="York@233"
SSH_OPTS="-o StrictHostKeyChecking=no -o ConnectTimeout=3"
CSV="/home/charlotte/MyWorkSpace/PROJECT/acs/results.csv"

IPS=("120.27.215.50" "116.62.149.8" "47.98.121.97" "116.62.240.167" "121.43.234.253" "121.199.72.252" "121.40.130.83" "121.40.94.52" "120.26.46.218" "120.55.86.74" "121.40.255.201" "121.43.148.183" "121.40.158.250" "121.40.117.123" "121.40.88.101" "121.40.118.7")

KS=(750 1000 2500 5000 7500 10000 25000 50000 75000 100000)

for B in "${KS[@]}"; do
    echo "=== K=$B ==="
    
    # 启动
    START_TIME=$(python3 -c "import time; now=int(time.time()); print((now//30+2)*30)")
    for i in "${!IPS[@]}"; do
        sshpass -p "$PASS" ssh $SSH_OPTS root@${IPS[$i]} "screen -dmS exp bash /root/acs/run_exp.sh $B $i $START_TIME" 2>/dev/null &
    done
    wait
    
    # 等待启动时间+实验完成
    WAIT=$((START_TIME - $(date +%s) + 5))
    [ $WAIT -gt 0 ] && sleep $WAIT
    
    # 等待完成（只检查第一个节点，节省时间）
    MAX_WAIT=60
    [ $B -ge 10000 ] && MAX_WAIT=300
    for ((t=0; t<MAX_WAIT; t+=10)); do
        sleep 10
        DONE=$(sshpass -p "$PASS" ssh $SSH_OPTS root@${IPS[0]} "grep -c 'ADKG time' /root/acs/benchmark-logs/node-0.log 2>/dev/null || echo 0" 2>/dev/null)
        [ "$DONE" -ge "1" ] && break
        echo "  等待${t}秒..."
    done
    
    # 收集结果
    for i in "${!IPS[@]}"; do
        ip=${IPS[$i]}
        LOG=$(sshpass -p "$PASS" ssh $SSH_OPTS root@$ip "grep 'ADKG time' /root/acs/benchmark-logs/node-$i.log 2>/dev/null | tail -1" 2>/dev/null)
        if [ -n "$LOG" ]; then
            ADKG=$(echo "$LOG" | grep -oP 'ADKG time:\s+\K[0-9.]+')
            ACSS=$(echo "$LOG" | grep -oP 'ACSS time:\s+\K[0-9.]+')
            RBC1=$(echo "$LOG" | grep -oP 'RBC1 time:\s+\K[0-9.]+')
            RBC2=$(echo "$LOG" | grep -oP 'RBC2 time:\s+\K[0-9.]+')
            EVAL=$(echo "$LOG" | grep -oP 'Eval time:\s+\K[0-9.]+')
            echo "16,4,$B,$i,$ip,$ADKG,$ACSS,$RBC1,$RBC2,$EVAL" >> "$CSV"
        fi
    done
    echo "K=$B 完成"
done

echo "=== 全部完成 ==="
awk -F',' 'NR>1 {print $3}' "$CSV" | sort -n | uniq -c

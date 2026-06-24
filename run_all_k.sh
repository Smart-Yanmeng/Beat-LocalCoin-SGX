#!/bin/bash
# 批量运行多个K值实验
PASS="York@233"
SSH_OPTS="-o StrictHostKeyChecking=no -o ConnectTimeout=5"
PORT=7001
N=16
T=4
CSV="/home/charlotte/MyWorkSpace/PROJECT/acs/results.csv"

IPS=("120.27.215.50" "116.62.149.8" "47.98.121.97" "116.62.240.167" "121.43.234.253" "121.199.72.252" "121.40.130.83" "121.40.94.52" "120.26.46.218" "120.55.86.74" "121.40.255.201" "121.43.148.183" "121.40.158.250" "121.40.117.123" "121.40.88.101" "121.40.118.7")

# 清理CSV
echo "N,t,K,节点ID,IP地址,ADKG时间(s),ACSS时间(s),RBC1时间(s),RBC2时间(s),Eval时间(s)" > "$CSV"

# 部署启动脚本到所有服务器
echo "部署启动脚本..."
for i in "${!IPS[@]}"; do
    IP=${IPS[$i]}
    sshpass -p "$PASS" scp $SSH_OPTS /home/charlotte/MyWorkSpace/PROJECT/acs/run_exp.sh root@$IP:/root/acs/run_exp.sh 2>/dev/null &
done
wait
echo "启动脚本已部署"

KS=(10 100 250 500 750 1000 2500 5000 7500 10000 25000 50000 75000 100000)

for B in "${KS[@]}"; do
    echo "=============================="
    echo "运行 K=$B"
    echo "=============================="
    
    # 获取启动时间
    START_TIME=$(python3 -c "import time; now=int(time.time()); print((now//30+2)*30)")
    WAIT=$((START_TIME - $(date +%s)))
    echo "START_TIME=$START_TIME (等待${WAIT}秒)"
    
    # 使用screen启动所有节点
    for i in "${!IPS[@]}"; do
        IP=${IPS[$i]}
        sshpass -p "$PASS" ssh $SSH_OPTS root@$IP "
            screen -dmS exp bash /root/acs/run_exp.sh $B $i $START_TIME
        " 2>/dev/null &
    done
    wait
    
    # 等待启动时间
    echo "等待${WAIT}秒..."
    sleep $WAIT
    echo "实验开始执行..."
    
    # 轮询结果
    MAX_WAIT=120
    [ $B -ge 10000 ] && MAX_WAIT=600
    
    for ((t=0; t<MAX_WAIT; t+=5)); do
        sleep 5
        DONE=0
        for i in "${!IPS[@]}"; do
            HAS=$(sshpass -p "$PASS" ssh $SSH_OPTS root@${IPS[$i]} "grep -c 'ADKG time' /root/acs/benchmark-logs/node-$i.log 2>/dev/null || echo 0" 2>/dev/null)
            [ "$HAS" -ge "1" ] 2>/dev/null && DONE=$((DONE+1))
        done
        echo "  ${t}秒: $DONE/$N 完成"
        [ "$DONE" -ge "14" ] && break
    done
    
    # 收集结果
    echo "收集结果..."
    for i in "${!IPS[@]}"; do
        ip=${IPS[$i]}
        LOG=$(sshpass -p "$PASS" ssh $SSH_OPTS root@$ip "grep 'ADKG time' /root/acs/benchmark-logs/node-$i.log 2>/dev/null | tail -1" 2>/dev/null)
        if [ -n "$LOG" ]; then
            ADKG=$(echo "$LOG" | grep -oP 'ADKG time:\s+\K[0-9.]+')
            ACSS=$(echo "$LOG" | grep -oP 'ACSS time:\s+\K[0-9.]+')
            RBC1=$(echo "$LOG" | grep -oP 'RBC1 time:\s+\K[0-9.]+')
            RBC2=$(echo "$LOG" | grep -oP 'RBC2 time:\s+\K[0-9.]+')
            EVAL=$(echo "$LOG" | grep -oP 'Eval time:\s+\K[0-9.]+')
            echo "$N,$T,$B,$i,$ip,$ADKG,$ACSS,$RBC1,$RBC2,$EVAL" >> "$CSV"
            printf "  节点%2d: ADKG=%.4fs\n" $i $ADKG
        fi
    done
    
    echo "K=$B 完成"
    echo ""
    sleep 3
done

echo ""
echo "=== 所有实验完成 ==="
echo "结果保存在: $CSV"

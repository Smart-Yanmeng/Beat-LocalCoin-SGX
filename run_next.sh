#!/bin/bash
# 用法: bash run_next.sh <B值>
B=$1
if [ -z "$B" ]; then echo "用法: bash run_next.sh <B>"; exit 1; fi

echo "=== B=$B ==="
sshpass -p 'York@233' ssh -o StrictHostKeyChecking=no root@120.27.215.50 'cd /root/acs && bash acs_run_node.sh 0 '$B &
sshpass -p 'York@233' ssh -o StrictHostKeyChecking=no root@116.62.149.8 'cd /root/acs && bash acs_run_node.sh 1 '$B &
sshpass -p 'York@233' ssh -o StrictHostKeyChecking=no root@47.98.121.97 'cd /root/acs && bash acs_run_node.sh 2 '$B &
sshpass -p 'York@233' ssh -o StrictHostKeyChecking=no root@116.62.240.167 'cd /root/acs && bash acs_run_node.sh 3 '$B &
wait
echo "Collecting..."
T0=$(sshpass -p 'York@233' ssh -o StrictHostKeyChecking=no root@120.27.215.50 "grep 'ADKG time' /root/acs/benchmark-logs/node-0.log | tail -1 | grep -oP 'ADKG time:\s+\K[0-9.]+'" 2>/dev/null)
T1=$(sshpass -p 'York@233' ssh -o StrictHostKeyChecking=no root@116.62.149.8 "grep 'ADKG time' /root/acs/benchmark-logs/node-1.log | tail -1 | grep -oP 'ADKG time:\s+\K[0-9.]+'" 2>/dev/null)
T2=$(sshpass -p 'York@233' ssh -o StrictHostKeyChecking=no root@47.98.121.97 "grep 'ADKG time' /root/acs/benchmark-logs/node-2.log | tail -1 | grep -oP 'ADKG time:\s+\K[0-9.]+'" 2>/dev/null)
T3=$(sshpass -p 'York@233' ssh -o StrictHostKeyChecking=no root@116.62.240.167 "grep 'ADKG time' /root/acs/benchmark-logs/node-3.log | tail -1 | grep -oP 'ADKG time:\s+\K[0-9.]+'" 2>/dev/null)
echo "$B,$T0,$T1,$T2,$T3" >> /home/charlotte/MyWorkSpace/PROJECT/acs/benchmark_results.csv
echo "B=$B: $T0,$T1,$T2,$T3"

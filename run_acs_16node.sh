#!/bin/bash
# ACS 16-node B sweep
PASS='York@233'
SSH="sshpass -p $PASS ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10"

ALL_IPS=("120.27.215.50" "116.62.149.8" "47.98.121.97" "116.62.240.167" "121.43.234.253" "121.199.72.252" "121.40.130.83" "121.40.94.52" "120.26.46.218" "120.55.86.74" "121.40.255.201" "121.43.148.183" "121.40.158.250" "121.40.117.123" "121.40.88.101" "121.40.118.7")
B_LIST=(10 100 250 500 750 1000 2500 5000 7500 10000 25000 50000 75000 100000)
RESULTS="/home/charlotte/MyWorkSpace/PROJECT/dumbo/acs_16node_results.csv"

echo "B,node0,node1,node2,node3,node4,node5,node6,node7,node8,node9,node10,node11,node12,node13,node14,node15" > "$RESULTS"

for B in "${B_LIST[@]}"; do
    echo "=== B=$B ==="

    # Kill all
    for ip in "${ALL_IPS[@]}"; do
      $SSH root@$ip "pkill -9 -f vaba_run 2>/dev/null; true" 2>/dev/null
    done
    sleep 2

    # Generate configs with Python (avoids sed corruption)
    for ip in "${ALL_IPS[@]}"; do
      $SSH root@$ip "python3 -c \"
import json
ips = ['120.27.215.50','116.62.149.8','47.98.121.97','116.62.240.167','121.43.234.253','121.199.72.252','121.40.130.83','121.40.94.52','120.26.46.218','120.55.86.74','121.40.255.201','121.43.148.183','121.40.158.250','121.40.117.123','121.40.88.101','121.40.118.7']
peers = [p+':7001' for p in ips]
for i in range(16):
    with open(f'/root/acs/conf/adkg_16_remote/config-{i}.json','w') as f:
        json.dump({'N':16,'t':5,'k':$B,'my_id':i,'peers':peers},f)
\" 2>/dev/null" 2>/dev/null
    done

    START=$(date -d "+10 seconds" +%s)

    # Launch all 16
    for i in $(seq 0 15); do
      ip=${ALL_IPS[$i]}
      $SSH -f root@$ip "cd /root/acs && export LD_LIBRARY_PATH=/usr/local/lib:\$LD_LIBRARY_PATH && export PYTHONUNBUFFERED=1 && nohup timeout 300 python3 -u -m scripts.vaba_run -d -f conf/adkg_16_remote/config-${i}.json -time $START > /tmp/acs_node${i}.log 2>&1 &"
    done

    # Wait for completion
    for t in $(seq 30 30 300); do
      done=0
      for i in $(seq 0 15); do
        ip=${ALL_IPS[$i]}
        r=$($SSH root@$ip "grep -c 'Total bytes sent out aa' /tmp/acs_node${i}.log 2>/dev/null || echo 0" 2>&1)
        if echo "$r" | grep -qE '^[0-9]+$' && [ "$r" -ge 1 ] 2>/dev/null; then
          done=$((done+1))
        fi
      done
      if [ "$done" -ge 16 ]; then
        break
      fi
      echo "  ${t}s: $done/16"
    done

    # Collect
    row="$B"
    for i in $(seq 0 15); do
      ip=${ALL_IPS[$i]}
      t=$($SSH root@$ip "python3 -c \"
import re
from datetime import datetime
lines = open('/tmp/acs_node${i}.log').readlines()
s = e = None
for l in lines:
    m = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),(\d+).*ADKG start time', l)
    if m:
        dt = datetime.strptime(m.group(1), '%Y-%m-%d %H:%M:%S')
        s = dt.timestamp() + int(m.group(2)) / 10**len(m.group(2))
    m = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),(\d+)', l)
    if m and 'Total bytes' in l:
        dt = datetime.strptime(m.group(1), '%Y-%m-%d %H:%M:%S')
        e = dt.timestamp() + int(m.group(2)) / 10**len(m.group(2))
print(f'{e-s:.4f}' if s and e else '')
\" 2>&1" 2>&1)
      row="$row,${t}"
    done
    echo "$row" >> "$RESULTS"
    echo "  $row"
done

echo "All done!"

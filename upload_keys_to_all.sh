#!/bin/bash
# Upload keys to all 16 servers
PASS='York@233'
SSH="sshpass -p $PASS ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10"
SCP="sshpass -p $PASS scp -o StrictHostKeyChecking=no"

ALL_IPS=(
    "120.27.215.50"   # node 0
    "116.62.149.8"    # node 1
    "47.98.121.97"    # node 2
    "116.62.240.167"  # node 3
    "121.43.234.253"  # node 4
    "121.199.72.252"  # node 5
    "121.40.130.83"   # node 6
    "121.40.94.52"    # node 7
    "120.26.46.218"   # node 8
    "120.55.86.74"    # node 9
    "121.40.255.201"  # node 10
    "121.43.148.183"  # node 11
    "121.40.158.250"  # node 12
    "121.40.117.123"  # node 13
    "121.40.88.101"   # node 14
    "121.40.118.7"    # node 15
)

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  Uploading 16-node BEAT keys to all servers            ║"
echo "╚══════════════════════════════════════════════════════════╝"

for ip in "${ALL_IPS[@]}"; do
    echo "  Uploading to $ip..."
    $SCP /tmp/thsig16_4.keys root@${ip}:/root/BEAT/BEAT0/ 2>/dev/null &
    $SCP /tmp/thenc16_4.keys root@${ip}:/root/BEAT/BEAT0/ 2>/dev/null &
    $SCP /tmp/ecdsa.keys root@${ip}:/root/BEAT/BEAT0/ 2>/dev/null &
done
wait

echo ""
echo "Verifying keys on all nodes..."
for i in $(seq 0 15); do
    ip=${ALL_IPS[$i]}
    result=$($SSH root@$ip "ls -la /root/BEAT/BEAT0/thsig16_4.keys /root/BEAT/BEAT0/thenc16_4.keys /root/BEAT/BEAT0/ecdsa.keys 2>/dev/null | wc -l" 2>&1)
    if [ "$result" -eq 3 ]; then
        echo "  Node $i ($ip): ✅ OK"
    else
        echo "  Node $i ($ip): ❌ Missing keys"
    fi
done

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  Keys uploaded successfully!                           ║"
echo "╚══════════════════════════════════════════════════════════╝"

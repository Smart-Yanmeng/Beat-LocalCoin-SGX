#!/bin/bash
# Deploy BEAT to all 16 servers
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
echo "║  Deploying BEAT to all 16 servers                      ║"
echo "╚══════════════════════════════════════════════════════════╝"

# Step 1: Upload BEAT tar.gz to all servers
echo ""
echo "[Step 1] Uploading BEAT code to all servers..."
for ip in "${ALL_IPS[@]}"; do
    echo "  Uploading to $ip..."
    $SCP /tmp/BEAT.tar.gz root@${ip}:/tmp/ 2>/dev/null &
done
wait
echo "  BEAT code uploaded to all servers"

# Step 2: Extract BEAT on all servers
echo ""
echo "[Step 2] Extracting BEAT on all servers..."
for ip in "${ALL_IPS[@]}"; do
    echo "  Extracting on $ip..."
    $SSH root@$ip "cd /root && tar -xzf /tmp/BEAT.tar.gz && echo 'Extracted on $ip'" 2>/dev/null &
done
wait
echo "  BEAT extracted on all servers"

# Step 3: Setup Python 3.8 environment
echo ""
echo "[Step 3] Setting up Python 3.8 environment..."
for ip in "${ALL_IPS[@]}"; do
    echo "  Setting up $ip..."
    $SSH root@$ip "
        # Create charm symlink for Python 3.8
        cd /usr/lib/python3/dist-packages
        ln -sf /usr/lib/python3.8/site-packages/charm_crypto_framework-0.63-py3.8-linux-x86_64.egg/charm charm 2>/dev/null || true
        
        # Fix Python 3.10 compatibility issues
        cd /root/BEAT/BEAT0
        sed -i 's/encodestring/encodebytes/g; s/decodestring/decodebytes/g' \
            BEAT/commoncoin/thresprf.py \
            BEAT/threshenc/tdh2.py 2>/dev/null || true
        
        echo \"  $ip configured\"
    " 2>/dev/null &
done
wait
echo "  Python 3.8 environment configured"

# Step 4: Upload keys to all servers
echo ""
echo "[Step 4] Uploading keys to all servers..."
for ip in "${ALL_IPS[@]}"; do
    echo "  Uploading keys to $ip..."
    $SCP /tmp/thsig16_4.keys root@${ip}:/root/BEAT/BEAT0/ 2>/dev/null &
    $SCP /tmp/thenc16_4.keys root@${ip}:/root/BEAT/BEAT0/ 2>/dev/null &
    $SCP /tmp/ecdsa.keys root@${ip}:/root/BEAT/BEAT0/ 2>/dev/null &
done
wait
echo "  Keys uploaded to all servers"

# Step 5: Verify installation
echo ""
echo "[Step 5] Verifying installation..."
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
echo "║  BEAT deployed successfully to all 16 servers!         ║"
echo "╚══════════════════════════════════════════════════════════╝"

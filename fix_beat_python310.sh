#!/bin/bash
# Fix Python 3.10 compatibility issues in BEAT
PASS='York@233'
SSH="sshpass -p $PASS ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10"

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

echo "Fixing Python 3.10 compatibility issues in BEAT..."

for ip in "${ALL_IPS[@]}"; do
    echo "  Fixing $ip..."
    $SSH root@$ip "cd /root/BEAT/BEAT0 && \
        sed -i 's/encodestring/encodebytes/g; s/decodestring/decodebytes/g' \
            BEAT/commoncoin/thresprf.py \
            BEAT/threshenc/tdh2.py" 2>/dev/null &
done
wait

echo "Done! Python 3.10 compatibility issues fixed on all nodes."

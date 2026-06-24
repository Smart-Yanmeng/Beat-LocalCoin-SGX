#!/bin/bash
# 在每个服务器上部署的启动脚本
# 用法: bash run_exp.sh <B值> <节点ID> <启动时间>

B=$1
NODE_ID=$2
START_TIME=$3

cd /root/acs
pkill -9 -f vaba_run 2>/dev/null
rm -f benchmark-logs/node-${NODE_ID}.log
mkdir -p conf/adkg_16_remote benchmark-logs

# 生成配置文件
cat > conf/adkg_16_remote/config-${NODE_ID}.json << EOF
{"N":16,"t":4,"k":${B},"my_id":${NODE_ID},"peers":["120.27.215.50:7001","116.62.149.8:7001","47.98.121.97:7001","116.62.240.167:7001","121.43.234.253:7001","121.199.72.252:7001","121.40.130.83:7001","121.40.94.52:7001","120.26.46.218:7001","120.55.86.74:7001","121.40.255.201:7001","121.43.148.183:7001","121.40.158.250:7001","121.40.117.123:7001","121.40.88.101:7001","121.40.118.7:7001"]}
EOF

export LIBRARY_PATH=/usr/local/lib
export LD_LIBRARY_PATH=/usr/local/lib
export PYTHONUNBUFFERED=1

python3 -u -m scripts.vaba_run -d -f conf/adkg_16_remote/config-${NODE_ID}.json -time ${START_TIME} > benchmark-logs/node-${NODE_ID}.log 2>&1

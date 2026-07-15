#!/bin/bash

# BFT 分支一键运行脚本
# 用法: ./helper.sh <协议> [参数...]
#
# 支持的协议:
#   acs [N] [t] [B]       - ACS/VABA 异步共识
#   beat [N] [t] [B]      - Beat (无SGX)
#   beat-localcoin [N] [t] [B] - Beat Localcoin
#   dumbo [N] [f] [B] [E] - Dumbo BFT
#
# 示例:
#   ./helper.sh acs           → N=4, t=1, B=100
#   ./helper.sh acs 6 2 500   → N=6, t=2, B=500
#   ./helper.sh beat          → N=4, t=1, B=100
#   ./helper.sh dumbo         → N=4, f=1, B=1000, E=20

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

PROTOCOL=${1:-acs}
shift 2>/dev/null || true

case "$PROTOCOL" in
    acs)
        N=${1:-4}
        T=${2:-1}
        B=${3:-100}
        K=$((T + 1))
        echo "[ACS] N=$N, t=$T, k=$K, B=$B"
        docker build -t trubft:ACS . -q 2>/dev/null
        docker-compose run --rm vaba
        ;;
    beat)
        N=${1:-4}
        T=${2:-1}
        B=${3:-100}
        echo "[Beat] N=$N, t=$T, B=$B"
        docker build -t trubft:TruBFT-None-SGX . -q 2>/dev/null
        docker-compose run --rm beat
        ;;
    beat-localcoin)
        N=${1:-4}
        T=${2:-1}
        B=${3:-100}
        echo "[Beat-Localcoin] N=$N, t=$T, B=$B"
        docker build -t trubft:Beat-Localcoin-PY3 . -q 2>/dev/null
        docker-compose run --rm beat-localcoin
        ;;
    dumbo)
        N=${1:-4}
        F=${2:-1}
        B=${3:-1000}
        E=${4:-20}
        echo "[Dumbo] N=$N, f=$F, B=$B, E=$E"
        sed -i 's/\r$//' run_local_network_test.sh 2>/dev/null
        sed -i 's/llall python3/which python3/' run_local_network_test.sh 2>/dev/null
        sed -i 's/--P "honeybadger"/--P "dumbo"/' run_local_network_test.sh 2>/dev/null
        ./run_local_network_test.sh "$N" "$F" "$B" "$E"
        ;;
    *)
        echo "不支持的协议: $PROTOCOL"
        echo ""
        echo "用法: ./helper.sh <协议> [参数...]"
        echo ""
        echo "支持的协议:"
        echo "  acs [N] [t] [B]           - ACS/VABA 异步共识"
        echo "  beat [N] [t] [B]          - Beat (无SGX)"
        echo "  beat-localcoin [N] [t] [B]- Beat Localcoin"
        echo "  dumbo [N] [f] [B] [E]     - Dumbo BFT"
        echo ""
        echo "示例:"
        echo "  ./helper.sh acs 6 2 500"
        echo "  ./helper.sh beat 4 1 100"
        exit 1
        ;;
esac

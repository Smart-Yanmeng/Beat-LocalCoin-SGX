#!/bin/bash

# BFT 一键运行脚本
# 用法: ./run_bft.sh <协议> [参数覆盖]
#
# 示例:
#   ./run_bft.sh acs                    → N=4, t=1
#   ./run_bft.sh acs -e BFT_N=6 -e BFT_T=2  → N=6, t=2
#   ./run_bft.sh dumbo                  → N=4, B=1000, E=20
#   ./run_bft.sh beat                   → N=4, B=100

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

PROTOCOL=${1:-acs}
shift 2>/dev/null || true

# 默认参数
case "$PROTOCOL" in
    acs)
        IMAGE="trubft:ACS"
        N=${BFT_N:-4}
        T=${BFT_T:-1}
        echo "[ACS] N=$N, t=$T"
        docker build -t trubft:ACS . -q 2>/dev/null
        docker-compose run --rm acs "$@"
        ;;
    dumbo)
        IMAGE="trubft:ACS"
        N=${BFT_N:-4}
        T=${BFT_T:-1}
        B=${BFT_B:-1000}
        E=${BFT_E:-20}
        echo "[Dumbo] N=$N, t=$T, B=$B, E=$E"
        docker build -t trubft:ACS . -q 2>/dev/null
        docker-compose run --rm dumbo "$@"
        ;;
    beat)
        IMAGE="trubft:TruBFT-None-SGX"
        N=${BFT_N:-4}
        T=${BFT_T:-1}
        B=${BFT_B:-100}
        echo "[Beat] N=$N, t=$T, B=$B"
        docker build -t trubft:TruBFT-None-SGX . -q 2>/dev/null
        docker-compose run --rm beat "$@"
        ;;
    *)
        echo "不支持的协议: $PROTOCOL"
        echo ""
        echo "用法: ./run_bft.sh <协议> [参数覆盖]"
        echo ""
        echo "支持的协议:"
        echo "  acs   - ACS/VABA 异步共识"
        echo "  dumbo - Dumbo BFT 异步共识"
        echo "  beat  - Beat (无SGX)"
        echo ""
        echo "参数覆盖 (环境变量):"
        echo "  BFT_N  - 节点数 (默认 4)"
        echo "  BFT_T  - 容错数 (默认 1)"
        echo "  BFT_B  - 批量大小 (beat默认100, dumbo默认1000)"
        echo "  BFT_E  - 轮数 (dumbo默认20)"
        echo ""
        echo "示例:"
        echo "  BFT_N=6 BFT_T=2 ./run_bft.sh acs"
        exit 1
        ;;
esac

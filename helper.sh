#!/bin/bash

# BFT 一键运行脚本
# 用法: ./helper.sh [协议]
#
# 无参数: 显示所有可用命令
# 有参数: 自动切换分支并运行

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

show_help() {
    echo "=========================================="
    echo "  BFT 分支一键运行"
    echo "=========================================="
    echo ""
    echo "直接复制运行以下命令："
    echo ""
    echo "  # ACS/VABA (N=4, t=1, B=100)"
    echo "  git checkout -- . && git checkout ACS && ./helper.sh acs"
    echo ""
    echo "  # Beat 无SGX (N=4, t=1, B=100)"
    echo "  git checkout -- . && git checkout TruBFT-None-SGX && ./helper.sh beat"
    echo ""
    echo "  # Beat-Localcoin (N=4, t=1, B=100)"
    echo "  git checkout -- . && git checkout Beat-Localcoin-PY3 && ./helper.sh beat-localcoin"
    echo ""
    echo "  # Dumbo BFT (N=4, f=1, B=1000, E=20)"
    echo "  git checkout -- . && git checkout Dumbo\\&HB && ./helper.sh dumbo"
    echo ""
    echo "=========================================="
    echo "  自定义参数"
    echo "=========================================="
    echo ""
    echo "  ./helper.sh acs [N] [t] [B]"
    echo "  ./helper.sh beat [N] [t] [B]"
    echo "  ./helper.sh beat-localcoin [N] [t] [B]"
    echo "  ./helper.sh dumbo [N] [f] [B] [E]"
    echo ""
    echo "  示例: ./helper.sh acs 6 2 500"
    echo ""
}

PROTOCOL=${1:-help}
shift 2>/dev/null || true

case "$PROTOCOL" in
    help|--help|-h)
        show_help
        ;;
    acs)
        if [ ! -f docker-compose.yml ] || ! grep -q "vaba" docker-compose.yml 2>/dev/null; then
            echo "错误: 当前分支没有 ACS 配置"
            echo "请运行: git checkout -- . && git checkout ACS && ./helper.sh acs"
            exit 1
        fi
        N=${1:-4}
        T=${2:-1}
        B=${3:-100}
        echo "[ACS] N=$N, t=$T, B=$B"
        docker build -t trubft:ACS . -q 2>/dev/null
        docker-compose run --rm vaba
        ;;
    beat)
        if [ ! -f docker-compose.yml ] || ! grep -q "beat" docker-compose.yml 2>/dev/null; then
            echo "错误: 当前分支没有 Beat 配置"
            echo "请运行: git checkout -- . && git checkout TruBFT-None-SGX && ./helper.sh beat"
            exit 1
        fi
        N=${1:-4}
        T=${2:-1}
        B=${3:-100}
        echo "[Beat] N=$N, t=$T, B=$B"
        docker build -t trubft:TruBFT-None-SGX . -q 2>/dev/null
        docker-compose run --rm beat
        ;;
    beat-localcoin)
        if [ ! -f docker-compose.yml ] || ! grep -q "beat-localcoin" docker-compose.yml 2>/dev/null; then
            echo "错误: 当前分支没有 Beat-Localcoin 配置"
            echo "请运行: git checkout -- . && git checkout Beat-Localcoin-PY3 && ./helper.sh beat-localcoin"
            exit 1
        fi
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
        show_help
        exit 1
        ;;
esac

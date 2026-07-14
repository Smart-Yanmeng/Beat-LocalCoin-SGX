#!/bin/bash

# TruBFT Docker 运行脚本 - 所有操作在容器内完成

MODE=${1:-help}

show_help() {
    echo "=========================================="
    echo "TruBFT Docker 运行"
    echo "=========================================="
    echo ""
    echo "用法: ./run.sh [模式]"
    echo ""
    echo "模式:"
    echo "  build         - 构建镜像"
    echo "  standalone    - 单节点测试"
    echo "  distributed   - 分布式模式"
    echo "  all           - 启动所有4个节点"
    echo "  stop          - 停止所有容器"
    echo "  status        - 查看容器状态"
    echo "  shell         - 进入容器shell"
    echo "  help          - 显示此帮助"
    echo ""
    echo "环境变量（可选）:"
    echo "  TRUBFT_N      - 节点数（默认: 4）"
    echo "  TRUBFT_T      - 容错数（默认: 1）"
    echo "  TRUBFT_B      - 每轮交易数（默认: 100）"
    echo ""
    echo "示例:"
    echo "  ./run.sh build                         # 构建镜像"
    echo "  ./run.sh standalone                    # 默认4节点测试"
    echo "  TRUBFT_N=6 TRUBFT_T=2 ./run.sh standalone  # 6节点测试"
    echo "  ./run.sh shell                         # 进入容器"
    echo ""
    echo "注意: 密钥在容器内自动生成，无需本地环境"
    echo ""
}

case "$MODE" in
    build)
        echo "构建镜像..."
        docker build -t trubft:TruBFT .
        echo "构建完成！"
        ;;
    standalone)
        docker-compose run --rm trubft-standalone
        ;;
    distributed)
        docker-compose run --rm trubft-node
        ;;
    all)
        docker-compose up -d
        docker-compose ps
        ;;
    stop)
        docker-compose down
        ;;
    status)
        docker-compose ps
        ;;
    shell)
        docker-compose run --rm --entrypoint bash trubft-standalone
        ;;
    help|--help|-h|*)
        show_help
        ;;
esac

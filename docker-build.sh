#!/bin/bash

# 分支管理脚本 - 自动为所有分支构建Docker镜像

set -e

# 显示帮助信息
show_help() {
    echo "用法: $0 [选项]"
    echo "选项:"
    echo "  -b, --branch <分支名>    指定单个分支构建"
    echo "  -a, --all                为所有远程分支构建镜像"
    echo "  -m, --mode <模式>        测试模式: standalone 或 distributed"
    echo "  -n, --nodes <节点数>     节点数量（默认: 4）"
    echo "  -t, --tolerance <T>      容错阈值（默认: 1）"
    echo "  -s, --batch <B>          每轮提议交易数（默认: 100）"
    echo "  -x, --transactions <TX>  每节点提交交易数（默认: -1，使用B的值）"
    echo "  -v, --version <V>        共识版本（分布式模式，默认: 1）"
    echo "  -k, --keys <file>        阈值签名密钥文件（默认: thsig4_1.keys）"
    echo "  -e, --ecdsa <file>       ECDSA密钥文件（默认: ecdsa.keys）"
    echo "  -c, --enc <file>         阈值加密密钥文件（默认: thenc4_1.keys）"
    echo "  -r, --run                构建后运行容器"
    echo "  -h, --help               显示帮助信息"
    echo "示例:"
    echo "  $0 -b feature-x -m standalone -n 6 -t 2"
    echo "  $0 -a                    # 为所有分支构建镜像"
    echo "  $0 -a -r -n 8 -t 2      # 构建所有分支并以8节点运行"
}

# 默认值
BRANCH=""
BUILD_ALL=false
MODE="standalone"
NODES=4
TOLERANCE=1
BATCH_SIZE=100
TX_COUNT=-1
VERSION=1
KEYS_FILE="thsig4_1.keys"
ECDSA_FILE="ecdsa.keys"
ENC_FILE="thenc4_1.keys"
RUN_AFTER=false

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -b|--branch)
            BRANCH="$2"
            shift 2
            ;;
        -a|--all)
            BUILD_ALL=true
            shift
            ;;
        -m|--mode)
            MODE="$2"
            shift 2
            ;;
        -n|--nodes)
            NODES="$2"
            shift 2
            ;;
        -t|--tolerance)
            TOLERANCE="$2"
            shift 2
            ;;
        -s|--batch)
            BATCH_SIZE="$2"
            shift 2
            ;;
        -x|--transactions)
            TX_COUNT="$2"
            shift 2
            ;;
        -v|--version)
            VERSION="$2"
            shift 2
            ;;
        -k|--keys)
            KEYS_FILE="$2"
            shift 2
            ;;
        -e|--ecdsa)
            ECDSA_FILE="$2"
            shift 2
            ;;
        -c|--enc)
            ENC_FILE="$2"
            shift 2
            ;;
        -r|--run)
            RUN_AFTER=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "未知参数: $1"
            show_help
            exit 1
            ;;
    esac
done

# 保存当前分支
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
REPO_NAME=$(basename -s .git $(git remote get-url origin))

# 生成docker-compose文件的函数
generate_compose() {
    local branch=$1
    local branch_clean=$(echo "$branch" | sed 's/\//-/g')
    local image_name="${REPO_NAME,,}:${branch_clean}"
    local compose_file="docker-compose.${branch_clean}.yml"
    
    cat > "$compose_file" << EOF
version: '3.8'

services:
  # Standalone模式服务
  trubft-standalone:
    image: ${image_name}
    volumes:
      - .:/app
    environment:
      - TRUBFT_MODE=standalone
      - TRUBFT_N=\${TRUBFT_N:-4}
      - TRUBFT_T=\${TRUBFT_T:-1}
      - TRUBFT_B=\${TRUBFT_B:-100}
      - TRUBFT_TX=\${TRUBFT_TX:--1}
      - TRUBFT_KEYS=\${TRUBFT_KEYS:-thsig4_1.keys}
      - TRUBFT_ECDSA=\${TRUBFT_ECDSA:-ecdsa.keys}
      - TRUBFT_ENC=\${TRUBFT_ENC:-thenc4_1.keys}

  # Distributed模式服务（动态节点）
  trubft-node:
    image: ${image_name}
    volumes:
      - .:/app
    environment:
      - TRUBFT_MODE=distributed
      - TRUBFT_N=\${TRUBFT_N:-4}
      - TRUBFT_T=\${TRUBFT_T:-1}
      - TRUBFT_B=\${TRUBFT_B:-100}
      - TRUBFT_TX=\${TRUBFT_TX:--1}
      - TRUBFT_KEYS=\${TRUBFT_KEYS:-thsig4_1.keys}
      - TRUBFT_ECDSA=\${TRUBFT_ECDSA:-ecdsa.keys}
      - TRUBFT_ENC=\${TRUBFT_ENC:-thenc4_1.keys}
      - TRUBFT_MY_ID=\${TRUBFT_MY_ID:-0}
      - TRUBFT_VERSION=\${TRUBFT_VERSION:-1}
      - TRUBFT_DELAY=\${TRUBFT_DELAY:-50}

  # 预定义4节点配置
  trubft-node-0:
    image: ${image_name}
    volumes:
      - .:/app
    environment:
      - TRUBFT_MODE=distributed
      - TRUBFT_N=\${TRUBFT_N:-4}
      - TRUBFT_T=\${TRUBFT_T:-1}
      - TRUBFT_B=\${TRUBFT_B:-100}
      - TRUBFT_TX=\${TRUBFT_TX:--1}
      - TRUBFT_KEYS=\${TRUBFT_KEYS:-thsig4_1.keys}
      - TRUBFT_ECDSA=\${TRUBFT_ECDSA:-ecdsa.keys}
      - TRUBFT_ENC=\${TRUBFT_ENC:-thenc4_1.keys}
      - TRUBFT_MY_ID=0
      - TRUBFT_VERSION=\${TRUBFT_VERSION:-1}
    depends_on:
      - trubft-node-1
      - trubft-node-2
      - trubft-node-3

  trubft-node-1:
    image: ${image_name}
    volumes:
      - .:/app
    environment:
      - TRUBFT_MODE=distributed
      - TRUBFT_N=\${TRUBFT_N:-4}
      - TRUBFT_T=\${TRUBFT_T:-1}
      - TRUBFT_B=\${TRUBFT_B:-100}
      - TRUBFT_TX=\${TRUBFT_TX:--1}
      - TRUBFT_KEYS=\${TRUBFT_KEYS:-thsig4_1.keys}
      - TRUBFT_ECDSA=\${TRUBFT_ECDSA:-ecdsa.keys}
      - TRUBFT_ENC=\${TRUBFT_ENC:-thenc4_1.keys}
      - TRUBFT_MY_ID=1
      - TRUBFT_VERSION=\${TRUBFT_VERSION:-1}

  trubft-node-2:
    image: ${image_name}
    volumes:
      - .:/app
    environment:
      - TRUBFT_MODE=distributed
      - TRUBFT_N=\${TRUBFT_N:-4}
      - TRUBFT_T=\${TRUBFT_T:-1}
      - TRUBFT_B=\${TRUBFT_B:-100}
      - TRUBFT_TX=\${TRUBFT_TX:--1}
      - TRUBFT_KEYS=\${TRUBFT_KEYS:-thsig4_1.keys}
      - TRUBFT_ECDSA=\${TRUBFT_ECDSA:-ecdsa.keys}
      - TRUBFT_ENC=\${TRUBFT_ENC:-thenc4_1.keys}
      - TRUBFT_MY_ID=2
      - TRUBFT_VERSION=\${TRUBFT_VERSION:-1}

  trubft-node-3:
    image: ${image_name}
    volumes:
      - .:/app
    environment:
      - TRUBFT_MODE=distributed
      - TRUBFT_N=\${TRUBFT_N:-4}
      - TRUBFT_T=\${TRUBFT_T:-1}
      - TRUBFT_B=\${TRUBFT_B:-100}
      - TRUBFT_TX=\${TRUBFT_TX:--1}
      - TRUBFT_KEYS=\${TRUBFT_KEYS:-thsig4_1.keys}
      - TRUBFT_ECDSA=\${TRUBFT_ECDSA:-ecdsa.keys}
      - TRUBFT_ENC=\${TRUBFT_ENC:-thenc4_1.keys}
      - TRUBFT_MY_ID=3
      - TRUBFT_VERSION=\${TRUBFT_VERSION:-1}
EOF
    
    echo "✓ 生成 $compose_file"
}

# 构建单个分支的函数
build_branch() {
    local branch=$1
    local branch_clean=$(echo "$branch" | sed 's/\//-/g')
    local image_name="${REPO_NAME,,}:${branch_clean}"
    
    echo "=========================================="
    echo "构建分支: $branch"
    echo "镜像名称: $image_name"
    echo "=========================================="
    
    # 切换到指定分支
    git checkout "$branch"
    
    # 构建Docker镜像
    docker build -t "$image_name" .
    
    # 生成docker-compose文件
    generate_compose "$branch"
    
    echo "✓ 镜像 $image_name 构建完成"
    echo ""
}

# 运行容器的函数
run_container() {
    local branch=$1
    local branch_clean=$(echo "$branch" | sed 's/\//-/g')
    local compose_file="docker-compose.${branch_clean}.yml"
    
    echo "运行分支 $branch 的容器..."
    echo "参数: N=$NODES, T=$TOLERANCE, B=$BATCH_SIZE"
    
    # 导出环境变量供docker-compose使用
    export TRUBFT_N=$NODES
    export TRUBFT_T=$TOLERANCE
    export TRUBFT_B=$BATCH_SIZE
    export TRUBFT_TX=$TX_COUNT
    export TRUBFT_KEYS=$KEYS_FILE
    export TRUBFT_ECDSA=$ECDSA_FILE
    export TRUBFT_ENC=$ENC_FILE
    export TRUBFT_VERSION=$VERSION
    
    if [ "$MODE" = "standalone" ]; then
        docker-compose -f "$compose_file" up trubft-standalone
    elif [ "$MODE" = "distributed" ]; then
        docker-compose -f "$compose_file" up -d
    fi
}

# 主逻辑
if [ "$BUILD_ALL" = true ]; then
    echo "开始为所有远程分支构建Docker镜像..."
    echo ""
    
    # 获取所有远程分支
    branches=$(git branch -r | grep -v HEAD | sed 's/origin\///' | xargs)
    
    for branch in $branches; do
        # 检查分支是否有Dockerfile
        if git show "origin/$branch:Dockerfile" >/dev/null 2>&1; then
            build_branch "$branch"
        else
            echo "跳过分支 $branch (无Dockerfile)"
        fi
    done
    
    # 如果需要运行，遍历运行
    if [ "$RUN_AFTER" = true ]; then
        echo "开始运行所有分支的容器..."
        for branch in $branches; do
            if git show "origin/$branch:Dockerfile" >/dev/null 2>&1; then
                run_container "$branch"
            fi
        done
    fi
    
    # 恢复到原始分支
    git checkout "$CURRENT_BRANCH"
    echo "已恢复到原始分支: $CURRENT_BRANCH"
    
elif [ -n "$BRANCH" ]; then
    build_branch "$BRANCH"
    
    if [ "$RUN_AFTER" = true ]; then
        run_container "$BRANCH"
    fi
    
    # 恢复到原始分支
    git checkout "$CURRENT_BRANCH"
    
else
    echo "错误: 必须指定分支 (-b) 或使用 -a 构建所有分支"
    show_help
    exit 1
fi

echo "=========================================="
echo "构建完成！"
echo "=========================================="
echo ""
echo "查看所有镜像:"
docker images | grep "$REPO_NAME"
echo ""
echo "运行容器:"
echo "  单分支: docker-compose -f docker-compose.<分支名>.yml up trubft-standalone"
echo "  所有分支: ./docker-build.sh -a -r"
echo ""
echo "自定义参数运行:"
echo "  TRUBFT_N=8 TRUBFT_T=2 ./docker-build.sh -b TruBFT -r"
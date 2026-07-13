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
    echo "  -n, --nodes <节点数>     节点数量（distributed模式）"
    echo "  -r, --run                构建后运行容器"
    echo "  -h, --help               显示帮助信息"
    echo "示例:"
    echo "  $0 -b feature-x -m standalone"
    echo "  $0 -a                    # 为所有分支构建镜像"
    echo "  $0 -a -r                 # 为所有分支构建并运行"
}

# 默认值
BRANCH=""
BUILD_ALL=false
MODE="standalone"
NODES=4
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
    
    echo "✓ 镜像 $image_name 构建完成"
    echo ""
}

# 运行容器的函数
run_container() {
    local branch=$1
    local branch_clean=$(echo "$branch" | sed 's/\//-/g')
    local image_name="${REPO_NAME,,}:${branch_clean}"
    
    echo "运行分支 $branch 的容器..."
    
    if [ "$MODE" = "standalone" ]; then
        docker run --rm -it "$image_name"
    elif [ "$MODE" = "distributed" ]; then
        echo "分布式模式需要docker-compose配置"
        # 为分布式模式创建临时docker-compose
        cat > docker-compose临时.yml << EOF
version: '3.8'
services:
  node-0:
    image: $image_name
    command: python3 -m adaptive.test.honest_party_test_EC2 -k thsig4_1.keys -e ecdsa.keys -b 100 -n 4 -t 1 -c thenc4_1.keys -s hosts -v 1 --my-id 0
  node-1:
    image: $image_name
    command: python3 -m adaptive.test.honest_party_test_EC2 -k thsig4_1.keys -e ecdsa.keys -b 100 -n 4 -t 1 -c thenc4_1.keys -s hosts -v 1 --my-id 1
  node-2:
    image: $image_name
    command: python3 -m adaptive.test.honest_party_test_EC2 -k thsig4_1.keys -e ecdsa.keys -b 100 -n 4 -t 1 -c thenc4_1.keys -s hosts -v 1 --my-id 2
  node-3:
    image: $image_name
    command: python3 -m adaptive.test.honest_party_test_EC2 -k thsig4_1.keys -e ecdsa.keys -b 100 -n 4 -t 1 -c thenc4_1.keys -s hosts -v 1 --my-id 3
EOF
        docker-compose -f docker-compose临时.yml up
        rm docker-compose临时.yml
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
            run_container "$branch"
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
echo "  单分支: ./docker-build.sh -b <分支名> -r"
echo "  所有分支: ./docker-build.sh -a -r"
#!/bin/bash

# 列出所有分支的Docker镜像状态

REPO_NAME=$(basename -s .git $(git remote get-url origin))

echo "TruBFT 分支 Docker 镜像状态"
echo "=========================================="
echo ""

# 获取所有远程分支
branches=$(git branch -r | grep -v HEAD | sed 's/origin\///' | xargs)

for branch in $branches; do
    branch_clean=$(echo "$branch" | sed 's/\//-/g')
    image_name="${REPO_NAME,,}:${branch_clean}"
    
    # 检查镜像是否存在
    if docker image inspect "$image_name" >/dev/null 2>&1; then
        # 获取镜像大小和创建时间
        size=$(docker image inspect "$image_name" --format '{{.Size}}' | numfmt --to=iec-i --suffix=B)
        created=$(docker image inspect "$image_name" --format '{{.Created}}' | cut -d'T' -f1)
        echo "✓ $branch -> $image_name ($size, $created)"
    else
        echo "✗ $branch -> $image_name (未构建)"
    fi
done

echo ""
echo "=========================================="
echo "构建所有镜像: ./docker-build.sh -a"
echo "构建并运行:   ./docker-build.sh -a -r"
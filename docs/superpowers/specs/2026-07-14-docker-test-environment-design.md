# Docker容器测试环境设计方案

## 项目背景

TruBFT项目是一个基于阈值密码学的分布式共识协议实现。每个分支需要独立的Docker容器进行测试，支持standalone和distributed两种测试模式。

## 设计目标

1. 为每个分支创建独立的Docker容器测试环境
2. 支持standalone模式（单节点测试）
3. 支持distributed模式（多节点测试）
4. 使用Docker Compose统一管理
5. 支持代码热更新（volume挂载）

## 技术方案

### 1. Dockerfile设计

基于Python 3.8，安装所有必要依赖：

```dockerfile
FROM python:3.8-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libgmp-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
RUN pip install gevent charm-crypto pycryptodome

# 复制项目代码
COPY . .

# 设置环境变量
ENV PYTHONPATH=/app/adaptive/commoncoin:/app/adaptive/ecdsa:/app/adaptive/threshenc:/app/adaptive/core:/app/adaptive
ENV LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:$LIBRARY_PATH
ENV LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH

# 默认命令（standalone模式）
CMD ["python3", "-m", "adaptive.test.honest_party_test", "-k", "thsig4_1.keys", "-e", "ecdsa.keys", "-b", "100", "-n", "4", "-t", "1", "-c", "thenc4_1.keys"]
```

### 2. docker-compose.yml设计

```yaml
version: '3.8'

services:
  # Standalone模式服务
  trubft-standalone:
    build:
      context: .
      dockerfile: Dockerfile
    volumes:
      - .:/app
    command: >
      python3 -m adaptive.test.honest_party_test 
      -k thsig4_1.keys 
      -e ecdsa.keys 
      -b 100 
      -n 4 
      -t 1 
      -c thenc4_1.keys

  # Distributed模式服务（4个节点）
  trubft-node-0:
    build:
      context: .
      dockerfile: Dockerfile
    volumes:
      - .:/app
    command: >
      python3 -m adaptive.test.honest_party_test_EC2 
      -k thsig4_1.keys 
      -e ecdsa.keys 
      -b 100 
      -n 4 
      -t 1 
      -c thenc4_1.keys 
      -s hosts 
      -v 1 
      --my-id 0
    depends_on:
      - trubft-node-1
      - trubft-node-2
      - trubft-node-3

  trubft-node-1:
    build:
      context: .
      dockerfile: Dockerfile
    volumes:
      - .:/app
    command: >
      python3 -m adaptive.test.honest_party_test_EC2 
      -k thsig4_1.keys 
      -e ecdsa.keys 
      -b 100 
      -n 4 
      -t 1 
      -c thenc4_1.keys 
      -s hosts 
      -v 1 
      --my-id 1

  trubft-node-2:
    build:
      context: .
      dockerfile: Dockerfile
    volumes:
      - .:/app
    command: >
      python3 -m adaptive.test.honest_party_test_EC2 
      -k thsig4_1.keys 
      -e ecdsa.keys 
      -b 100 
      -n 4 
      -t 1 
      -c thenc4_1.keys 
      -s hosts 
      -v 1 
      --my-id 2

  trubft-node-3:
    build:
      context: .
      dockerfile: Dockerfile
    volumes:
      - .:/app
    command: >
      python3 -m adaptive.test.honest_party_test_EC2 
      -k thsig4_1.keys 
      -e ecdsa.keys 
      -b 100 
      -n 4 
      -t 1 
      -c thenc4_1.keys 
      -s hosts 
      -v 1 
      --my-id 3
```

### 3. 分支管理脚本

创建`docker-build.sh`脚本，支持自动切换分支并构建Docker容器：

```bash
#!/bin/bash

# 分支管理脚本

set -e

# 显示帮助信息
show_help() {
    echo "用法: $0 [选项]"
    echo "选项:"
    echo "  -b, --branch <分支名>    指定分支名称"
    echo "  -m, --mode <模式>        测试模式: standalone 或 distributed"
    echo "  -n, --nodes <节点数>     节点数量（distributed模式）"
    echo "  -h, --help               显示帮助信息"
    echo "示例:"
    echo "  $0 -b feature-x -m standalone"
    echo "  $0 -b feature-x -m distributed -n 4"
}

# 默认值
BRANCH=""
MODE="standalone"
NODES=4

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -b|--branch)
            BRANCH="$2"
            shift 2
            ;;
        -m|--mode)
            MODE="$2"
            shift 2
            ;;
        -n|--nodes)
            NODES="$2"
            shift 2
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

# 检查分支参数
if [ -z "$BRANCH" ]; then
    echo "错误: 必须指定分支名称"
    show_help
    exit 1
fi

# 切换到指定分支
echo "切换到分支: $BRANCH"
git checkout "$BRANCH"

# 构建Docker镜像
echo "构建Docker镜像..."
docker-compose build

# 根据模式运行容器
if [ "$MODE" = "standalone" ]; then
    echo "启动standalone模式..."
    docker-compose up trubft-standalone
elif [ "$MODE" = "distributed" ]; then
    echo "启动distributed模式，节点数: $NODES"
    docker-compose up -d --scale trubft-node-0=1 --scale trubft-node-1=1 --scale trubft-node-2=1 --scale trubft-node-3=1
else
    echo "错误: 未知模式 $MODE"
    exit 1
fi

echo "测试完成"
```

### 4. hosts文件

在项目根目录创建`hosts`文件，用于distributed模式：

```
trubft-node-0
trubft-node-1
trubft-node-2
trubft-node-3
```

## 使用方法

### 1. 构建Docker镜像

```bash
docker-compose build
```

### 2. Standalone模式测试

```bash
docker-compose up trubft-standalone
```

### 3. Distributed模式测试

```bash
docker-compose up -d
```

### 4. 使用分支管理脚本

```bash
# 为feature-x分支创建standalone测试环境
./docker-build.sh -b feature-x -m standalone

# 为feature-x分支创建distributed测试环境
./docker-build.sh -b feature-x -m distributed -n 4
```

## 设计优势

1. **隔离性**：每个分支对应独立的Docker容器，互不影响
2. **灵活性**：支持standalone和distributed两种测试模式
3. **易用性**：使用Docker Compose统一管理，简化操作
4. **可扩展性**：易于添加新的测试节点或服务
5. **热更新**：使用volume挂载代码，支持代码修改后实时更新

## 注意事项

1. 确保Docker和Docker Compose已安装
2. distributed模式需要配置正确的hosts文件
3. 首次运行需要构建镜像，可能需要一些时间
4. 使用volume挂载代码时，修改会实时反映到容器中
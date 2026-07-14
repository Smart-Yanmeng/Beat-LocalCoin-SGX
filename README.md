# TruBFT

> 基于 [HoneyBadgerBFT](https://github.com/amiller/HoneyBadgerBFT) 项目的改进实现

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## 项目简介

TruBFT 是一个基于阈值密码学的分布式共识协议实现，支持 SGX 和 Non-SGX 两种运行模式。

## 环境要求

### 基础依赖
- Python 3.7+
- pip

### Python 依赖
```bash
pip install gevent charm-crypto pycryptodome ecdsa cryptography gipc
```

### SGX 模式额外依赖（可选）
- Intel SGX SDK
- Gramine 1.8+

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/Smart-Yanmeng/TruBFT.git
cd TruBFT
```

### 2. 密钥文件

项目已预生成 N=4, T=1 的密钥文件，可直接使用：

| 文件 | 说明 | 大小 |
|------|------|------|
| `thsig4_1.keys` | 阈值签名密钥 | ~533 字节 |
| `ecdsa.keys` | ECDSA 密钥 | ~156 字节 |
| `thenc4_1.keys` | 阈值加密密钥 | ~363 字节 |

**如果密钥文件丢失或损坏，从 git 恢复：**
```bash
git checkout -- thsig4_1.keys ecdsa.keys thenc4_1.keys
```

**如果需要生成其他 N 值的密钥（需在 Docker 容器内执行）：**
```bash
# 进入容器
docker-compose run --rm --entrypoint bash trubft-standalone

# 在容器内生成密钥（例如 N=6, K=3）
python3 -m adaptive.commoncoin.thresprf 6 3 > thsig6_1.keys
python3 -m adaptive.ecdsa.generate_keys_ecdsa 6 ecdsa6.keys
python3 -m adaptive.threshenc.tdh2 6 3 > thenc6_1.keys
```

### 3. 运行测试

#### 单机模式（Standalone）

```bash
python3 -m adaptive.test.honest_party_test \
  -k thsig4_1.keys \
  -e ecdsa.keys \
  -c thenc4_1.keys \
  -n 4 \
  -t 1 \
  -b 100
```

#### 分布式模式（Distributed）

首先创建 `hosts` 文件，每行一个服务器 IP：
```
192.168.1.101
192.168.1.102
192.168.1.103
192.168.1.104
```

然后在每台服务器上运行（以节点0为例）：
```bash
python3 -m adaptive.test.honest_party_test_EC2 \
  -k thsig4_1.keys \
  -e ecdsa.keys \
  -c thenc4_1.keys \
  -s hosts \
  -n 4 \
  -t 1 \
  -b 100 \
  -v 1 \
  --my-id 0
```

## 命令参数说明

### Standalone 模式参数 (`honest_party_test.py`)

| 参数 | 长参数 | 说明 | 类型 | 默认值 | 必填 |
|------|--------|------|------|--------|------|
| `-k` | `--threshold-keys` | 阈值签名密钥文件路径 | string | - | 是 |
| `-e` | `--ecdsa-keys` | ECDSA 密钥文件路径 | string | - | 是 |
| `-c` | `--threshold-enc` | 阈值加密密钥文件路径 | string | - | 是 |
| `-n` | `--number` | 节点总数 | int | - | 是 |
| `-t` | `--tolerance` | 容忍的恶意节点数 | int | - | 是 |
| `-b` | `--propose-size` | 每轮提议的交易数量 | int | ceil(N*ln(N)) | 否 |
| `-x` | `--transactions` | 每个节点提交的交易数 | int | -1 (使用B的值) | 否 |

**Standalone 模式示例：**
```bash
python3 -m adaptive.test.honest_party_test \
  -k thsig4_1.keys \
  -e ecdsa.keys \
  -c thenc4_1.keys \
  -n 4 \
  -t 1 \
  -b 100
```

### Distributed 模式参数 (`honest_party_test_EC2.py`)

| 参数 | 长参数 | 说明 | 类型 | 默认值 | 必填 |
|------|--------|------|------|--------|------|
| `-k` | `--threshold-keys` | 阈值签名密钥文件路径 | string | - | 是 |
| `-e` | `--ecdsa-keys` | ECDSA 密钥文件路径 | string | - | 是 |
| `-c` | `--threshold-enc` | 阈值加密密钥文件路径 | string | - | 是 |
| `-n` | `--number` | 节点总数 | int | - | 是 |
| `-t` | `--tolerance` | 容忍的恶意节点数 | int | - | 是 |
| `-b` | `--propose-size` | 每轮提议的交易数量 | int | ceil(N*ln(N)) | 否 |
| `-x` | `--transactions` | 每个节点提交的交易数 | int | -1 (使用B的值) | 否 |
| `-v` | `--version` | 二进制共识版本 | int | - | 是 |
| `-s` | `--hosts` | 主机列表文件路径 | string | ~/hosts | 否 |
| `-p` | `--tx-path` | 交易集文件路径 | string | tx | 否 |
| `-a` | `--negotiated-time` | 协议启动延迟倍数 | int | 50 | 否 |
| | `--my-id` | 当前节点 ID | int | 0 | 否 |

**Distributed 模式示例：**
```bash
python3 -m adaptive.test.honest_party_test_EC2 \
  -k thsig4_1.keys \
  -e ecdsa.keys \
  -c thenc4_1.keys \
  -s hosts \
  -n 4 \
  -t 1 \
  -b 100 \
  -v 1 \
  --my-id 0
```

### docker-build.sh 脚本参数

| 参数 | 长参数 | 说明 | 默认值 |
|------|--------|------|--------|
| `-b` | `--branch` | 指定单个分支构建 | - |
| `-a` | `--all` | 为所有远程分支构建镜像 | false |
| `-m` | `--mode` | 测试模式: standalone 或 distributed | standalone |
| `-n` | `--nodes` | 节点数量 | 4 |
| `-t` | `--tolerance` | 容错阈值 | 1 |
| `-s` | `--batch` | 每轮提议交易数 | 100 |
| `-x` | `--transactions` | 每节点提交交易数 | -1 (使用B的值) |
| `-v` | `--version` | 共识版本（分布式模式） | 1 |
| `-k` | `--keys` | 阈值签名密钥文件 | thsig4_1.keys |
| `-e` | `--ecdsa` | ECDSA密钥文件 | ecdsa.keys |
| `-c` | `--enc` | 阈值加密密钥文件 | thenc4_1.keys |
| `-r` | `--run` | 构建后运行容器 | false |
| `-h` | `--help` | 显示帮助信息 | - |

**docker-build.sh 示例：**
```bash
# 为指定分支构建
./docker-build.sh -b TruBFT -m standalone

# 为所有分支构建并运行
./docker-build.sh -a -r

# 自定义参数构建
./docker-build.sh -b TruBFT -n 6 -t 2 -r
```

## Docker 容器测试

### 环境要求
- Docker Desktop (Windows/Mac) 或 Docker Engine (Linux)
- Docker Compose

### 快速开始

#### 1. 构建镜像
```bash
docker build -t trubft:TruBFT .
```

#### 2. 运行测试
```bash
# 默认参数 (N=4, T=1, B=100)
docker-compose run --rm trubft-standalone

# 或使用 run.sh 脚本
./run.sh standalone
```

### 参数配置

Docker 容器支持通过环境变量配置以下参数：

| 环境变量 | 说明 | 默认值 |
|---------|------|--------|
| `TRUBFT_N` | 节点总数 | 4 |
| `TRUBFT_T` | 容错阈值 | 1 |
| `TRUBFT_B` | 每轮提议交易数 | 100 |
| `TRUBFT_TX` | 每节点提交交易数 | -1 (使用B的值) |
| `TRUBFT_MODE` | 运行模式 (standalone/distributed) | standalone |
| `TRUBFT_MY_ID` | 节点ID (分布式模式) | 0 |
| `TRUBFT_VERSION` | 共识版本 (分布式模式) | 1 |
| `TRUBFT_DELAY` | 启动延迟 (分布式模式) | 50 |

### 运行模式

#### Standalone模式（单节点测试）
```bash
# 使用默认参数
docker-compose run --rm trubft-standalone

# 自定义参数
TRUBFT_N=4 TRUBFT_T=1 TRUBFT_B=100 docker-compose run --rm trubft-standalone
```

#### Distributed模式（多节点测试）
```bash
# 启动所有4个节点
docker-compose up -d

# 查看节点状态
docker-compose ps

# 停止所有节点
docker-compose down
```

### run.sh 脚本使用

```bash
# 查看帮助
./run.sh help

# 运行 standalone 模式
./run.sh standalone

# 生成密钥
./run.sh keys

# 查看容器状态
./run.sh status

# 停止所有容器
./run.sh stop
```

### 分支镜像管理

#### 为所有分支构建Docker镜像
```bash
./docker-build.sh -a
```

#### 为指定分支构建并运行
```bash
./docker-build.sh -b TruBFT -r
./docker-build.sh -b ACS -r
```

#### 查看所有分支的镜像状态
```bash
./docker-list.sh
```

#### 分支镜像命名规则
- 镜像格式: `trubft:<分支名>`
- 示例: `trubft:TruBFT`, `trubft:ACS`, `trubft:Beat-PY3`

### 密钥文件说明

| 文件 | 说明 | 生成方式 |
|------|------|----------|
| `thsig4_1.keys` | 阈值签名密钥 | 预生成（N=4, K=2） |
| `ecdsa.keys` | ECDSA 密钥 | 预生成（N=4） |
| `thenc4_1.keys` | 阈值加密密钥 | 预生成（N=4, K=2） |

**注意：** 当前密钥文件是为 N=4, T=1 预生成的。如果需要改变节点数 N，必须在 Docker 容器内重新生成所有密钥文件。

## 项目结构

```
TruBFT/
├── adaptive/
│   ├── commoncoin/     # 阈值签名和公共硬币协议
│   ├── core/           # 核心共识协议实现
│   ├── ecdsa/          # ECDSA 签名模块
│   ├── sgx/            # SGX 相关代码（可选）
│   ├── test/           # 测试脚本
│   └── threshenc/      # 阈值加密模块
├── Dockerfile          # Docker容器配置
├── docker-compose.yml  # Docker Compose配置
├── docker-build.sh     # 分支管理脚本
├── docker-list.sh      # 查看镜像状态
├── docker-entrypoint.sh # Docker入口脚本
├── run.sh              # 运行脚本
├── hosts               # 分布式模式节点配置
├── LICENSE
└── README.md
```

## 常见问题

### 1. 密钥文件为空
如果密钥文件大小为 0 字节，从 git 恢复：
```bash
git checkout -- thsig4_1.keys ecdsa.keys thenc4_1.keys
```

### 2. Docker 构建失败
如果构建过程中出现网络问题，可以配置镜像源：
```bash
# 配置 pip 镜像
pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/

# 配置 apt 镜像（Ubuntu/Debian）
echo "deb http://mirrors.aliyun.com/debian/ bullseye main" > /etc/apt/sources.list
```

### 3. charm-crypto 安装失败
charm-crypto 需要从源码编译，确保已安装以下依赖：
```bash
apt-get install build-essential libgmp-dev libssl-dev
```

### 4. 共识协议运行正常但没有输出
确保使用正确的密钥文件和参数。检查密钥文件是否完整：
```bash
ls -la *.keys
# 正常大小: thsig4_1.keys (~533字节), ecdsa.keys (~156字节), thenc4_1.keys (~363字节)
```

## 致谢

本项目基于 [HoneyBadgerBFT](https://github.com/amiller/HoneyBadgerBFT) 项目开发。

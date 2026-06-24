# Dumbo&HB (Dumbo BFT & HoneyBadger BFT)

> 基于 Bolt-Dumbo Transformer 的概念验证实现，包含 HoneyBadger BFT 协议

## License

This project is released under the CRAPL academic license. See `CRAPL-LICENSE.txt`.

## 项目简介

本项目是 Bolt-Dumbo Transformer 的概念验证实现，基于 [HoneyBadgerBFT](https://github.com/initc3/HoneyBadgerBFT-Python) 协议开发。

### 主要特性

- 实现 Dumbo-2 协议（Guo et al. CCS'2020）
- 支持 Bolt-Dumbo Transformer (BDT) 变体
- 支持 RBC-BDT 变体
- 提供本地测试和 AWS 部署支持
- 包含完整的基准测试结果

## 项目结构

```
Beat-LocalCoin-SGX/
├── bdtbft/                     # Bolt-Dumbo Transformer 实现
├── dumbobft/                   # Dumbo BFT 协议实现
├── honeybadgerbft/             # HoneyBadger BFT 协议实现
├── rbcbdtbft/                  # RBC-BDT 协议实现
├── crypto/                     # 密码学工具
├── network/                    # 网络通信模块
├── keys/                       # 密钥文件
├── keys-4/                     # 4节点密钥
├── keys-7/                     # 7节点密钥
├── keys-16/                    # 16节点密钥
├── keys-100/                   # 100节点密钥
├── log/                        # 日志目录
├── myexperiements/             # 实验记录
├── Dockerfile                  # Docker 镜像
├── run_socket_node.py          # 节点运行脚本
├── run_local_network_test.sh   # 本地网络测试
├── start_node.sh               # 节点启动脚本
├── run_*.sh                    # 各种运行脚本
├── *_results.csv               # 基准测试结果
├── LICENSE
└── README.md
```

## 环境要求

### Python 版本

- **最低要求**: Python 3.8

### 依赖安装（Ubuntu 18.04+）

```bash
sudo apt-get update
sudo apt-get -y install make bison flex libgmp-dev libmpc-dev python3 python3-dev python3-pip libssl-dev

# 安装 PBC 库
wget https://crypto.stanford.edu/pbc/files/pbc-0.5.14.tar.gz
tar -xvf pbc-0.5.14.tar.gz
cd pbc-0.5.14
sudo ./configure
sudo make
sudo make install
cd ..

sudo ldconfig /usr/local/lib

# 设置环境变量
export LIBRARY_PATH=$LIBRARY_PATH:/usr/local/lib
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib

# 安装 Charm 库
git clone https://github.com/JHUISI/charm.git
cd charm
sudo ./configure.sh
sudo make
sudo make install
sudo make test
cd ..

# 安装 Python 依赖
python3 -m pip install --upgrade pip
sudo pip3 install gevent setuptools gevent numpy ecdsa pysocks gmpy2==2.1.2 zfec==1.5.7.4 gipc pycryptodome==3.23.0 coincurve
```

## 快速开始

### 1. 运行 Dumbo-2 本地测试

```bash
# 运行 4 节点，1000 交易，20 轮
./run_local_network_test.sh 4 1 1000 20
```

### 2. 运行 BDT 变体

编辑 `run_local_network_test.sh` 第12行，将 `"dumbo"` 替换为 `"bdt"` 或 `"rbc-bdt"`：

```bash
./run_local_network_test.sh 4 1 1000 20
```

### 3. 使用 Docker

```bash
docker-compose run --rm honeybadger
```

## 命令参数说明

### run_local_network_test.sh 参数

| 参数 | 说明 | 示例 |
|------|------|------|
| N | 节点总数 | 4 |
| t | 容忍的恶意节点数（需满足 N > 3t） | 1 |
| B | 批量交易数 | 1000 |
| E | 运行轮数 | 20 |

### run_socket_node.py 参数

| 参数 | 说明 | 默认值 | 示例 |
|------|------|--------|------|
| `--sid` | 会话 ID | 无 | `--sid sidA` |
| `--id` | 节点 ID | 无 | `--id 0` |
| `--N` | 节点总数 | 无 | `--N 4` |
| `--f` | 容忍恶意节点数 | 无 | `--f 1` |
| `--B` | 批量大小 | 无 | `--B 10000` |
| `--K` | 参数 K | 无 | `--K 11` |
| `--S` | 参数 S | 无 | `--S 50` |
| `--T` | 参数 T | 无 | `--T 2` |
| `--P` | 协议类型 | 无 | `--P "bdt"` |
| `--F` | 参数 F | 无 | `--F 1000000` |

### 示例命令

#### 本地 4 节点测试

```bash
./run_local_network_test.sh 4 1 1000 20
```

#### AWS 分布式部署

参考 `run_local_network_test.sh` 中的命令，在 AWS 服务器上运行协议。

## 协议说明

### Dumbo-2

Dumbo-2 是一个异步拜占庭容错协议，使用悲观回退路径。

### Bolt-Dumbo Transformer (BDT)

BDT 是 Dumbo-2 的变体，使用 Bolt 协议进行广播。

### RBC-BDT

RBC-BDT 是使用可靠广播（RBC）的 BDT 变体。

## 致谢

本项目基于 [HoneyBadgerBFT](https://github.com/initc3/HoneyBadgerBFT-Python) 项目开发。

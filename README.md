# BEAT-LOCAL-COIN

> 基于 [HoneyBadgerBFT](https://github.com/amiller/HoneyBadgerBFT) 项目的改进实现

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## 项目简介

BEAT-LOCAL-COIN 是一个基于阈值密码学的分布式共识协议实现，支持 SGX 和 Non-SGX 两种运行模式。

## 环境要求

### 基础依赖
- Python 3.8
- pip

### Python 依赖
```bash
pip install gevent charm-crypto pycryptodome
```

### SGX 模式额外依赖（可选）
- Intel SGX SDK
- Gramine 1.8+

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/Smart-Yanmeng/Beat-LocalCoin-SGX.git
cd Beat-LocalCoin-SGX
```

### 2. 生成密钥

#### 生成阈值签名密钥（4节点，阈值2）
```bash
python3 -m adaptive.commoncoin.thresprf 4 2 > thsig4_1.keys
```

#### 生成 ECDSA 密钥
```bash
python3 -m adaptive.ecdsa.generate_keys_ecdsa 4 ecdsa.keys
```

#### 生成阈值加密密钥（4节点，阈值2）
```bash
python3 -m adaptive.threshenc.tdh2 4 2 > thenc4_1.keys
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

| 参数 | 说明 | 示例 |
|------|------|------|
| `-k` | 阈值签名密钥文件路径 | `-k thsig4_1.keys` |
| `-e` | ECDSA 密钥文件路径 | `-e ecdsa.keys` |
| `-c` | 阈值加密密钥文件路径 | `-c thenc4_1.keys` |
| `-n` | 节点总数 | `-n 4` |
| `-t` | 容忍的恶意节点数 | `-t 1` |
| `-b` | 每轮提议的交易数量 | `-b 100` |
| `-v` | 二进制共识版本（分布式模式） | `-v 1` |
| `--my-id` | 当前节点 ID（分布式模式） | `--my-id 0` |
| `-s` | 主机列表文件（分布式模式） | `-s hosts` |

## 项目结构

```
Beat-LocalCoin-SGX/
├── adaptive/
│   ├── commoncoin/     # 阈值签名和公共硬币协议
│   ├── core/           # 核心共识协议实现
│   ├── ecdsa/          # ECDSA 签名模块
│   ├── sgx/            # SGX 相关代码（可选）
│   ├── test/           # 测试脚本
│   └── threshenc/      # 阈值加密模块
├── LICENSE
└── README.md
```

## 致谢

本项目基于 [HoneyBadgerBFT](https://github.com/amiller/HoneyBadgerBFT) 项目开发。

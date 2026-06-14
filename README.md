# BEAT-LOCAL-COIN ( None-SGX )

> CODE BASED ON ***HONEYBADGER*** PROJECT [> LINK <](https://github.com/amiller/HoneyBadgerBFT)

## 版本说明

本分支 (`Beat-Localcoin-None-SGX`) 移除了 SGX socket 通信层，将加密逻辑直接内联到协议模块中运行。无需启动独立的 SGX 服务器进程，加密操作在协议执行时直接完成。

### 相比 SGX 版本的变更

- 删除所有 SGX socket 服务端/客户端代码（端口 65430-65437）
- 将 RSA/AES 加密逻辑内联到 `broadcasts.py` 和 `includeTransaction.py`
- 用纯 Python `ecdsa` 包替代 OpenSSL ctypes（兼容 OpenSSL 3.x）
- 修复 Python 3.9+ 兼容性问题（`encodestring` → `encodebytes` 等）
- 分布式测试改用直连 socket（移除 Tor/socks 依赖）

## 环境要求

### Python 版本

- **最低要求**: Python 3.8+
- **测试通过**: Python 3.10（服务器）、Python 3.12（本地）

### 依赖

```bash
pip install gevent cryptography charm-crypto-framework pycryptodome ecdsa
```

| 依赖 | 版本 | 用途 |
|------|------|------|
| gevent | 24.2.1 | 协程并发 |
| cryptography | 3.4.8+ | RSA/AES 加密 |
| charm-crypto-framework | 0.62+ | 门限密码学（椭圆曲线） |
| pycryptodome | 3.10+ | AES 加密 |
| ecdsa | 0.19.2 | ECDSA 签名（纯 Python，兼容 OpenSSL 3.x） |

## 密钥文件

运行前需生成三类密钥（或使用仓库中的示例密钥）：

```bash
# 生成 4 节点密钥（N=4, k=2）
python3 generate_keys.py 4 2

# 生成 16 节点密钥（N=16, k=5）
python3 generate_keys.py 16 5
```

生成的文件：
- `thsigN.keys` — 门限签名密钥
- `thencNkeys` — 门限加密密钥
- `ecdsaN.keys` — ECDSA 密钥

## 快速开始

### 单机模式

```bash
python3 -m adaptive.test.honest_party_test \
    -k thsig4_1.keys -e ecdsa.keys -b 100 -n 4 -t 1 -c thenc4_1.keys
```

### 分布式模式

1. 将代码部署到所有服务器
2. 在每台服务器上运行（指定不同的 `--my-id`）：

```bash
# 服务器 0
python3 -m adaptive.test.honest_party_test_EC2 \
    -k thsig4_1.keys -e ecdsa.keys -c thenc4_1.keys \
    -s hosts -n 4 -t 1 -b 100 -v 1 --my-id 0

# 服务器 1
python3 -m adaptive.test.honest_party_test_EC2 \
    -k thsig4_1.keys -e ecdsa.keys -c thenc4_1.keys \
    -s hosts -n 4 -t 1 -b 100 -v 1 --my-id 1

# ...以此类推
```

`hosts` 文件格式：每行一个服务器 IP。

### 参数说明

| 参数 | 说明 |
|------|------|
| `-k` | 门限签名密钥文件 |
| `-e` | ECDSA 密钥文件 |
| `-c` | 门限加密密钥文件 |
| `-n` | 节点总数 |
| `-t` | 容错阈值（需满足 N > 3t） |
| `-b` | 每轮提议的交易数量 |
| `-v` | 共识版本号 |
| `--my-id` | 当前节点 ID（分布式模式） |
| `-s` | 服务器 IP 列表文件（分布式模式） |

## 测试结果

### 单机模式

| N | t | B | 耗时 | 同步交易数 |
|---|---|---|------|-----------|
| 4 | 1 | 100 | 0.09s | 54/100 |
| 4 | 1 | 100000 | 2.1s | 68,391/100,000 |
| 16 | 5 | 100 | ~26s | 54/100 |

### 分布式模式（4 台阿里云服务器）

| N | t | B | 耗时 | 同步交易数 |
|---|---|---|------|-----------|
| 4 | 1 | 100 | 0.06-0.12s | 59/100 |
| 4 | 1 | 100000 | ~155s | 43,731/100,000 |

## 项目结构

```
adaptive/
├── core/           # 共识协议核心
│   ├── broadcasts.py        # 可靠广播、二进制共识
│   ├── includeTransaction.py # 交易包含协议
│   ├── bkr_acs.py           # ACS 原子公共子集
│   └── utils.py             # 工具函数
├── commoncoin/     # 共同币协议（门限 PRF）
├── ecdsa/          # ECDSA 签名
├── sgx/            # 加密工具（cryptor + 密钥文件）
├── threshenc/      # 门限加密（TDH2）
└── test/           # 测试脚本
```

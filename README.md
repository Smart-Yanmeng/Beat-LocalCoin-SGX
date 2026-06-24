# BEAT-LOCAL-COIN ( Original Python 3 Version )

> 基于 [HoneyBadgerBFT](https://github.com/amiller/HoneyBadgerBFT) 项目的改进实现

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## 版本说明

本分支 (`Beat-Origin-PY3`) 是原始的 Python 3 版本实现，包含完整的 BEAT0 协议代码和基准测试结果。

### 分支特点

- 包含完整的 BEAT0 协议实现（`BEAT0/` 目录）
- 包含多个基准测试结果文件
- 支持 4 节点和 16 节点配置
- 提供密钥生成和验证工具

## 项目结构

```
Beat-LocalCoin-SGX/
├── BEAT0/                    # 原始 BEAT 协议实现
│   └── BEAT/
│       ├── core/             # 核心共识协议
│       ├── commoncoin/       # 共同币协议
│       ├── ecdsa/            # ECDSA 签名
│       ├── threshenc/        # 门限加密
│       └── test/             # 测试脚本
├── adaptive/                 # 改进的自适应版本
├── benchmark_*.csv           # 基准测试结果
├── generate_keys.py          # 密钥生成工具
├── verify_keys.py            # 密钥验证工具
├── verify_keys_deep.py       # 深度密钥验证
├── LICENSE
└── README.md
```

## 环境要求

### Python 版本

- **最低要求**: Python 3.8
- **推荐**: Python 3.10+

### 依赖

```bash
pip install gevent charm-crypto pycryptodome ecdsa
```

## 快速开始

### 1. 生成密钥

#### 生成 4 节点密钥
```bash
python3 generate_keys.py 4 2
```

#### 生成 16 节点密钥
```bash
python3 generate_keys.py 16 5
```

### 2. 验证密钥

```bash
python3 verify_keys.py
python3 verify_keys_deep.py
```

### 3. 运行测试

#### 使用 BEAT0 原始版本

```bash
cd BEAT0/BEAT
python3 -m test.honest_party_test \
    -k ../../thsig4.keys \
    -e ../../ecdsa.keys \
    -c ../../thenc4.keys \
    -n 4 -t 1 -b 100
```

#### 使用 adaptive 改进版本

```bash
python3 -m adaptive.test.honest_party_test \
    -k thsig4_1.keys \
    -e ecdsa.keys \
    -c thenc4_1.keys \
    -n 4 -t 1 -b 100
```

### 4. 查看基准测试结果

```bash
cat benchmark_all.csv
cat benchmark_none_sgx_vs_beat.csv
```

## 命令参数说明

### 基础参数（单机/分布式模式通用）

| 参数 | 长参数 | 说明 | 默认值 | 示例 |
|------|--------|------|--------|------|
| `-k` | `--threshold-keys` | 门限签名密钥文件路径 | 无（必填） | `-k thsig4.keys` |
| `-e` | `--ecdsa-keys` | ECDSA 签名密钥文件路径 | 无（必填） | `-e ecdsa.keys` |
| `-c` | `--threshold-enc` | 门限加密密钥文件路径 | 无（必填） | `-c thenc4.keys` |
| `-n` | `--number` | 节点总数 N | 无（必填） | `-n 4` |
| `-t` | `--tolerance` | 容忍的拜占庭恶意节点数 t（需满足 N > 3t） | 无（必填） | `-t 1` |
| `-b` | `--propose-size` | 每轮提议的交易数量 B | `ceil(N * ln(N))` | `-b 100` |
| `-x` | `--transactions` | 每个节点提议的总交易数 TX | 等于 B | `-x 1000` |

### 分布式模式专用参数（honest_party_test_EC2）

| 参数 | 长参数 | 说明 | 默认值 | 示例 |
|------|--------|------|--------|------|
| `-s` | `--hosts` | 服务器 IP 列表文件路径 | `~/hosts` | `-s hosts7` |
| `-a` | `--negotiated-time` | 协议同步启动时间（Unix 时间戳） | `50` | `-a 1688888888` |
| | `--my-id` | 当前节点的 ID（0 到 N-1） | `0` | `--my-id 3` |
| `-p` | `--tx-path` | 交易集文件路径 | `tx` | `-p tx` |

### 参数详解

#### 密钥文件参数 (`-k`, `-e`, `-c`)

这三类密钥是协议运行的必要输入：

- **`-k thsigN.keys`**：门限签名密钥，用于共识过程中的阈值签名。文件格式为 6 元组 `(N, t, sVK, sVKs, SKs, gg)`，由 `generate_keys.py` 生成。
- **`-e ecdsaN.keys`**：ECDSA 签名密钥，用于节点身份验证。每个节点一个 32 字节私钥。
- **`-c thencN.keys`**：门限加密密钥，用于交易内容的加密保护。文件格式为 5 元组 `(N, t, sVK, sVKs, SKs)`。

#### 节点参数 (`-n`, `-t`)

- **`-n N`**：参与共识的节点总数。决定了网络的规模和容错能力。
- **`-t t`**：系统可容忍的恶意节点数量。必须满足 `N > 3t`（拜占庭容错条件）。
  - N=4, t=1：可容忍 1 个恶意节点
  - N=7, t=2：可容忍 2 个恶意节点
  - N=16, t=5：可容忍 5 个恶意节点

#### 交易参数 (`-b`, `-x`)

- **`-b B`**：每轮共识提议的交易数量。影响单轮共识的吞吐量和耗时。
  - 较小的 B（如 10-100）：快速完成，适合测试
  - 较大的 B（如 10000-100000）：更接近真实负载，测量最大吞吐量
- **`-x TX`**：每个节点总共提议的交易数。默认等于 B，即只运行一轮。设置更大值可测试多轮共识。

#### 分布式参数 (`-s`, `-a`, `--my-id`)

- **`-s hosts`**：服务器 IP 列表文件，每行一个 IP 地址。节点按文件顺序分配 ID（0, 1, 2, ...）。
- **`-a TIMESTAMP`**：协议同步启动时间。所有节点在此时间戳同时开始共识，确保公平测试。
- **`--my-id ID`**：指定当前进程代表的节点 ID。分布式部署时，每台服务器运行相同命令但使用不同的 `--my-id`。

### 示例命令

#### 单机模式（4 节点）

```bash
python3 -m BEAT0.BEAT.test.honest_party_test \
    -k thsig4.keys \
    -e ecdsa.keys \
    -c thenc4.keys \
    -n 4 -t 1 -b 100
```

#### 分布式模式（7 节点）

```bash
# 在每台服务器上运行，指定不同的 --my-id
python3 -m BEAT0.BEAT.test.honest_party_test_EC2 \
    -k thsig7.keys \
    -e ecdsa7.keys \
    -c thenc7.keys \
    -s hosts7 \
    -n 7 -t 2 -b 1000 \
    -a 1688888888 \
    --my-id 0  # 其他服务器改为 1, 2, 3, 4, 5, 6
```

## 致谢

本项目基于 [HoneyBadgerBFT](https://github.com/amiller/HoneyBadgerBFT) 项目开发。

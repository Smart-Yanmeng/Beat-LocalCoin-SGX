# BEAT-LOCAL-COIN ( Python 3 LocalCoin Version )

> 基于 [HoneyBadgerBFT](https://github.com/amiller/HoneyBadgerBFT) 项目的改进实现，支持本地币（LocalCoin）模拟

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## 版本说明

本分支 (`Beat-Localcoin-PY3`) 是 LocalCoin 版本的 Python 3 实现，包含完整的 BEAT 协议代码、Simulator 模拟器和基准测试结果。

### 分支特点

- 包含完整的 BEAT 协议实现（`BEAT0/` 和 `adaptive/` 目录）
- 包含 Simulator 模拟器（`Simulator/` 目录）
- 支持 4 节点和 7 节点配置
- 提供密钥生成和验证工具
- 包含运行脚本（`run.sh`, `run_beat7.py`, `run_beat7.sh`, `start.sh`）

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
├── Simulator/                # 模拟器
├── log/                      # 日志目录
├── benchmark_*.csv           # 基准测试结果
├── generate_keys.py          # 密钥生成工具
├── verify_keys.py            # 密钥验证工具
├── verify_keys_deep.py       # 深度密钥验证
├── run.sh                    # 运行脚本
├── run_beat7.py              # 7节点运行脚本
├── run_beat7.sh              # 7节点Shell脚本
├── start.sh                  # 启动脚本
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

#### 生成 7 节点密钥
```bash
python3 generate_keys.py 7 2
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

### 4. 使用运行脚本

#### 运行 4 节点版本
```bash
./start.sh 4 1 10 1
```

#### 运行 7 节点版本
```bash
./run_beat7.sh
```

### 5. 查看基准测试结果

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

#### 交易参数 (`-b`, `-x`)

- **`-b B`**：每轮共识提议的交易数量。影响单轮共识的吞吐量和耗时。
  - 较小的 B（如 10-100）：快速完成，适合测试
  - 较大的 B（如 10000-100000）：更接近真实负载，测量最大吞吐量
- **`-x TX`**：每个节点总共提议的交易数。默认等于 B，即只运行一轮。设置更大值可测试多轮共识。

### 示例命令

#### 单机模式（4 节点）

```bash
python3 -m BEAT0.BEAT.test.honest_party_test \
    -k thsig4.keys \
    -e ecdsa.keys \
    -c thenc4.keys \
    -n 4 -t 1 -b 100
```

#### 使用 start.sh 脚本（4 节点）

```bash
./start.sh 4 1 10 1
```

#### 使用 run_beat7.sh 脚本（7 节点）

```bash
./run_beat7.sh
```

## 致谢

本项目基于 [HoneyBadgerBFT](https://github.com/amiller/HoneyBadgerBFT) 项目开发。

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

- **最低要求**: Python 3.8+
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

| 参数 | 说明 | 示例 |
|------|------|------|
| `-k` | 门限签名密钥文件 | `-k thsig4.keys` |
| `-e` | ECDSA 密钥文件 | `-e ecdsa.keys` |
| `-c` | 门限加密密钥文件 | `-c thenc4.keys` |
| `-n` | 节点总数 | `-n 4` |
| `-t` | 容忍的恶意节点数 | `-t 1` |
| `-b` | 每轮提议的交易数量 | `-b 100` |

## 基准测试结果

本分支包含多个基准测试结果文件：

- `benchmark_all.csv` - 完整基准测试结果
- `benchmark_none_sgx_vs_beat.csv` - None-SGX 与 BEAT 对比
- `benchmark_results.csv` - 测试结果汇总
- `benchmark_results.txt` - 测试结果文本
- `benchmark_small_b.csv` - 小规模 B 值测试
- `benchmark_small_b_all.csv` - 小规模 B 值完整测试

## 致谢

本项目基于 [HoneyBadgerBFT](https://github.com/amiller/HoneyBadgerBFT) 项目开发。

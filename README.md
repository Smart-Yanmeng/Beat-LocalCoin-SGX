# ACS (Asynchronous Consensus System)

> 基于论文 "Asynchronous Consensus without Trusted Setup or Public-Key Cryptography" 的原型实现

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## 项目简介

本项目实现了一种无需可信设置或公钥密码学的异步共识协议。基于 [htadkg](https://github.com/sourav1547/htadkg) 项目开发，复用了网络通信、可靠广播协议、群组运算等实现。

### 分支特点

- 实现 VABA（Verifiable Asynchronous Byzantine Agreement）协议
- 包含 ADKG（Asynchronous Distributed Key Generation）模块
- 支持 ASKS 签名方案
- 提供本地测试和 AWS 部署支持

## 项目结构

```
Beat-LocalCoin-SGX/
├── adkg/                       # 核心协议实现
│   ├── vaba.py                 # VABA 协议（核心）
│   ├── asks.py                 # ASKS 签名方案
│   └── ...
├── pairing/                    # 双线性配对实现
├── tests/                      # 测试代码
├── scripts/                    # 运行脚本
├── conf/                       # 配置文件
├── aws/                        # AWS 部署脚本
├── benchmark/                  # 基准测试
├── results/                    # 测试结果
├── Dockerfile                  # Docker 镜像
├── docker-compose.yml          # Docker Compose 配置
├── Makefile                    # 构建脚本
├── setup.py                    # Python 安装脚本
├── pytest.ini                  # pytest 配置
├── acs_run.sh                  # ACS 运行脚本
├── acs_run_node.sh             # 节点运行脚本
├── run_*.sh                    # 各种运行脚本
├── LICENSE
└── README.md
```

## 环境要求

### Python 版本

- **最低要求**: Python 3.8

### 依赖

```bash
pip install -e .
```

或使用 Docker：

```bash
docker-compose build vaba
```

## 快速开始

### 方式一：使用 Docker（推荐）

#### 1. 构建镜像

```bash
docker-compose build vaba
```

#### 2. 启动容器

```bash
docker-compose run --rm vaba bash
```

#### 3. 运行测试（单机多线程）

```bash
pytest tests/test_vaba.py -o log_cli=true --num 4 --ths 1
```

#### 4. 运行测试（多进程）

```bash
# 生成配置文件
python gen_config.py

# 启动 VABA 实例
bash scripts/run_vaba.sh 4
```

### 方式二：本地运行

#### 1. 安装依赖

```bash
pip install -e .
```

#### 2. 运行测试

```bash
pytest tests/test_vaba.py -o log_cli=true --num 4 --ths 1
```

## 命令参数说明

### 测试参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--num` | 节点总数 N | `--num 4` |
| `--ths` | 容忍的恶意节点数 t（需满足 N > 3t） | `--ths 1` |

### 参数详解

#### 节点参数 (`--num`, `--ths`)

- **`--num N`**：参与共识的节点总数。决定了网络的规模和容错能力。
- **`--ths t`**：系统可容忍的恶意节点数量。必须满足 `N > 3t`（拜占庭容错条件）。
  - N=4, t=1：可容忍 1 个恶意节点
  - N=7, t=2：可容忍 2 个恶意节点
  - N=10, t=3：可容忍 3 个恶意节点

### 示例命令

#### 单机测试（4 节点）

```bash
pytest tests/test_vaba.py -o log_cli=true --num 4 --ths 1
```

#### 使用运行脚本

```bash
# 运行 ACS 协议
./acs_run.sh

# 运行节点
./acs_run_node.sh
```

## AWS 部署

请参考 `aws/README.md` 了解如何在 AWS 上部署协议。

## 致谢

本项目基于 [htadkg](https://github.com/sourav1547/htadkg) 项目开发。

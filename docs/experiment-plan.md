# TruBFT 拜占庭容错实验计划

## 实验目标

验证 TruBFT 协议在 N=4, t=1 配置下对两种拜占庭行为的容忍能力。

## 实验环境

- 4 个 Docker 容器，每个容器运行 1 个节点
- 节点 ID: 0, 1, 2, 3
- 共同参数: N=4, T=1, B=100（每轮提议 100 笔交易）
- 密钥: thsig4_1.keys / ecdsa.keys / thenc4_1.keys

## 实验矩阵

| 实验 | 拜占庭节点 | 拜占庭类型 | 预期结果 |
|------|-----------|-----------|---------|
| Baseline | 无 | 诚实 | 4 节点全部完成共识 |
| Exp-1 | Node 3 | 崩溃（握手后退出） | 3 个诚实节点完成共识 |
| Exp-2 | Node 3 | 投 0（始终投 0） | 3 个诚实节点完成共识 |

## 实验步骤

### Baseline: 全诚实节点

```bash
# 构建镜像
docker build -t trubft:TruBFT .

# 启动 4 个诚实节点
docker-compose -f docker-compose.byzantine.yml up \
  trubft-node-0 trubft-node-1 trubft-node-2 trubft-node-3

# 注意：需要先把 Node 3 的 TRUBFT_MODE 改为 distributed
```

**观察指标:**
- 4 个节点是否全部输出 "Consensus Finished"
- 每个节点的 "Finishing Time" 耗时
- 交易同步数量是否一致

### Exp-1: 崩溃拜占庭

```bash
# Node 3 使用 TRUBFT_MODE=byzantine（默认配置即可）
docker-compose -f docker-compose.byzantine.yml up
```

**观察指标:**
- Node 3 是否输出 "CRASHING NOW!" 后退出
- Node 0, 1, 2 是否仍然完成共识
- Node 0, 1, 2 的 Finishing Time 是否合理（不应无限等待）
- 每个诚实节点同步的交易数量是否相同

### Exp-2: 投 0 拜占庭

```bash
# 修改 docker-compose.byzantine.yml 中 Node 3:
#   TRUBFT_MODE=byzantine-vote
docker-compose -f docker-compose.byzantine.yml up
```

**观察指标:**
- Node 3 是否保持运行（不崩溃）
- Node 3 是否输出 "BYZANTINE VOTE" 日志
- Node 0, 1, 2 是否完成共识
- 共识结果中包含的交易数量（投 0 会减少被接受的提案数）
- 是否有异常/超时/死锁

## 预期行为分析

### N=4, t=1 的 BFT 保证

- 可靠广播需要 N-t = 3 个 echo/ready → 3 个诚实节点足够
- 二元共识多数决需要 >N/2 = 2 个一致 → 3 个诚实节点足够
- ACS 终止需要 N-t = 3 个决策 → 3 个诚实节点足够
- 交易解密需要 N-2t = 2 个解密份额 → 3 个诚实节点足够

### Exp-1（崩溃）预期

Node 3 崩溃后，TCP 连接断开。诚实节点的可靠广播仍能收集到 3 个 echo/ready，共识正常完成。Node 3 的提案因没有收到足够的 ready 而被排除。

### Exp-2（投 0）预期

Node 3 正常参与所有消息交换，但在二元共识中始终投 0。对于 Node 3 自己的提案：
- Node 3 投 0，Node 0/1/2 投 1（因为他们收到了提案）
- 3:1 多数 → 提案仍可能被接受（取决于具体轮次的 coin 值）

对于其他节点的提案：
- Node 3 投 0，提案方投 1
- 如果另外 2 个诚实节点也投 1 → 3:1 → 接受
- 结论：投 0 行为的实际影响可能有限，因为 N-t=3 个诚实节点的投票已经够了

## 验收标准

| 实验 | 成功条件 |
|------|---------|
| Baseline | 4 节点全部完成，交易数一致 |
| Exp-1 | 3 个诚实节点完成，无死锁 |
| Exp-2 | 3 个诚实节点完成，无死锁，Node 3 保持运行 |

## 执行顺序

1. Baseline → 确认正常流程
2. Exp-1 → 验证崩溃容错
3. Exp-2 → 验证恶意投票容错

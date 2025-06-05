import random
from typing import List, Tuple


# 模拟候选人信息结构
class Candidate:
    def __init__(self, id, sgx_ver, cpu, ram, bw, lat):
        self.id = id
        self.sgx_ver = sgx_ver
        self.cpu = cpu
        self.ram = ram
        self.bw = bw
        self.lat = lat
        self.score = 0
        self.valid = False

    def __repr__(self):
        return f"Candidate(id={self.id}, score={self.score:.2f}, valid={self.valid})"


# 参数权重（可以根据实际需求调整）
w1, w2, w3, w4 = 0.3, 0.3, 0.2, 0.2


# 步骤 1：广播任务，收集候选人资料
def start_crowdsourcing(n: int, task_id: str) -> List[Candidate]:
    print(f"Broadcasting task {task_id} to server providers...")
    candidates = []
    for i in range(10):  # 假设收到 10 个候选者
        candidate = Candidate(
            id=f"node_{i}",
            sgx_ver=random.choice(["v1", "v2", "v3"]),
            cpu=random.uniform(2, 8),  # GHz
            ram=random.uniform(4, 32),  # GB
            bw=random.uniform(50, 1000),  # Mbps
            lat=random.uniform(5, 100)  # ms
        )
        candidates.append(candidate)
    return evaluate_candidates(candidates, n)


# 步骤 2：评估候选人
def evaluate_candidates(candidates: List[Candidate], n: int) -> List[Candidate]:
    for c in candidates:
        c.score = w1 * c.cpu + w2 * c.ram + w3 * c.bw - w4 * c.lat
    sorted_candidates = sorted(candidates, key=lambda c: c.score, reverse=True)
    print("Top candidates selected:")
    for c in sorted_candidates[:n]:
        print(c)
    return sorted_candidates[:n]


# 步骤 3：远程认证
def remote_attestation(tcn_candidates: List[Candidate], required: int = 4) -> List[Candidate]:
    valid_tcns = []
    for c in tcn_candidates:
        if len(valid_tcns) >= required:
            break
        print(f"Attesting {c.id}...")
        # 模拟 AR 生成与 IAS 验证（80% 成功率）
        approved = random.random() < 0.8
        if approved:
            c.valid = True
            print(f"{c.id} attestation approved.")
            valid_tcns.append(c)
        else:
            print(f"{c.id} attestation failed.")
    return valid_tcns


# 步骤 4：绑定 DDS
def bind_dds(dds_list: List[str], valid_tcns: List[Candidate]):
    for dds, tcn in zip(dds_list, valid_tcns):
        print(f"Binding TCN {tcn.id} to DDS {dds}...")


# 主流程模拟
def main():
    task_id = "task_001"
    n = 5  # 选择前 5 个候选人
    dds_list = [f"DDS_{i}" for i in range(n)]

    tcn_candidates = start_crowdsourcing(n, task_id)
    valid_tcns = remote_attestation(tcn_candidates, required=4)
    bind_dds(dds_list, valid_tcns)


if __name__ == "__main__":
    main()

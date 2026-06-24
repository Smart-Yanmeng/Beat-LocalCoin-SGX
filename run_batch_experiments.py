#!/usr/bin/env python3
"""
Batch experiment runner for Dumbo and Beat-LocalCoin on 4 remote servers.

For each protocol and each B value:
  1. Clean old logs/processes
  2. Launch node on each of 4 servers (background SSH)
  3. Poll for completion
  4. Collect time/tx-delivered from each node's log
  5. Append rows to combined CSV files (one per protocol)

Run:
  python3 run_batch_experiments.py [--protocols dumbo,beat] [--b-list 10,100,...]
"""

import argparse
import csv
import os
import subprocess
import sys
import time
from datetime import datetime

# ============================================================
# Configuration
# ============================================================
PASS = 'York@233'
SERVERS = [
    "120.27.215.50",
    "116.62.149.8",
    "47.98.121.97",
    "116.62.240.167",
    "121.43.234.253",
    "121.199.72.252",
    "121.40.130.83",
]
N = 7
F = 2

DUMBO_REMOTE_DIR = "/root/dumbo"
BEAT_REMOTE_DIR = "/root/beat-localcoin"

# Where output CSVs land locally
OUT_DIR = os.path.dirname(os.path.abspath(__file__))
DUMBO_CSV = os.path.join(OUT_DIR, "dumbo_results.csv")
BEAT_CSV = os.path.join(OUT_DIR, "beat_results.csv")

DEFAULT_B_LIST = [10, 100, 250, 500, 750, 1000, 2500, 5000, 7500,
                  10000, 25000, 50000, 75000, 100000]


# ============================================================
# SSH helpers (subprocess based, sshpass + ssh -o opts)
# ============================================================
SSH_OPTS = [
    "-o", "StrictHostKeyChecking=no",
    "-o", "ConnectTimeout=15",
    "-o", "ServerAliveInterval=30",
]


def ssh_run(host, cmd, capture=True, timeout=60):
    """Run a command on a remote host. Returns (returncode, stdout, stderr)."""
    args = ["sshpass", "-p", PASS, "ssh"] + SSH_OPTS + [f"root@{host}", cmd]
    try:
        r = subprocess.run(args, capture_output=capture, text=True, timeout=timeout)
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "timeout"


def ssh_run_async_detached(host, cmd):
    """Fire-and-forget SSH that starts a detached process on remote."""
    # Wrap in nohup ... & disown so the remote shell returns immediately
    full = f"nohup bash -c '{cmd}' </dev/null >/dev/null 2>&1 & disown"
    args = ["sshpass", "-p", PASS, "ssh", "-f"] + SSH_OPTS + [f"root@{host}", full]
    subprocess.run(args, timeout=15)


def launch_all_parallel(host_cmds):
    """Launch commands on multiple hosts as simultaneously as possible.

    host_cmds: list of (host, cmd). Uses threads so all SSH connections
    fire at the same time, minimizing start-time skew between nodes.
    """
    import threading
    threads = []
    for host, cmd in host_cmds:
        t = threading.Thread(target=ssh_run_async_detached, args=(host, cmd))
        threads.append(t)
    for t in threads:
        t.start()
    for t in threads:
        t.join()


def cleanup_all(remote_dir, kill_pattern, kill_port=None):
    """Clean logs, kill processes, free port on all servers. Verify processes gone."""
    print(f"  [cleanup] {remote_dir}")
    for host in SERVERS:
        cmds = [
            f"pkill -9 -f {kill_pattern} 2>/dev/null",
            f"rm -f {remote_dir}/log/consensus-node-*.log",
            f"rm -f {remote_dir}/beat-node-*.log",
            f"rm -f {remote_dir}/results.csv",
            f"rm -f /tmp/node-*.out /tmp/beat-*.out",
        ]
        if kill_port:
            cmds.append(f"fuser -k {kill_port}/tcp 2>/dev/null")
        ssh_run(host, "; ".join(cmds) + "; true", timeout=20)
    # Give the OS time to fully reap processes and release sockets
    time.sleep(5)
    # Verify no leftover processes; retry kill if needed
    for host in SERVERS:
        rc, out, _ = ssh_run(
            host,
            f"pgrep -f {kill_pattern} | wc -l",
            timeout=10,
        )
        try:
            n = int(out.strip())
        except Exception:
            n = 0
        if n > 0:
            print(f"    [cleanup] {host} still has {n} procs, force-killing again")
            ssh_run(host, f"pkill -9 -f {kill_pattern} 2>/dev/null; true", timeout=10)
            time.sleep(3)


def collect_time_dumbo(host, node_id):
    """Parse dumbo log to get total time. Returns (time_sec, total_txs) or (None, None)."""
    cmd = f"grep 'breaks in' {DUMBO_REMOTE_DIR}/log/consensus-node-{node_id}.log 2>/dev/null | tail -1"
    rc, out, _ = ssh_run(host, cmd, timeout=15)
    # Format: "node X breaks in Y seconds with total delivered Txs Z"
    if "breaks in" in out:
        try:
            t = float(out.split("breaks in")[1].split("seconds")[0].strip())
            txs = int(out.split("delivered Txs")[1].strip().rstrip())
            return t, txs
        except Exception:
            return None, None
    return None, None


def collect_time_beat(host, node_id):
    """Parse beat log to get finishing time. Returns (time_sec, total_txs) or (None, None)."""
    cmd = (
        f"grep -E 'Finishing Time {node_id}' {BEAT_REMOTE_DIR}/beat-node-{node_id}.log 2>/dev/null | tail -1; "
        f"echo ::; "
        f"grep -E 'distinct tx synced' {BEAT_REMOTE_DIR}/beat-node-{node_id}.log 2>/dev/null | tail -1"
    )
    rc, out, _ = ssh_run(host, cmd, timeout=15)
    parts = out.split("::")
    if len(parts) != 2:
        return None, None
    fin_line, tx_line = parts[0], parts[1]
    t = None
    txs = None
    if "Finishing Time" in fin_line:
        try:
            t = float(fin_line.split(",")[-1].strip())
        except Exception:
            pass
    if "distinct tx" in tx_line:
        try:
            # "[X] N distinct tx synced and ..."
            after = tx_line.split("]", 1)[1].strip()
            txs = int(after.split()[0])
        except Exception:
            pass
    return t, txs


def append_csv(path, rows, header):
    """Append rows to CSV, write header if file doesn't exist."""
    new_file = not os.path.exists(path)
    with open(path, "a", newline="") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow(header)
        for r in rows:
            w.writerow(r)


# ============================================================
# Per-protocol run
# ============================================================
def run_protocol_one(protocol, B, K=1, max_wait=900):
    """Run any protocol with batch=B, K rounds."""
    print(f"  [{protocol} B={B}] starting")
    cleanup_all(DUMBO_REMOTE_DIR, "[r]un_socket_node.py")
    time.sleep(2)

    # Start all nodes in parallel (minimize start-time skew)
    host_cmds = []
    for i, host in enumerate(SERVERS):
        cmd = (
            f"export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH && "
            f"cd {DUMBO_REMOTE_DIR} && "
            f"nohup ./start_node.sh {i} {protocol} {B} {K} </dev/null > /tmp/node-{i}.out 2>&1 &"
        )
        host_cmds.append((host, cmd))
    launch_all_parallel(host_cmds)

    # Poll for completion
    start = time.time()
    poll_interval = 5
    last_print = 0
    # If 3/4 are done, wait at most STRAGGLER_GRACE more seconds for the 4th
    straggler_grace = 180
    three_done_at = None
    while time.time() - start < max_wait:
        time.sleep(poll_interval)
        finished_count = 0
        for i, host in enumerate(SERVERS):
            rc, out, _ = ssh_run(
                host,
                f"grep -c 'breaks in' {DUMBO_REMOTE_DIR}/log/consensus-node-{i}.log 2>/dev/null || echo 0",
                timeout=10,
            )
            try:
                if int(out.strip()) >= 1:
                    finished_count += 1
            except Exception:
                pass
        elapsed = int(time.time() - start)
        if elapsed - last_print >= 20:
            print(f"    waiting... {elapsed}s, finished={finished_count}/{N}")
            last_print = elapsed
        if finished_count >= N:
            break
        if finished_count >= N - 1:
            if three_done_at is None:
                three_done_at = time.time()
                print(f"    {finished_count}/{N} done, giving straggler {straggler_grace}s grace")
            elif time.time() - three_done_at > straggler_grace:
                print(f"    straggler timeout, moving on with {finished_count}/{N}")
                break

    # Collect results
    rows = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for i, host in enumerate(SERVERS):
        t, txs = collect_time_dumbo(host, i)
        rows.append([timestamp, protocol, N, F, B, K, i, host, t, txs])
        print(f"    node {i}: time={t}, tx={txs}")

    # Force kill stragglers so port stays clean for next run
    for host in SERVERS:
        ssh_run(host, "pkill -9 -f '[r]un_socket_node.py' 2>/dev/null; true", timeout=10)
    return rows


def run_beat_one(B, max_wait=900):
    """Run beat-localcoin with batch=B. Wait until all 4 nodes finish or timeout."""
    print(f"  [beat B={B}] starting")
    cleanup_all(BEAT_REMOTE_DIR, "[h]onest_party_test", kill_port=49500)
    time.sleep(2)

    host_cmds = []
    for i, host in enumerate(SERVERS):
        cmd = (
            f"export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH && "
            f"cd {BEAT_REMOTE_DIR} && "
            f"nohup ./start_node.sh {i} {B} </dev/null > /tmp/beat-{i}.out 2>&1 &"
        )
        host_cmds.append((host, cmd))
    launch_all_parallel(host_cmds)

    start = time.time()
    poll_interval = 5
    last_print = 0
    straggler_grace = 60
    three_done_at = None
    while time.time() - start < max_wait:
        time.sleep(poll_interval)
        finished_count = 0
        for i, host in enumerate(SERVERS):
            rc, out, _ = ssh_run(
                host,
                f"grep -c 'Finishing Time {i}' {BEAT_REMOTE_DIR}/beat-node-{i}.log 2>/dev/null || echo 0",
                timeout=10,
            )
            try:
                if int(out.strip()) >= 1:
                    finished_count += 1
            except Exception:
                pass
        elapsed = int(time.time() - start)
        if elapsed - last_print >= 20:
            print(f"    waiting... {elapsed}s, finished={finished_count}/{N}")
            last_print = elapsed
        if finished_count >= N:
            break
        if finished_count >= N - 1:
            if three_done_at is None:
                three_done_at = time.time()
                print(f"    {finished_count}/{N} done, giving straggler {straggler_grace}s grace")
            elif time.time() - three_done_at > straggler_grace:
                print(f"    straggler timeout, moving on with {finished_count}/{N}")
                break

    rows = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for i, host in enumerate(SERVERS):
        t, txs = collect_time_beat(host, i)
        rows.append([timestamp, "beat", N, F, B, 1, i, host, t, txs])
        print(f"    node {i}: time={t}, tx={txs}")

    # Always kill remaining python processes so port 49500 frees up before next run
    for host in SERVERS:
        ssh_run(host, "fuser -k 49500/tcp 2>/dev/null; pkill -9 -f '[h]onest_party_test' 2>/dev/null; true", timeout=15)
    return rows


# ============================================================
# Main
# ============================================================
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocols", default="dumbo,beat",
                        help="comma-separated: dumbo, beat")
    parser.add_argument("--b-list", default=",".join(str(b) for b in DEFAULT_B_LIST),
                        help="comma-separated B values")
    args = parser.parse_args()

    protocols = [p.strip() for p in args.protocols.split(",") if p.strip()]
    b_list = [int(b.strip()) for b in args.b_list.split(",") if b.strip()]

    header = ["timestamp", "protocol", "N", "f", "B", "K",
              "replica", "host", "time_sec", "txs_delivered"]

    print(f"Protocols: {protocols}")
    print(f"B values:  {b_list}")
    print(f"Total runs: {len(protocols) * len(b_list)}")
    print(f"Output:    {DUMBO_CSV}, {BEAT_CSV}")
    print()

    overall_start = time.time()

    for proto in protocols:
        print(f"\n=== Running {proto} ===")
        for B in b_list:
            print(f"\n--- {proto} B={B} ---")
            try:
                if proto == "beat":
                    rows = run_beat_one(B)
                    append_csv(BEAT_CSV, rows, header)
                else:
                    rows = run_protocol_one(proto, B)
                    csv_path = os.path.join(OUT_DIR, f"{proto}_results.csv")
                    append_csv(csv_path, rows, header)
            except KeyboardInterrupt:
                print("Interrupted by user")
                sys.exit(0)
            except Exception as e:
                print(f"ERROR: {e}")
                continue

    print(f"\nAll done in {int(time.time() - overall_start)}s")


if __name__ == "__main__":
    main()

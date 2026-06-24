#!/usr/bin/env python3
"""
Batch experiment runner for ACS (VABA) on N remote servers.

Run:
  python3 run_acs_batch.py [--b-list 10,100,...]
"""

import argparse
import csv
import os
import subprocess
import sys
import time
from datetime import datetime
from threading import Thread

PASS = 'York@233'
SERVERS = [
    "120.27.215.50",
    "116.62.149.8",
    "47.98.121.97",
    "116.62.240.167",
    "121.43.234.253",
    "121.199.72.252",
    "121.40.130.83",
    "121.40.94.52",
    "120.26.46.218",
    "120.55.86.74",
    "121.40.255.201",
    "121.43.148.183",
    "121.40.158.250",
    "121.40.117.123",
    "121.40.88.101",
    "121.40.118.7",
]
N = 16
F = 5
ACS_REMOTE_DIR = "/root/acs"

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
ACS_CSV = os.path.join(OUT_DIR, "acs_results.csv")

DEFAULT_B_LIST = [10, 100, 250, 500, 750, 1000, 2500, 5000, 7500,
                  10000, 25000, 50000, 75000, 100000]


SSH_OPTS = [
    "-o", "StrictHostKeyChecking=no",
    "-o", "ConnectTimeout=15",
    "-o", "ServerAliveInterval=30",
]


def ssh_run(host, cmd, capture=True, timeout=60):
    """Run a command on a remote host."""
    full_cmd = ["sshpass", "-p", PASS, "ssh"] + SSH_OPTS + [f"root@{host}", cmd]
    try:
        result = subprocess.run(full_cmd, capture_output=capture, text=True, timeout=timeout)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "timeout"
    except Exception as e:
        return -1, "", str(e)


def ssh_run_background(host, cmd):
    """Run a command on a remote host in background (fire and forget)."""
    full_cmd = ["sshpass", "-p", PASS, "ssh"] + SSH_OPTS + [f"root@{host}", cmd]
    return subprocess.Popen(full_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def launch_all_parallel(host_cmds):
    """Launch commands on multiple hosts in parallel using threads."""
    threads = []
    for host, cmd in host_cmds:
        t = Thread(target=ssh_run_background, args=(host, cmd))
        t.daemon = True
        threads.append(t)
        t.start()
    for t in threads:
        t.join(timeout=5)


def collect_time_acs(host, node_id):
    """Collect ADKG time from ACS results.

    Looks for 'ADKG start time:' and 'Total bytes sent out' lines
    to compute elapsed time. Also tries the old 'ADKG time:' format.
    """
    import re

    # Try the new format: compute time from log timestamps
    rc1, out_start, _ = ssh_run(
        host,
        f"grep 'ADKG start time' /tmp/acs_node{node_id}.log 2>/dev/null | tail -1",
        timeout=10,
    )
    rc2, out_end, _ = ssh_run(
        host,
        f"grep 'Total bytes sent out aa' /tmp/acs_node{node_id}.log 2>/dev/null | tail -1",
        timeout=10,
    )

    adkg_time = None
    if out_start.strip() and out_end.strip():
        try:
            # Extract ADKG start timestamp
            m = re.search(r'ADKG start time:\s+([0-9.]+)', out_start)
            if m:
                t_start = float(m.group(1))
                # Extract the log timestamp of the "Total bytes sent" line
                # Format: "2026-06-06 21:32:48,098:[vaba_run.py:99]:..."
                m2 = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+', out_end)
                if m2:
                    from datetime import datetime
                    t_end = datetime.strptime(m2.group(1), "%Y-%m-%d %H:%M:%S").timestamp()
                    adkg_time = t_end - t_start
        except Exception:
            pass

    # Fallback: try old "ADKG time:" format
    if adkg_time is None:
        rc, out, _ = ssh_run(
            host,
            f"grep 'ADKG time' /tmp/acs_node{node_id}.log 2>/dev/null | tail -1",
            timeout=10,
        )
        if out.strip():
            m = re.search(r'ADKG time:\s+([0-9.]+)', out)
            if m:
                adkg_time = float(m.group(1))

    return adkg_time


def run_acs_one(B, max_wait=900):
    """Run one ACS experiment with given B across all servers."""
    print(f"  [acs B={B}] starting")

    # Update config files with correct B value on all servers
    ips_str = " ".join(SERVERS)
    for host in SERVERS:
        ssh_run(host,
            f"python3 -c \"import json; ips='{ips_str}'.split(); peers=[ip+':7001' for ip in ips]; "
            f"[json.dump({{'N':7,'t':2,'k':{B},'my_id':i,'peers':peers}}, "
            f"open(f'/root/acs/conf/adkg_16_remote/config-{{i}}.json','w')) for i in range(16)]\"",
            timeout=10)
    print(f"  [config] Updated k={B} on all servers")

    # Calculate a start time ~15s in the future
    start_time = int(time.time()) + 15

    # Generate config and launch on each server
    host_cmds = []
    for i, host in enumerate(SERVERS):
        cmd = (
            f"export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH && "
            f"export PYTHONUNBUFFERED=1 && "
            f"cd {ACS_REMOTE_DIR} && "
            f"nohup timeout 300 python3 -u -m scripts.vaba_run -d "
            f"-f conf/adkg_16_remote/config-{i}.json -time {start_time} "
            f"> /tmp/acs_node{i}.log 2>&1 &"
        )
        host_cmds.append((host, cmd))

    print(f"  [cleanup] {ACS_REMOTE_DIR}")
    # Clean up first
    for host in SERVERS:
        ssh_run(host, f"pkill -9 -f vaba_run 2>/dev/null; rm -f /tmp/acs_node*.log; true", timeout=10)

    # Launch all nodes in parallel
    launch_all_parallel(host_cmds)

    # Poll for completion
    start = time.time()
    poll_interval = 5
    last_print = 0
    straggler_grace = 180
    three_done_at = None
    while time.time() - start < max_wait:
        time.sleep(poll_interval)
        finished_count = 0
        for i, host in enumerate(SERVERS):
            rc, out, _ = ssh_run(
                host,
                f"grep -c 'Total bytes sent out aa' /tmp/acs_node{i}.log 2>/dev/null || echo 0",
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
        adkg = collect_time_acs(host, i)
        rows.append([timestamp, "acs", N, F, B, i, host, adkg])
        print(f"    node {i}: adkg={adkg}")

    # Kill stragglers
    for host in SERVERS:
        ssh_run(host, "pkill -9 -f vaba_run 2>/dev/null; true", timeout=10)
    return rows


def append_csv(path, rows, header):
    """Append rows to CSV, writing header if file doesn't exist."""
    file_exists = os.path.isfile(path)
    with open(path, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(header)
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--b-list", default=",".join(str(b) for b in DEFAULT_B_LIST),
                        help="comma-separated B values")
    args = parser.parse_args()

    b_list = [int(b.strip()) for b in args.b_list.split(",") if b.strip()]

    header = ["timestamp", "protocol", "N", "f", "B", "replica", "host",
              "adkg_time"]

    print(f"Protocol: acs (VABA)")
    print(f"N={N}, f={F}")
    print(f"B values:  {b_list}")
    print(f"Total runs: {len(b_list)}")
    print(f"Output:    {ACS_CSV}")
    print()

    overall_start = time.time()

    print(f"\n=== Running acs ===")
    for B in b_list:
        print(f"\n--- acs B={B} ---")
        try:
            rows = run_acs_one(B)
            append_csv(ACS_CSV, rows, header)
        except KeyboardInterrupt:
            print("Interrupted by user")
            sys.exit(0)
        except Exception as e:
            print(f"  ERROR: {e}")

    elapsed = time.time() - overall_start
    print(f"\nAll done in {int(elapsed)}s")


if __name__ == "__main__":
    main()

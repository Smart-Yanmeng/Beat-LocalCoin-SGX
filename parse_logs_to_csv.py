#!/usr/bin/env python3
"""Parse Dumbo BFT consensus logs and generate CSV results file."""

import re
import os
import csv
import sys
from datetime import datetime

def parse_consensus_log(log_file, node_id, protocol, N, f, batch_size, epochs):
    """Parse a single node's consensus log and return rows for CSV."""
    rows = []
    
    if not os.path.exists(log_file):
        print(f"  WARNING: {log_file} not found")
        return rows
    
    with open(log_file, 'r') as fp:
        content = fp.read()
    
    # Parse per-round results
    # Pattern: "Node X Delivers ACS Block in Round Y with having Z TXs"
    round_pattern = re.compile(
        r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d+).*Node (\d+) Delivers ACS Block in Round (\d+) with having (\d+) TXs'
    )
    delay_pattern = re.compile(
        r'ACS Block Delay at Node (\d+): ([\d.]+)'
    )
    tps_pattern = re.compile(
        r"Current Block's TPS at Node (\d+): ([\d.]+)"
    )
    summary_pattern = re.compile(
        r'node (\d+) breaks in ([\d.]+) seconds with total delivered Txs\s+(\d+)'
    )
    
    lines = content.split('\n')
    
    for i, line in enumerate(lines):
        # Match round delivery
        m = round_pattern.search(line)
        if m:
            timestamp = m.group(1)
            node = int(m.group(2))
            round_num = int(m.group(3))
            txs = int(m.group(4))
            
            # Look for delay and TPS in next lines
            delay = None
            tps = None
            for j in range(i+1, min(i+3, len(lines))):
                dm = delay_pattern.search(lines[j])
                if dm and int(dm.group(1)) == node:
                    delay = float(dm.group(2))
                tm = tps_pattern.search(lines[j])
                if tm and int(tm.group(1)) == node:
                    tps = float(tm.group(2))
            
            rows.append({
                'timestamp': timestamp,
                'protocol': protocol,
                'N': N,
                'f': f,
                'batch_size': batch_size,
                'epochs': epochs,
                'node_id': node_id,
                'round': round_num,
                'txs_delivered': txs,
                'delay_sec': f"{delay:.6f}" if delay else '',
                'tps': f"{tps:.2f}" if tps else '',
                'total_time_sec': '',
                'total_txs': ''
            })
    
    # Parse summary line
    m = summary_pattern.search(content)
    if m:
        total_time = float(m.group(2))
        total_txs = int(m.group(3))
        rows.append({
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'protocol': protocol,
            'N': N,
            'f': f,
            'batch_size': batch_size,
            'epochs': epochs,
            'node_id': node_id,
            'round': 'TOTAL',
            'txs_delivered': total_txs,
            'delay_sec': '',
            'tps': f"{total_txs/total_time:.2f}" if total_time > 0 else '',
            'total_time_sec': f"{total_time:.6f}",
            'total_txs': total_txs
        })
    
    return rows


def main():
    # Configuration
    log_dir = sys.argv[1] if len(sys.argv) > 1 else '/tmp/dumbo_logs'
    output_csv = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), 'experiment_results.csv')
    
    protocol = sys.argv[3] if len(sys.argv) > 3 else 'dumbo'
    N = int(sys.argv[4]) if len(sys.argv) > 4 else 4
    f = int(sys.argv[5]) if len(sys.argv) > 5 else 1
    batch_size = int(sys.argv[6]) if len(sys.argv) > 6 else 1000
    epochs = int(sys.argv[7]) if len(sys.argv) > 7 else 20
    
    print(f"Parsing logs from: {log_dir}")
    print(f"Output CSV: {output_csv}")
    print(f"Protocol: {protocol}, N: {N}, f: {f}, B: {batch_size}, K: {epochs}")
    print()
    
    all_rows = []
    for i in range(N):
        log_file = os.path.join(log_dir, f'consensus-node-{i}.log')
        print(f"  Parsing node {i}: {log_file}")
        rows = parse_consensus_log(log_file, i, protocol, N, f, batch_size, epochs)
        all_rows.extend(rows)
        print(f"    Found {len(rows)} entries")
    
    # Write CSV
    fieldnames = ['timestamp', 'protocol', 'N', 'f', 'batch_size', 'epochs', 
                  'node_id', 'round', 'txs_delivered', 'delay_sec', 'tps', 
                  'total_time_sec', 'total_txs']
    
    # Append if file exists, otherwise create with header
    file_exists = os.path.exists(output_csv)
    mode = 'a' if file_exists else 'w'
    
    with open(output_csv, mode, newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerows(all_rows)
    
    print(f"\n{'Appended' if file_exists else 'Written'} {len(all_rows)} rows to {output_csv}")
    
    # Print summary
    print("\n=== Summary ===")
    for i in range(N):
        node_rows = [r for r in all_rows if r['node_id'] == i and r['round'] != 'TOTAL']
        if node_rows:
            delays = [float(r['delay_sec']) for r in node_rows if r['delay_sec']]
            tps_vals = [float(r['tps']) for r in node_rows if r['tps']]
            print(f"  Node {i}: {len(node_rows)} rounds, "
                  f"avg delay: {sum(delays)/len(delays):.3f}s, "
                  f"avg TPS: {sum(tps_vals)/len(tps_vals):.1f}")


if __name__ == '__main__':
    main()

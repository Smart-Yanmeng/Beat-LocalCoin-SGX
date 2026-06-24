#!/usr/bin/env python3
"""Summarize per-B average latency / TPS from dumbo_results.csv and beat_results.csv."""

import csv
import os
from collections import defaultdict

OUT_DIR = os.path.dirname(os.path.abspath(__file__))


def load(path):
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path) as f:
        for r in csv.DictReader(f):
            rows.append(r)
    return rows


def summarize(rows, proto):
    # group by B
    by_b = defaultdict(list)
    for r in rows:
        try:
            B = int(r["B"])
            t = r["time_sec"]
            txs = r["txs_delivered"]
            if t in ("", "None", None):
                continue
            by_b[B].append((float(t), int(txs) if txs not in ("", "None", None) else 0))
        except Exception:
            continue

    out = []
    for B in sorted(by_b):
        entries = by_b[B]
        times = [e[0] for e in entries]
        txs = [e[1] for e in entries]
        avg_t = sum(times) / len(times)
        avg_tx = sum(txs) / len(txs)
        tps = avg_tx / avg_t if avg_t > 0 else 0
        out.append({
            "protocol": proto,
            "B": B,
            "nodes_done": len(entries),
            "avg_time_sec": round(avg_t, 4),
            "avg_txs": int(avg_tx),
            "tps": round(tps, 1),
        })
    return out


def main():
    dumbo = summarize(load(os.path.join(OUT_DIR, "dumbo_results.csv")), "dumbo")
    beat = summarize(load(os.path.join(OUT_DIR, "beat_results.csv")), "beat")

    summary_path = os.path.join(OUT_DIR, "summary.csv")
    with open(summary_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["protocol", "B", "nodes_done",
                                          "avg_time_sec", "avg_txs", "tps"])
        w.writeheader()
        for row in dumbo + beat:
            w.writerow(row)

    # Pretty print
    def show(title, data):
        print(f"\n=== {title} ===")
        print(f"{'B':>8} {'nodes':>6} {'avg_time(s)':>12} {'avg_txs':>9} {'TPS':>8}")
        for r in data:
            print(f"{r['B']:>8} {r['nodes_done']:>6} {r['avg_time_sec']:>12} "
                  f"{r['avg_txs']:>9} {r['tps']:>8}")

    show("Dumbo", dumbo)
    show("Beat-LocalCoin", beat)
    print(f"\nSummary written to {summary_path}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Pivot per-node results into wide format:
  <label>
  B   time_node0   time_node1   time_node2   time_node3
  ...

One block per protocol. Output to wide_results.csv (tab-separated, like the screenshot).
"""

import csv
import os
from collections import defaultdict

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# protocol -> (csv path, label)
SOURCES = [
    ("dumbo_results.csv", "Dumbo"),
    ("beat_results.csv",  "NONE-SGX"),
]

B_ORDER = [10, 100, 250, 500, 750, 1000, 2500, 5000, 7500,
           10000, 25000, 50000, 75000, 100000]


def load_wide(path):
    """Return {B: {replica: time}}."""
    table = defaultdict(dict)
    if not os.path.exists(path):
        return table
    with open(path) as f:
        for r in csv.DictReader(f):
            try:
                B = int(r["B"])
                rep = int(r["replica"])
                t = r["time_sec"]
                table[B][rep] = "" if t in ("", "None", None) else t
            except Exception:
                continue
    return table


def main():
    out_path = os.path.join(OUT_DIR, "wide_results.csv")
    lines = []
    for fname, label in SOURCES:
        table = load_wide(os.path.join(OUT_DIR, fname))
        if not table:
            continue
        lines.append([label, "", "", "", ""])
        for B in B_ORDER:
            if B not in table:
                continue
            row = [str(B)]
            for rep in range(4):
                row.append(str(table[B].get(rep, "")))
            lines.append(row)
        lines.append(["", "", "", "", ""])  # blank separator

    # Write comma-separated (standard CSV)
    with open(out_path, "w", newline="") as f:
        w = csv.writer(f)
        for row in lines:
            w.writerow(row)

    # Also print
    with open(out_path) as f:
        print(f.read())

    print(f"Written to {out_path}")


if __name__ == "__main__":
    main()

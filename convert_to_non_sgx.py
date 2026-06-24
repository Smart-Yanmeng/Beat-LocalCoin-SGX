#!/usr/bin/env python3
"""
Convert Beat-LocalCoin-SGX code from SGX mode to Non-SGX mode.

Only swap PAIRED markers (### todo: SGX immediately followed by ### todo: None-SGX
within the same enclosing block). Other isolated None-SGX markers are left untouched
to avoid breaking dependencies (some "None-SGX" blocks rely on cryptor which lives in SGX).

Usage:
  python3 convert_to_non_sgx.py <project_root>
"""

import os
import re
import sys

MARKER_RE = re.compile(r'^(\s*)#+\s*todo:\s*(SGX|None[\s-]?SGX|none[\s-]?sgx)(.*)$', re.I)

def parse_marker(line):
    m = MARKER_RE.match(line)
    if not m:
        return None
    indent = len(m.group(1))
    kind = m.group(2).lower()
    if kind == 'sgx':
        return ('sgx', indent)
    return ('none-sgx', indent)


def find_block_end(lines, start, marker_indent):
    """Find the end of a code block following a marker line. Block ends when we
    hit another marker or a non-empty line at indent <= marker_indent that is NOT a comment."""
    i = start
    while i < len(lines):
        line = lines[i]
        if parse_marker(line):
            return i
        if line.strip() == '':
            i += 1
            continue
        cur_indent = len(line) - len(line.lstrip())
        # If we drop below the marker indent and it's actual code (not a comment), stop.
        if cur_indent < marker_indent:
            return i
        i += 1
    return i


def comment_block(lines, start, end, base_indent):
    """Comment out non-comment lines from start..end (exclusive), preserving indent."""
    out = []
    for i in range(start, end):
        line = lines[i]
        stripped = line.lstrip()
        if stripped == '' or stripped.startswith('#'):
            out.append(line)
            continue
        cur_indent = len(line) - len(stripped)
        leading = line[:cur_indent]
        out.append(leading + '# ' + stripped)
    return out


def uncomment_block(lines, start, end, base_indent):
    """Uncomment '# ' or '#' prefix on lines deeper or equal to base_indent."""
    out = []
    for i in range(start, end):
        line = lines[i]
        stripped = line.lstrip()
        if not stripped.startswith('#'):
            out.append(line)
            continue
        cur_indent = len(line) - len(stripped)
        if cur_indent < base_indent:
            out.append(line)
            continue
        leading = line[:cur_indent]
        after = stripped[1:]  # remove '#'
        if after.startswith(' '):
            after = after[1:]
        out.append(leading + after)
    return out


def process_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Find all markers
    markers = []
    for i, line in enumerate(lines):
        m = parse_marker(line)
        if m:
            markers.append((i, m[0], m[1]))  # (line_index, kind, indent)

    if not markers:
        return False

    # Find PAIRED markers: SGX followed immediately by None-SGX at same indent
    swaps = []  # list of (sgx_marker_line, sgx_block_end, ns_marker_line, ns_block_end, indent)
    j = 0
    while j < len(markers) - 1:
        cur = markers[j]
        nxt = markers[j+1]
        # Pair only if SGX -> None-SGX at same indent
        if cur[1] == 'sgx' and nxt[1] == 'none-sgx' and cur[2] == nxt[2]:
            sgx_start = cur[0] + 1
            sgx_end = nxt[0]  # SGX block ends at None-SGX marker
            ns_start = nxt[0] + 1
            # None-SGX block ends at next marker, or end-of-block by indent
            ns_end = find_block_end(lines, ns_start, nxt[2])
            swaps.append((cur[0], sgx_start, sgx_end, nxt[0], ns_start, ns_end, cur[2]))
            j += 2
        else:
            j += 1

    if not swaps:
        return False

    # Apply swaps from bottom to top so line indices stay valid
    new_lines = lines[:]
    for sgx_marker, sgx_start, sgx_end, ns_marker, ns_start, ns_end, indent in reversed(swaps):
        # Replace none-sgx block first (later in file)
        ns_block = new_lines[ns_start:ns_end]
        ns_block = uncomment_block(ns_block, 0, len(ns_block), indent)
        new_lines[ns_start:ns_end] = ns_block

        # Replace sgx block
        sgx_block = new_lines[sgx_start:sgx_end]
        sgx_block = comment_block(sgx_block, 0, len(sgx_block), indent)
        new_lines[sgx_start:sgx_end] = sgx_block

    if new_lines != lines:
        with open(path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        return True
    return False


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 convert_to_non_sgx.py <project_root>")
        sys.exit(1)

    root = sys.argv[1]
    files_changed = 0

    for dirpath, _, files in os.walk(root):
        if '__pycache__' in dirpath:
            continue
        for fname in files:
            if not fname.endswith('.py'):
                continue
            path = os.path.join(dirpath, fname)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            if 'todo: SGX' not in content:
                continue
            print(f"Processing {path}")
            if process_file(path):
                files_changed += 1
                print(f"  ✓ Modified")
            else:
                print(f"  - No paired SGX/None-SGX blocks found")

    print(f"\n{files_changed} files modified.")

if __name__ == '__main__':
    main()

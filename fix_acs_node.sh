#!/bin/bash
# Fix acs_run_node.sh to support 7 nodes
# Run this on each server

sed -i 's|conf/adkg_4_remote|conf/adkg_7_remote|g' /root/acs/acs_run_node.sh

# Replace the hardcoded peers heredoc with dynamic generation
python3 << 'PYEOF'
import re

with open("/root/acs/acs_run_node.sh", "r") as f:
    content = f.read()

# Find and replace the heredoc block that generates the config
old = '''cat > "$CONFIG_FILE" << EOF
{"N":$N,"t":$T,"k":$B,"my_id":$NODE_ID,"peers":["${IPS[0]}:$PORT","${IPS[1]}:$PORT","${IPS[2]}:$PORT","${IPS[3]}:$PORT"]}
EOF'''

new = '''PEERS_JSON=$(python3 -c "
ips = '${IPS[*]}'.split()
print('[' + ','.join(['\\\"' + ip + ':$PORT\\\"' for ip in ips]) + ']')
")
cat > "$CONFIG_FILE" << EOF
{"N":$N,"t":$T,"k":$B,"my_id":$NODE_ID,"peers":$PEERS_JSON}
EOF'''

if old in content:
    content = content.replace(old, new)
    with open("/root/acs/acs_run_node.sh", "w") as f:
        f.write(content)
    print("Fixed acs_run_node.sh")
else:
    print("Pattern not found, checking current state...")
    # Show the relevant lines
    for i, line in enumerate(content.split('\n')):
        if 'cat > "$CONFIG_FILE"' in line or 'peers' in line.lower():
            print(f"  Line {i+1}: {line}")
PYEOF

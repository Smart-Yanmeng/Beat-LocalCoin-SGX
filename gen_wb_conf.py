#!/usr/bin/env python3
"""Generate WaterBear multi-host conf.json (QS-Q: consensus=14, RBCType=1)."""
import json
import sys

IPS = ["120.27.215.50", "116.62.149.8", "47.98.121.97", "116.62.240.167"]
PORT = "11000"

# QS-Q preset
consensus = 14
rbctype = 1

conf = {
    "maxBatchSize": 1000000,
    "maxTxSize": 250,
    "sleepTimer": 50,
    "clientTimer": 10000,
    "broadcastTimer": 10000,
    "tParameter": 0,
    "verbose": False,
    "evalMode": 0,
    "evalInterval": 10,
    "cryptoOpt": 0,
    "local": False,
    "maliciousNode": False,
    "maliciousMode": 0,
    "maliciousNID": "",
    "splitPorts": False,
    "logOpt": 0,
    "consensus": consensus,
    "RBCType": rbctype,
    "replicas": [
        {"id": str(i), "host": ip, "port": PORT}
        for i, ip in enumerate(IPS)
    ],
}

out = sys.argv[1] if len(sys.argv) > 1 else "/tmp/wb_conf.json"
with open(out, "w") as f:
    json.dump(conf, f, indent=3)
print(f"written {out}")
print(json.dumps(conf["replicas"], indent=2))

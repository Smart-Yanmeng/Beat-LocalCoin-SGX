#!/usr/bin/env python3
"""Generate keys for N nodes."""
import sys
import os
import pickle

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from adaptive.commoncoin.thresprf import dealer as prf_dealer
from adaptive.threshenc.tdh2 import dealer as enc_dealer
from adaptive.ecdsa.ecdsa_ssl import KEY


def generate_prf_keys(N, k, output_file):
    print(f"Generating threshold signature keys: N={N}, k={k}...")
    PK, SKs, gg = prf_dealer(players=N, k=k)
    from adaptive.commoncoin.thresprf import serialize, serialize1
    from adaptive.core.utils import serialize as core_serialize
    data = (N, k, serialize(PK.VK), [serialize(vk) for vk in PK.VKs],
            [(sk.i, serialize(sk.SK)) for sk in SKs], core_serialize(gg))
    with open(output_file, "wb") as f:
        pickle.dump(data, f)
    print(f"  -> {output_file} ({os.path.getsize(output_file)} bytes)")


def generate_enc_keys(N, k, output_file):
    print(f"Generating threshold encryption keys: N={N}, k={k}...")
    PK, SKs = enc_dealer(players=N, k=k)
    from adaptive.threshenc.tdh2 import serialize, serialize1
    data = (N, k, serialize(PK.VK), [serialize1(vk) for vk in PK.VKs],
            [(sk.i, serialize1(sk.SK)) for sk in SKs])
    with open(output_file, "wb") as f:
        pickle.dump(data, f)
    print(f"  -> {output_file} ({os.path.getsize(output_file)} bytes)")


def generate_ecdsa_keys(N, output_file):
    print(f"Generating ECDSA keys: N={N}...")
    keylist = []
    for i in range(N):
        key = KEY()
        key.generate()
        keylist.append(key.get_secret())
    with open(output_file, "wb") as f:
        pickle.dump(keylist, f)
    print(f"  -> {output_file} ({os.path.getsize(output_file)} bytes)")


if __name__ == "__main__":
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 16
    k = int(sys.argv[2]) if len(sys.argv) > 2 else N // 2
    prefix = f"thsig{N}_{k}" if k != N // 2 else f"thsig{N}"

    generate_prf_keys(N, k, f"{prefix}.keys")
    generate_enc_keys(N, k, f"thenc{prefix.split('thsig')[1]}.keys".replace(".", ""))
    generate_ecdsa_keys(N, f"ecdsa{N}.keys")

    print("\nDone! Generated:")
    print(f"  {prefix}.keys        (threshold signature)")
    print(f"  thenc{prefix.split('thsig')[1]}.keys  (threshold encryption)")
    print(f"  ecdsa{N}.keys        (ECDSA)")

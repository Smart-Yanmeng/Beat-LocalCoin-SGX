#!/usr/bin/env python3
"""Verify generated keys for 16 nodes."""
import sys
import os
import pickle
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from adaptive.commoncoin.thresprf import deserialize, TPRFPublicKey, TPRFPrivateKey
from adaptive.threshenc.tdh2 import deserialize as enc_deserialize, deserialize0, TDHPublicKey, TDHPrivateKey
from adaptive.ecdsa.ecdsa_ssl import KEY


def verify_prf(N, k):
    print(f"[1] Threshold Signature Keys (thsig16.keys)")
    with open("thsig16.keys", "rb") as f:
        (l, k_file, sVK, sVKs, SKs_data, gg) = pickle.load(f)
    from adaptive.core.utils import deserialize as core_deserialize
    gg = core_deserialize(gg)

    PK = TPRFPublicKey(l, k_file, deserialize(sVK), [deserialize(vk) for vk in sVKs])
    SKs = [TPRFPrivateKey(l, k_file, deserialize(sVK), [deserialize(vk) for vk in sVKs],
                           deserialize(SKp[1]), SKp[0]) for SKp in SKs_data]

    assert l == N and k_file == k and len(SKs) == N
    print(f"  N={l}, k={k_file}, {len(SKs)} shares loaded")

    # Test sign + combine + verify
    h = PK.hash_message("verification test")
    sigs = {}
    proof_c = {}
    proof_z = {}
    for SK in SKs:
        sigs[SK.i], proof_c[SK.i], proof_z[SK.i] = SK.sign(h, gg)

    indices = list(range(N))
    random.shuffle(indices)
    S = set(indices[:k])
    combined = PK.combine_shares(dict((s, sigs[s]) for s in S))
    assert PK.verify_signature(combined, h)
    print(f"  Sign -> combine {k} shares -> verify: OK")
    print(f"  PASS\n")


def verify_enc(N, k):
    print(f"[2] Threshold Encryption Keys (thenc16keys)")
    with open("thenc16keys", "rb") as f:
        (l, k_file, sVK, sVKs, SKs_data) = pickle.load(f)

    PK = TDHPublicKey(l, k_file, enc_deserialize(sVK), [enc_deserialize(vk) for vk in sVKs])
    SKs = [TDHPrivateKey(l, k_file, enc_deserialize(sVK), [enc_deserialize(vk) for vk in sVKs],
                           deserialize0(SKp[1]), SKp[0]) for SKp in SKs_data]

    assert l == N and k_file == k and len(SKs) == N
    print(f"  N={l}, k={k_file}, {len(SKs)} shares loaded")

    # Test encrypt + decrypt share generation
    msg = b"test"
    L = "label"
    ciphertext = PK.encrypt(msg, L)
    c, L_val, u, u1, e, f = ciphertext

    indices = list(range(N))
    random.shuffle(indices)
    S = indices[:k]
    shares = {}
    for i in S:
        shares[i] = SKs[i].decrypt_share(c, L_val, u, u1, e, f)

    assert len(shares) == k
    print(f"  Encrypt -> {k} decrypt shares generated: OK")
    print(f"  PASS\n")


def verify_ecdsa(N):
    print(f"[3] ECDSA Keys (ecdsa16.keys)")
    with open("ecdsa16.keys", "rb") as f:
        ecdsa_sec_list = pickle.load(f)

    assert len(ecdsa_sec_list) == N
    print(f"  {len(ecdsa_sec_list)} keys loaded")

    keys = []
    for secret in ecdsa_sec_list:
        k = KEY()
        k.generate(secret)
        k.set_compressed(True)
        keys.append(k)

    # Test sign + verify on all keys
    msg = b"verification test message"
    for i, k in enumerate(keys):
        sig = k.sign(msg)
        assert k.verify(msg, sig), f"Key {i} failed"
    print(f"  All {N} keys: sign + verify OK")
    print(f"  PASS\n")


if __name__ == "__main__":
    N, k = 16, 8
    print("=" * 50)
    print(f"Key Verification: {N} nodes, threshold={k}")
    print("=" * 50)
    verify_prf(N, k)
    verify_enc(N, k)
    verify_ecdsa(N)
    print("=" * 50)
    print("ALL VERIFICATIONS PASSED")
    print("=" * 50)

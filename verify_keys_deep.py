#!/usr/bin/env python3
"""Deep verification: test share combination for threshold schemes."""
import sys
import os
import pickle
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from adaptive.commoncoin.thresprf import deserialize, TPRFPublicKey, TPRFPrivateKey
from adaptive.threshenc.tdh2 import deserialize as enc_deserialize, deserialize0, TDHPublicKey, TDHPrivateKey
from adaptive.commoncoin.thresprf_gipc import serialize, serialize1, combine_and_verify


def deep_verify_prf(N, k):
    print(f"[PRF] Deep verification: N={N}, k={k}")
    with open("thsig16.keys", "rb") as f:
        (l, k_file, sVK, sVKs, SKs_data, gg) = pickle.load(f)

    from adaptive.core.utils import deserialize as core_deserialize
    gg = core_deserialize(gg)

    PK = TPRFPublicKey(l, k_file, deserialize(sVK), [deserialize(vk) for vk in sVKs])
    SKs = [TPRFPrivateKey(l, k_file, deserialize(sVK), [deserialize(vk) for vk in sVKs],
                           deserialize(SKp[1]), SKp[0]) for SKp in SKs_data]

    # Sign with k shares and combine
    h = PK.hash_message("test message")
    sigs = {}
    proof_c = {}
    proof_z = {}
    for SK in SKs:
        sigs[SK.i], proof_c[SK.i], proof_z[SK.i] = SK.sign(h, gg)

    # Pick k random shares and combine
    indices = list(range(N))
    random.shuffle(indices)
    S = set(indices[:k])
    combined = PK.combine_shares(dict((s, sigs[s]) for s in S))
    assert PK.verify_signature(combined, h), "PRF signature verification failed!"
    print(f"  Combined {k} shares -> signature verified OK")

    # Try with different subset
    random.shuffle(indices)
    S2 = set(indices[:k])
    combined2 = PK.combine_shares(dict((s, sigs[s]) for s in S2))
    assert PK.verify_signature(combined2, h), "PRF signature verification failed (2nd subset)!"
    print(f"  Combined {k} different shares -> signature verified OK")
    print(f"  PASS")


def deep_verify_enc(N, k):
    print(f"[ENC] Deep verification: N={N}, k={k}")
    with open("thenc16keys", "rb") as f:
        (l, k_file, sVK, sVKs, SKs_data) = pickle.load(f)

    PK = TDHPublicKey(l, k_file, enc_deserialize(sVK), [enc_deserialize(vk) for vk in sVKs])
    SKs = [TDHPrivateKey(l, k_file, enc_deserialize(sVK), [enc_deserialize(vk) for vk in sVKs],
                           deserialize0(SKp[1]), SKp[0]) for SKp in SKs_data]

    # Encrypt a message
    msg = b"hello threshold encryption!"
    L = "label"
    ciphertext = PK.encrypt(msg, L)
    c, L_val, u, u1, e, f = ciphertext
    print(f"  Encrypted message: {len(msg)} bytes -> ciphertext OK")

    # Decrypt with k shares
    indices = list(range(N))
    random.shuffle(indices)
    S = indices[:k]

    shares = {}
    for i in S:
        shares[i] = SKs[i].decrypt_share(c, L_val, u, u1, e, f)

    recovered = PK.combine_shares(c, L_val, u, u1, e, f, shares)
    assert recovered == msg.decode("ISO-8859-1"), f"Decryption mismatch: {recovered} != {msg}"
    print(f"  Decrypted with {k} shares -> message recovered OK")
    print(f"  PASS")


if __name__ == "__main__":
    N, k = 16, 8
    print("=" * 50)
    print(f"Deep Key Verification ({N} nodes, threshold={k})")
    print("=" * 50)
    deep_verify_prf(N, k)
    print()
    deep_verify_enc(N, k)
    print()
    print("=" * 50)
    print("ALL DEEP VERIFICATIONS PASSED")
    print("=" * 50)

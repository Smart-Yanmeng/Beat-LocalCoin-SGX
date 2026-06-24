# =====================================================
# Inline replacements for SGX socket calls.
# Replicates the logic from adaptive/sgx/sgx_*.py servers
# without going through TCP sockets.
# =====================================================

import base64
import random as _stdrandom
from collections import defaultdict
from ..sgx.cryptor import Cryptor

# Shared cryptor instance (RSA + AES helper)
_cryptor = Cryptor()


def _default_zero():
    return 0


# -----------------------------------------------------
# State that used to live in each SGX server process
# -----------------------------------------------------
# sgx_counter0  (was port 65433)
_readyCounter_b0 = [defaultdict(_default_zero) for _ in range(4)]
# sgx_counter1  (was port 65434)
_readyCounter_b1 = [defaultdict(_default_zero) for _ in range(4)]
# sgx_counter2  (was port 65435)
_readyCounter_b2 = [defaultdict(_default_zero) for _ in range(4)]


def _counter_step(counter_table, t, msgBundle, threshold2):
    """Common counter logic used by sgx_counter0/1/2."""
    counter_table[msgBundle[1]][msgBundle[2]] += 1
    tmp = counter_table[msgBundle[1]][msgBundle[2]]
    result = 0
    if tmp >= t + 1:
        result = 1
    if tmp >= threshold2:
        result = 2
    return result


# -----------------------------------------------------
# Inline replacement: sgx_counter0 (port 65433)
# -----------------------------------------------------
def get_counter_result_from_sgx_broadcast(host='127.0.0.1', port=65433, obj=None):
    if obj is None:
        return 0
    t = obj.get("t", 0)
    msgBundle = obj.get("msgBundle", [])
    threshold2 = obj.get("Threshold2", 0)
    return _counter_step(_readyCounter_b0, t, msgBundle, threshold2)


# -----------------------------------------------------
# Inline replacement: sgx_counter1 (port 65434)
# -----------------------------------------------------
def get_counter_result_from_sgx_broadcast1(host='127.0.0.1', port=65434, obj=None):
    if obj is None:
        return 0
    t = obj.get("t", 0)
    msgBundle = obj.get("msgBundle", [])
    threshold2 = obj.get("Threshold2", 0)
    return _counter_step(_readyCounter_b1, t, msgBundle, threshold2)


# -----------------------------------------------------
# Inline replacement: sgx_counter2 (port 65435)
# -----------------------------------------------------
def get_counter_result_from_sgx_broadcast2(host='127.0.0.1', port=65435, obj=None):
    if obj is None:
        return 0
    t = obj.get("t", 0)
    msgBundle = obj.get("msgBundle", [])
    threshold2 = obj.get("Threshold2", 0)
    return _counter_step(_readyCounter_b2, t, msgBundle, threshold2)


# -----------------------------------------------------
# Inline replacement: sgx_judge_est0 (port 65430)
# Decrypt votes, majority decision, return encrypted bit
# -----------------------------------------------------
def get_est1_from_sgx(host='127.0.0.1', port=65430, obj=None):
    if obj is None:
        return None
    voteObj1 = obj.get("voteObj1", dict())
    count_0 = 0
    count_1 = 0
    for key in voteObj1:
        vote = int.from_bytes(_cryptor.decrypt_rsa(base64.b16decode(voteObj1[key])), byteorder='big')
        if vote == 0:
            count_0 += 1
        else:
            count_1 += 1

    if count_0 > count_1:
        est = 0
    elif count_0 < count_1:
        est = 1
    else:
        est = _stdrandom.choice([0, 1])
    return base64.b16encode(_cryptor.encrypt_rsa(est.to_bytes(1, "big"))).decode("utf8")


# -----------------------------------------------------
# Inline replacement: sgx_judge_est1 (port 65431)
# Majority over N/2 vs ambiguous (returns 2)
# -----------------------------------------------------
def get_est2_from_sgx(host='127.0.0.1', port=65431, obj=None):
    if obj is None:
        return None
    N = obj.get("n", 0)
    voteObj2 = obj.get("voteObj2", dict())
    count_0 = 0
    count_1 = 0
    for key in voteObj2:
        vote = int.from_bytes(_cryptor.decrypt_rsa(base64.b16decode(voteObj2[key])), byteorder="big")
        if vote == 0:
            count_0 += 1
        else:
            count_1 += 1
    if count_0 > N / 2:
        est = 0
    elif count_1 > N / 2:
        est = 1
    else:
        est = 2
    return base64.b16encode(_cryptor.encrypt_rsa(est.to_bytes(1, "big"))).decode("utf-8")


# -----------------------------------------------------
# Inline replacement: sgx_judge_est2 (port 65432)
# Final round: returns dict {v, result, coin}
# -----------------------------------------------------
def get_est3_from_sgx(host='127.0.0.1', port=65432, obj=None):
    if obj is None:
        return {"v": 0, "result": 0, "coin": 0}
    counter0 = 0
    counter1 = 0
    result = {"v": 0, "result": 0, "coin": 0}

    voteObj3 = obj.get("voteObj3", dict())
    t = obj.get("t", 0)

    for key in voteObj3:
        vote = int.from_bytes(_cryptor.decrypt_rsa(base64.b16decode(voteObj3[key])), byteorder="big")
        if vote == 0:
            result['v'] = voteObj3[key]
            counter0 += 1
        else:
            result['v'] = voteObj3[key]
            counter1 += 1

    if counter1 >= 2 * t + 1:
        result['result'] = 1
    elif counter0 >= 2 * t + 1:
        result['result'] = 2
    elif counter0 >= t + 1:
        result['result'] = 3
    elif counter1 >= t + 1:
        result['result'] = 4
    else:
        est = _stdrandom.choice([0, 1])
        result['coin'] = base64.b16encode(_cryptor.encrypt_rsa(est.to_bytes(1, "big"))).decode("utf-8")
    return result


# -----------------------------------------------------
# Inline replacement: sgx_decrypt (port 65436)
# Decrypts proposal: RSA-decrypt AES key, AES-decrypt body
# -----------------------------------------------------
_TR_SIZE = 250


def get_recovered_syncedTx_from_SGX(obj=None):
    if obj is None:
        return []
    encryptedVote = obj.get("vote", "")
    proposal = obj.get("proposal", "")

    voteFromEncrypted = int.from_bytes(_cryptor.decrypt_rsa(base64.b16decode(encryptedVote)), byteorder='big')
    if voteFromEncrypted != 1:
        return []
    aesKeyFromEncrypted = _cryptor.decrypt_rsa(proposal[:256])
    encodedTxSet = _cryptor.decrypt_aes(proposal[256:].rstrip(b'\x01'), aesKeyFromEncrypted)
    assert len(encodedTxSet) % _TR_SIZE == 0
    return [encodedTxSet[i:i + _TR_SIZE] for i in range(0, len(encodedTxSet), _TR_SIZE)]


# -----------------------------------------------------
# Inline replacement: get_coin_from_sgx (was random server)
# Original server returned a random bit. Just do it locally.
# -----------------------------------------------------
def get_coin_from_sgx():
    return _stdrandom.choice([0, 1])


# -----------------------------------------------------
# Inline replacement: get_rbc_counter_from_SGX (used by includeTransaction.py)
# Same counter logic.
# -----------------------------------------------------
_rbc_counter_state = {}


def get_rbc_counter_from_SGX(obj=None):
    """obj has keys: tmp (already-incremented count), t, Threshold2.
    The original SGX server simply applied threshold logic on the tmp value.
    """
    if obj is None:
        return 0
    tmp = obj.get("tmp", 0)
    t = obj.get("t", 0)
    threshold2 = obj.get("Threshold2", 0)
    result = 0
    if tmp >= t + 1:
        result = 1
    if tmp >= threshold2:
        result = 2
    return result

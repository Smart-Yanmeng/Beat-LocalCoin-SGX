#!/bin/bash

export PYTHONPATH=/app/adaptive:$PYTHONPATH
export LIBRARY_PATH=/usr/local/lib:$LIBRARY_PATH
export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH

N=${TRUBFT_N:-4}
T=${TRUBFT_T:-1}
B=${TRUBFT_B:-100}
TX=${TRUBFT_TX:--1}
K=$((T + 1))

if [ "$TX" = "-1" ]; then
    TX=$B
fi

# 密钥文件名包含N，不同N使用不同密钥
KEYS_FILE="thsig${N}_1.keys"
ECDSA_FILE="ecdsa${N}.keys"
ENC_FILE="thenc${N}_1.keys"

# 在容器内生成密钥
generate_keys() {
    echo "生成密钥 N=$N, T=$T, K=$K ..." >&2
    
    python3 -m adaptive.commoncoin.thresprf $N $K > "$KEYS_FILE"
    python3 -m adaptive.ecdsa.generate_keys_ecdsa $N "$ECDSA_FILE"
    python3 -m adaptive.threshenc.tdh2 $N $K > "$ENC_FILE"
    
    echo "密钥生成完成" >&2
}

# 检查密钥是否存在，不存在则生成
if [ ! -f "$KEYS_FILE" ] || [ ! -f "$ECDSA_FILE" ] || [ ! -f "$ENC_FILE" ]; then
    generate_keys
fi

# Standalone模式
if [ "$TRUBFT_MODE" = "standalone" ]; then
    echo "TruBFT N=$N T=$T B=$B" >&2
    exec python3 -m adaptive.test.honest_party_test \
        -k "$KEYS_FILE" \
        -e "$ECDSA_FILE" \
        -c "$ENC_FILE" \
        -n "$N" \
        -t "$T" \
        -b "$B" \
        -x "$TX"
fi

# Distributed模式
if [ "$TRUBFT_MODE" = "distributed" ]; then
    MY_ID=${TRUBFT_MY_ID:-0}
    VERSION=${TRUBFT_VERSION:-1}
    DELAY=${TRUBFT_DELAY:-50}
    
    echo "TruBFT Distributed N=$N Node=$MY_ID" >&2
    exec python3 -m adaptive.test.honest_party_test_EC2 \
        -k "$KEYS_FILE" \
        -e "$ECDSA_FILE" \
        -c "$ENC_FILE" \
        -s hosts \
        -n "$N" \
        -t "$T" \
        -b "$B" \
        -x "$TX" \
        -v "$VERSION" \
        -a "$DELAY" \
        --my-id "$MY_ID"
fi

exec "$@"

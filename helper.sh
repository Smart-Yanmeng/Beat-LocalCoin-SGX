#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"
PROTOCOL=${1:-acs}
shift 2>/dev/null || true
case "$PROTOCOL" in
    acs) docker build -t trubft:ACS . -q 2>/dev/null; docker-compose run --rm vaba ;;
    beat) docker build -t trubft:TruBFT-None-SGX . -q 2>/dev/null; docker-compose run --rm beat ;;
    beat-localcoin) docker build -t trubft:Beat-Localcoin-PY3 . -q 2>/dev/null; docker-compose run --rm beat-localcoin ;;
    dumbo) sed -i 's/\r$//' run_local_network_test.sh 2>/dev/null; sed -i 's/llall python3/which python3/' run_local_network_test.sh 2>/dev/null; sed -i 's/--P "honeybadger"/--P "dumbo"/' run_local_network_test.sh 2>/dev/null; ./run_local_network_test.sh ${1:-4} ${2:-1} ${3:-1000} ${4:-20} ;;
    *) echo "Usage: ./helper.sh <acs|beat|beat-localcoin|dumbo>"; exit 1 ;;
esac

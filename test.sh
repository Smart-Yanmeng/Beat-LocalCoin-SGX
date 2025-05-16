#!/bin/bash
export LIBRARY_PATH=$LIBRARY_PATH:/usr/lib/x86_64-linux-gnu
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/lib/x86_64-linux-gnu
export PYTHONPATH=~/Beat-LocalCoin/adaptive/commoncoin:~/Beat-LocalCoin/adaptive/ecdsa:~/Beat-LocalCoin/adaptive/threshenc:~/Beat-LocalCoin/adaptive/core:~/Beat-LocalCoin/adaptive:$PYTHONPATH

#rm -f thsig4_1.keys ecdsa1.keys thenc4_1.keys
#python3 -m adaptive.commoncoin.prf_generate_keys 4 2 > thsig4_1.keys
#python3 -m adaptive.ecdsa.generate_keys_ecdsa 4 > ecdsa.keys
#python3 -m adaptive.threshenc.generate_keys 4 2 > thenc4_1.keys
python3 -m adaptive.test.honest_party_test -k thsig4_1.keys -e ecdsa.keys -b 40 -n 4 -t 1 -c thenc4_1.keys
#python3 -m adaptive.test.honest_party_test_EC2 -k thsig4_1.keys -e ecdsa.keys -a 3 -b 10000 -n 4 -t 1 -c thenc4_1.keys -v 1

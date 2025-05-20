# BEAT-LOCAL-COIN ( SGX Based )

> CODE BASED ON ***HONEYBADGER*** PROJECT [> LINK <](https://github.com/amiller/HoneyBadgerBFT)

## The latest test
### Standalone
Test on ***WSL2*** \[ 24H2 with kernel **5.15.167.4-microsoft-standard-WSL2 (Ubuntu 24.04)** ] </br>
Python \[ 3.8 ] </br>
Charm \[ 1.5 ] </br>
Gramine \[ 1.8 ] </br>

### Distributed
Test on 4 ***Aliyun Server*** - Ubuntu 22.04 </br>
SGX \[ 1.22 ] </br>
Python \[ 3.8 ] </br>
Charm \[ 1.5 ] </br>
Gramine \[ 1.8 ] </br>

## QUICK START \[ Make sure the environment is installed ]
> Non-SGX should refer to the todo part of the code
#### Clone the project
```bash
git clone https://github.com/Smart-Yanmeng/Beat-LocalCoin-SGX.git
```
#### Make sure you have a working directory
```bash
cd Beat-LocalCoin-SGX
```
#### Run SGX server (Make sure ports 65430-65436 are not occupied)
```bash
cd adaptive/sgx/
python sgx_counter0.py
python sgx_counter1.py
python sgx_counter2.py
python sgx_judge_est0.py
python sgx_judge_est1.py
python sgx_judge_est2.py
python sgx_decrypt.py
```
#### Standalone
```bash
python3 -m adaptive.test.honest_party_test -k thsig4_1.keys -e ecdsa.keys -b 100 -n 4 -t 1 -c thenc4_1.keys
```
#### Distributed
```bash
python3 -m adaptive.test.honest_party_test_EC2 -k thsig4_1.keys -e ecdsa.keys -a 3 -b 100 -n 4 -t 1 -c thenc4_1.keys -v 1
```
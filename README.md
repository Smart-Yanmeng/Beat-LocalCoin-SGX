# adaptive


version = 1: BEAT (with threshold encryption and threshold signature adavanced from HoneyBadgerBFT)
version = 2: Fast termination ABA (no liveness issue)
version = 4: Cobalt (with BEAT ABA replaced with Cobalt ABA)

for fast
python -m adaptive.commoncoin.prf_generate_keys 6 2 > thsig6_1.keys
python -m adaptive.ecdsa.generate_keys_ecdsa 6 > ecdsa1-f.keys
python -m adaptive.threshenc.generate_keys 6 2 > thenc6_1.keys

#Testing ABA on local machine


python -m adaptive.test.mmr13_test -k thsig4_1.keys -v 1 
python -m adaptive.test.mmr13_test -k thsig6_1.keys -v 2 
python -m adaptive.test.mmr13_test -k thsig4_1.keys -v 4

#Testing BFT on local machine

For version 1 and 4
python -m adaptive.test.honest_party_test -k thsig4_1.keys -e ecdsa.keys -b 10 -n 4 -t 1 -c thenc4_1.keys -v 1

For version 2:
python -m adaptive.test.honest_party_test -k thsig6_1.keys -e ecdsa-f.keys -b 10 -n 6 -t 1 -c thenc6_1.keys -v 2


If you run the following commands, new keys will be generated everytime you run. 
./start.sh $N $t $B $v
./start.sh 4 1 10 1 
This will run n=4 servers, batch size (for each node) = 10, and version 1 (BEAT)

You can also use run.sh

When you see 'Consensus finished', it means everything is done. 

#Testing on EC2 Sample workflow

python utility.py [key] [key]
launch_new_instances('us-east-1',4)

launch_new_instances('us-west-1',4)

launch_new_instances('us-west-2',4)
launch_new_instances('eu-west-1',4)

launch_new_instances('sa-east-1',4)

launch_new_instances('ap-southeast-1',4)

launch_new_instances('ap-southeast-2',4)
launch_new_instances('ap-northeast-1',4)
launch_new_instances('ca-central-1',4)
launch_new_instances('ap-south-1',4)


ipAll()
c(getIP(), 'install_dependencies')
c(getIP(), 'git_pull')
c(getIP(), 'syncKeys')

c(getIP(), 'runProtocol:N,t,B,v,time')
c(getIP(), 'runProtocol:4,1,10,1,3')
c(getIP(), 'runProtocol:4,1,10,2,3')
c(getIP(), 'runProtocol:4,1,10,3,3')


terminate_all_instances('us-east-1')


# Testing Key dist only
c(getIP(), 'syncDistKeys')
c(getIP(), 'runKeyDist:4,1')


Running Simulator.py
(For BEAT)
python Simulator.py <N> <Pool size> <B> <Rounds> 0 <Shuffle or not> -s <Results list from the EC2 evaluation>
python Simulator.py 4 1000 10 20 0 0 -s 1,1,0,1


(For EPIC)

python Simulator.py <N> <Pool size> <B> <Rounds> 1 <Shuffle or not> -s <Results list from the EC2 evaluation> -t <Threshold>

python Simulator.py 4 1000 10 20 1 0 -s 1,1,0,1 -t 5


(For mode 3: select tx from the front of the queues)

python Simulator.py <N> <Pool size> <B> <Rounds> 2 <Shuffle or not> -s <Results list from the EC2 evaluation>
python Simulator.py 4 1000 10 20 2 0 -s 1,1,0,1

(if not shuffle, the output must be 1.0)
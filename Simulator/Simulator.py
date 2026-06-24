import sys
from sets import Set
import random

def sample(poolset,size):
    return random.sample(poolset,size)


def simulate(N, P, B, R, results,shuffle):
    poollist = {}
    for i in range (N):
        poollist[i] = range(P)
    '''if shuffle == 1:
        for i in range(N):
            random.shuffle(poollist[i])'''

    totalNum = 0
    resultset = Set()

    for i in range(R):
        if shuffle == 1:
            for i in range(N):
                random.shuffle(poollist[i])
        txlist = {}
        tmpSet = Set()
        for j in range(N):
            #Each node randomly selects B transactions
            txlist[j] = sample(poollist[j],B)

        for k in range(N):
            bavalue = results[k]
            if bavalue == "1":
                tmp = Set(txlist[int(k)])
                resultset.update(tmp)
                tmpSet.update(tmp)
                for l in range(N):
                    poollist[l] = Set(poollist[l])
                    poollist[l] = poollist[l] - tmp
                    poollist[l] = sorted(list(poollist[l]))

                '''for j in txlist[int(k)]:
                    print j
                    resultset.add(j)
                    tmpSet.add(j)
                    try:
                        for l in range(N):
                            poollist[l].remove(j)
                    except:
                        pass '''
        #print tmpSet
        localresult = float(len(tmpSet)/float(B))
        print "Round", i, "result:", localresult
        totalNum = totalNum + localresult
    
    finalNum = totalNum/R 
    print ("Final result: ", finalNum)

def simulateEPICPlain(N,P,B,R,results,shuffle):
    poollist = {}
    for i in range (N):
        poollist[i] = range(P)
    
    totalNum = 0
    
    resultset = Set()

    for i in range(R):
        txlist = {}
        tmpSet = Set()
        if shuffle == 1:
            for i in range(N):
                random.shuffle(poollist[i])
        for j in range(N):
            #Each node only selects B transactions in front of the queue
            for k in range(B):
                value = poollist[j][k]
                try:
                    txlist[j].append(value)
                except:
                    txlist[j] = []
                    txlist[j].append(value)
        for k in range(N):
            bavalue = results[k]
            if bavalue == "1":
                tmp = Set(txlist[int(k)])
                resultset.update(tmp)
                tmpSet.update(tmp)
                for l in range(N):
                    poollist[l] = Set(poollist[l])
                    poollist[l] = poollist[l] - tmp
                    poollist[l] = sorted(list(poollist[l]))
                '''for j in txlist[int(k)]:
                    resultset.add(j)
                    tmpSet.add(j)
                    try:
                        for l in range(N):
                            poollist[l].remove(j)
                    except:
                        pass '''
        #print tmpSet
        
        localresult = float(len(tmpSet)/float(B))
        print "Round", i, "result:", localresult
        totalNum = totalNum + localresult
    
    finalNum = totalNum/R 
    print ("Final result: ", finalNum)

def simulateEPIC(N, P, B, R, threshold, results, shuffle):
    poollist = {}
    for i in range (N):
        poollist[i] = range(P)

    '''if shuffle == 1:
        for i in range(N):
            random.shuffle(poollist[i])'''
    totalNum = 0
    
    resultset = Set()

    for i in range(R):
        txlist = {}
        tmpSet = Set()
        if shuffle == 1:
            for i in range(N):
                random.shuffle(poollist[i])
        if (i+1)%threshold != 0: #select random value from the list
            for j in range(N):
                #Each node randomly selects B transactions
                txlist[j] = sample(poollist[j],B)
            for k in range(N):
                bavalue = results[k]
                if bavalue == "1":
                    tmp = Set(txlist[int(k)])
                    resultset.update(tmp)
                    tmpSet.update(tmp)
                    for l in range(N):
                        poollist[l] = Set(poollist[l])
                        poollist[l] = poollist[l] - tmp
                        poollist[l] = sorted(list(poollist[l]))
                    '''for j in txlist[int(k)]:
                        resultset.add(j)
                        tmpSet.add(j)
                        try:
                            for l in range(N):
                                poollist[l].remove(j)
                        except:
                            pass '''
        else:
            for l in range(N):
                if (len(poollist[l])>=B):
                    for j in range(B):
                        value = poollist[l][j]
                        try:
                            txlist[l].append(value)
                        except:
                            txlist[l] = []
                            txlist[l].append(value)
                
                else:
                    for j in range(len(poollist[l])):
                        value = poollist[l][j]
                        try:
                            txlist[l].append(value)
                        except:
                            txlist[l] = []
                            txlist[l].append(value)
            for l in range(N):
                bavalue = results[l]
                if bavalue == "1":
                    tmp = Set(txlist[int(k)])
                    resultset.update(tmp)
                    tmpSet.update(tmp)
                    for l in range(N):
                        poollist[l] = Set(poollist[l])
                        poollist[l] = poollist[l] - tmp
                        poollist[l] = sorted(list(poollist[l]))
                    '''for j in txlist[int(l)]:
                        resultset.add(j)
                        tmpSet.add(j)
                        try:
                            for k in range(N):
                                poollist[k].remove(j)
                        except:
                            pass '''
                
        localresult = float(len(tmpSet)/float(B))
        print "Round", i, "result:", localresult
        totalNum = totalNum + localresult
    
    finalNum = totalNum/R 
    print ("Final result: ", finalNum)

if __name__=='__main__':
    print "Simulating Transaction Selection Behavior for BEAT-like Protocol..."

    N = int(sys.argv[1])
    P = int(sys.argv[2])
    B = int(sys.argv[3])
    R = int(sys.argv[4])
    v = int(sys.argv[5])
    shuffle = int(sys.argv[6])

    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-s", "--results", dest="results",
                      help="results of BA output", metavar="S", type="string")
    parser.add_option("-t", "--threshold", dest="threshold",
                      help="threshold of how often we select tx in front of th pool", metavar="T", type="int")

    (options, args) = parser.parse_args()

    results = options.results.split(",")
    if len(results) != N:
        print ("The size of the results should be the same with N")
        exit()

    print "testing N = %d, P = %d, B = %d, R = %d"% (N, P, B, R) 
    print results


    if v== 0:
        simulate(N,P,B,R,results,shuffle)
    elif v == 1:
        if not options.threshold:
            print "please enter the threshold value"
            exit()
        threshold = options.threshold
        if threshold > R:
            print ("for simulator, we usually test it when threshold is smaller than the rounds of simulation")
            exit()
        simulateEPIC(N,P,B,R,threshold,results,shuffle)
    elif v == 2:
        simulateEPICPlain(N,P,B,R,results,shuffle)
    print "done"
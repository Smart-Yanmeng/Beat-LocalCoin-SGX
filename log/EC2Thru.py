

import os
import sys

#need absolute path
def main(directory, N):
    
    total_num = 0
    rounds = []
    values = []
    throughput = []
    total_throughput = 0.0

    for filename in sorted(os.listdir(directory)):
        total_num = total_num + 1
        f = open(directory+'/'+filename)
        try:
            B = int(filename.split(".")[0])
        except:
            continue
        #print B
        lines = f.readlines()
        currentrounds = 0.0
        currentvalues = 0.0
        total_time = []
        total_timee = []
        numbers = 0
        numbere = 0
        for line in lines:
            try:
                line = line.split("out: ")[1]
            except:
                continue
            #print line
            if line.startswith('[Finishing Time '):
                total_time.append(float(line.split(", ")[1]))
                numbers += 1
            if line.startswith('[Finishing TimeE'):
                total_timee.append(float(line.split(", ")[1]))
                numbere += 1
            if line.startswith('[PID: 0'):
                currentrounds = currentrounds + float(line.split(",")[1].split(":")[1])
                number = int(line.split(",")[0].split(": ")[2])
                if number == 1:
                    currentvalues += 1.0
       
        #print total_time
        #print total_timee
        rounds.append(currentrounds/N)
        values.append(currentvalues)
        cur_thru = 0.0
        avg_tm = tm/numbers
        
        cur_thru = cur_thru/numbers
        throughput.append(cur_thru)
        total_throughput += cur_thru
        #print "(%d, %d)"%(B,cur_thru), #if printing throughput chart, uncomment this
        print "(%d, %f)"%(cur_thru,avg_tm), #if printing lat vs throughput chart, uncomment this

    print "\n rounds", rounds
    print "values", values
    print "throughput", throughput
    print "avg throughput", total_throughput/total_num
    print "avg rounds %f, avg values %f"%(sum(rounds)/total_num, sum(values)/total_num)

if __name__=='__main__':
    #directory, N
    main(sys.argv[1],int(sys.argv[2]))
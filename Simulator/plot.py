import sys

if __name__=='__main__':
    print ("generating results for figures in latex")

    number = sys.argv[1]
    numbers = number.split(" ")
    if len(numbers)!=9:
        print ("the input numbers may not be correct")
        exit()
    cnt = 0
    for i in (1,50,100,500,1000,2000,5000,8000,10000):
        print ("(%d, %s) "%(i, numbers[cnt]), end='')
        cnt += 1
    print ("")
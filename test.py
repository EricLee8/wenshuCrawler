import queue
import multiprocessing as mp
from multiprocessing import Lock
import os, time, random

mutex = Lock()
file_name = "test.txt"
num = 0

def data_process(letter):
    global num
    print('Run task %s (%s)...' % (letter, os.getpid()))
    text = ""
    time.sleep(0.05)
    for _ in range(10000):
        text = text + letter
    num += 2
    print(num)
    return text



def main():
    p = mp.Pool(4)
    for i in range(4):
        p.apply_async(data_process, args=(str(i)))
    p.close()
    p.join()
    print("Finished!")
    print(num)

if __name__=='__main__':
    main()

import tc_full
from datetime import datetime,time
import numpy as np
from pathos.helpers import freeze_support 
import os
from inspect import getsourcefile
from os.path import abspath

def main():
    #start_date = datetime(2016,1,1,0,0,0);
    #end_date = datetime(2016,6,1,0,0,0);
    start_date = datetime(2001,01,01,0,0,0);
    end_date = datetime(2017,01,10,0,0,0); # 2017,1,10,0,0,0 (general end point for all sats)
    localpath = abspath(getsourcefile(lambda:0))[:-8] # gets path and removes file from it
    
    satlist = [41,48,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73]
    #satlist = [53,59,60,61]
    
    #L_thres = np.arange(0.000,0.070,0.001) # 0.000 might return nothing, but we might have data there...
    L_thres = np.arange(1.0,70.0,1.0) / 1000 # floating point fun fix. Work with Int then divide down.
    #alt2test = [i * 100 for i in [0,1,2,3,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20]]
    intalt = 400
    alt2test = [i * 100 for i in range(20)]
    alt2test.remove(intalt)
    maxsizeondisk = 100 # given in GB.
    threads = 6
    
    tc = tc_full.temporal_correlation(start_date, end_date, satlist, localpath, maxsizeondisk, threads)
    #tc.runtc(alt2test, L_thres, karg=1)
    tc.finish()





if __name__ == '__main__':
    freeze_support()
    #print abspath(getsourcefile(lambda:0))[:-8]
    main()

















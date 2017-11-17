import tc_full
from datetime import datetime
import numpy as np
from pathos.helpers import freeze_support 



def main():
    start_date = datetime(2016,1,1,0,0,0);
    end_date = datetime(2017,1,1,0,0,0);
    localpath = 'D:\\jackj\\Documents\\GitHub\\EQPB_2017\\'
    satlist = [41,48]
    
    L_thres = np.arange(0.01,0.07,0.01)
    #L_thres = [0.005,0.03,0.07,0.10,0.13,0.17]
    alt2test = [i * 100 for i in [1,4,8,12,16,20]]
    maxsizeondisk = 100 # given in GB.
    threads = 6

    
    tc = tc_full.temporal_correlation(start_date, end_date, satlist, localpath, maxsizeondisk, threads)
    tc.runtc([400], alt2test, L_thres) # intalt needs to be an array as it's treated like alt2test.





if __name__ == '__main__':
    freeze_support()
    main()









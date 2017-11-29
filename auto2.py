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
    start_date = datetime(2015,12,20,0,0,0);
    end_date = datetime(2017,1,10,0,0,0);
    #localpath = 'D:\\jackj\\Documents\\GitHub\\EQPB_2017\\'
    #localpath = os.path.dirname(os.path.realpath(__file__)) #has issues if ran from IDE/interp
    localpath = abspath(getsourcefile(lambda:0))
    satlist = [70]
    
    #L_thres = np.arange(0.000,0.070,0.001) # 0.000 might return nothing, but we might have data there...
    L_thres = np.arange(1.0,70.0,1.0) / 1000 # floating point fun fix. Work with Int then divide down.
    #L_thres = [0.005,0.03,0.07,0.10,0.13,0.17]
    #alt2test = [i * 100 for i in [0,1,2,3,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20]]
    intalt = 400
    alt2test = [i * 100 for i in range(20)]
    alt2test.remove(intalt)
    maxsizeondisk = 100 # given in GB.
    threads = 6

    print L_thres
    
    tc = tc_full.temporal_correlation(start_date, end_date, satlist, localpath, maxsizeondisk, threads)
    tc.runtc(alt2test, L_thres, karg=3, new_L=[[0.005,0.029,0.062]])
    """
        mode 1 is the default mode.
        
        mode | TC | confpeak | alt | plot tc/alt | plot conf |||
        0      x       x        x                  tc   alt  ||| confpeak isn't the most accurate thing in the world.
        1      x       x                           tc        ||| requires manual analysis of peaks. Combine with mode 3.
        2              x        x                       alt  ||| auto discover peaks and alt test them.
        3                       x                       alt  ||| provide new_L values to test.
        4              x                  x        tc   alt  ||| plots all histograms and all conf plot; Also gives conf peaks.
        5              x                           tc   alt  ||| plots conf; Also gives conf peaks.
        6+                                                   ||| N/A
        
        runtc(self, alt2test, L_thres, intalt = 400, new_L = None, karg = 1, vsmooth = 9)
        """





if __name__ == '__main__':
    freeze_support()
    main()

















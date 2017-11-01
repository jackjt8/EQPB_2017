import gps_particle_dataMOD
import wget
import os
import numpy as np 
import time
import json
import sys
import math
from datetime import datetime, timedelta, date
from itertools import compress
from random import randint
import urllib2
import aacgmv2
import scipy
import matplotlib
from matplotlib import gridspec
import numpy as np
import matplotlib.pyplot as plt
from multiprocessing import Pool
from itertools import repeat

# This warning suppression is NOT a good idea by any means.
# https://docs.python.org/2/library/warnings.html#temporarily-suppressing-warnings
# need to put part of code that causes the issue into a function.
import warnings
warnings.simplefilter("ignore", RuntimeWarning) 

#%matplotlib inline 


start_time = time.clock()
def tc_fw((n, dday, ls, indices, L_shells, eq_datetimes, lthres)):
    # setup the current file we are using
    # removes deciaml point for lthres
    slthres = ''.join(e for e in str(lthres) if e.isalnum())
    # file...
    current_file = 'Ltemp_' + str(n) + '_' + slthres + '.ascii'

    his_data = [] #not sure this one is necessary?
    #trying to match EQ and PB based on two conditions: delta T < 0.5 days and delta L (in this case) < 1
    for i in indices:
        for j in range(len(L_shells)):
            #datet was date
            datet = datetime.strptime(str(eq_datetimes[j])[:10], "%Y-%m-%d")
            int_diy = datet.timetuple().tm_yday
            rest = (float(str(eq_datetimes[j])[11:13])/24) + (float(str(eq_datetimes[j])[14:16])/(24*60))+(float(str(eq_datetimes[j])[17:19])/(24*3600))
            diy = int_diy + rest
            del_T = dday[i]-diy
            del_L = ls[i]-L_shells[j]
            if abs(del_L) < lthres and  abs(del_T) < 0.5: # lthres use to be 1.
                dT = del_T*24
                #append it to the file
                with open(current_file, 'a') as f:
                    np.savetxt(f, dT)

def main():
	start_time = time.clock()
	start_date = datetime(2001,1,1,0,0,0);
	end_date = datetime(2017,1,1,0,0,0);
	localpath = 'D:\\jackj\\Documents\\GitHub\\'
	satlist = [41]
	L_thres = np.arange(0.01,0.31,0.01)
	#alt = np.arange(0.0,805.0,5.0) # 0 to 800 in km

	
	#Get Sat data
	ms = gps_particle_dataMOD.meta_search(satlist,localpath)
	ms.load_local_data(start_date,end_date)

	#Get earthquakes for given conditions
	eq_s = gps_particle_dataMOD.earthquake_search(start_date,end_date, min_magnitude=4,min_lat=-90,max_lat=90,min_lon=-180,max_lon=180)
	#Calculate L-shells of the earthquakes
	L_shells = eq_s.get_L_shells(400.0)
	#EQ datetimes
	eq_datetimes = eq_s.get_datetimes()

	n = 41

	output_data = ms.get_all_data_by_satellite()
	signame = 'rate_electron_measured';
	#calculations performed w.r.t. channel 2 (electron rates)
	ch2 = np.asarray(output_data[n][signame])[:,2]
	#get avg and stddev
	avg = np.mean(signal)
	stddev = np.std(signal)
	#find difference between signal and average
	sig_dif = np.subtract(ch2, avg)
	#ratio in terms of std dev
	ratio = np.divide(sig_dif, stddev)

	indices = []
	burst_indices = ratio>4

	#get indices of the signal points with sig_dif value > 4 sigma
	for i in range(len(burst_indices)):
		if burst_indices[i] == True:
			indices.append(i)

	dday = output_data[n]['decimal_day']
	ls = output_data[n]['L_shell']

	#Need to clear ms and eq_s to save memory.
	
	print 'Time to complete prep: ' + str(time.clock() - start_time)
	
	threads = 8
	start_time = time.clock()
	mthandler(n,dday,ls,indices,L_shells,eq_datetimes,L_thres,threads)
	print 'Time to complete MT section: ' + str(time.clock() - start_time)


#https://stackoverflow.com/questions/25553919/passing-multiple-parameters-to-pool-map-function-in-python
def mthandler(n,dday,ls,indices,L_shells,eq_datetimes,L_thres,threads):
    pool = Pool(threads)
    #L_thres is our iterable
    temp = zip(repeat(n), repeat(dday), repeat(ls), repeat(indices), repeat(L_shells), repeat(eq_datetimes),L_thres)
    pool.map(tc_fw, temp)
    pool.close()
    pool.join()

if __name__ == '__main__':
	main()


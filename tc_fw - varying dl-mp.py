import gps_particle_data
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
%matplotlib inline 

#######

start_time = time.clock()
start_date = datetime(2016,1,1,0,0,0);
end_date = datetime(2017,1,1,0,0,0);
satlist = [56]
#L_thres = np.arange(0.01,0.21,0.01)
L_thres = [0.05,0.07,0.10,0.20]
#alt = np.arange(0.0,805.0,5.0) # 0 to 800 in km

ms = gps_particle_data.meta_search(satlist); 

ms.load_data(start_date,end_date);
print "--- meta_search: %s seconds ---" % (time.clock() - start_time)

#######

#Get earthquakes for given conditions
eq_s = gps_particle_data.earthquake_search(start_date,end_date, min_magnitude=4,min_lat=-90,max_lat=90,min_lon=-180,max_lon=180)
#Calculate L-shells of the earthquakes
L_shells = eq_s.get_L_shells(400.0)
#EQ datetimes
eq_datetimes = eq_s.get_datetimes()
print "--- EQ_search, get L shells: %s seconds ---" % (time.clock() - start_time)

#######

n = 56

#find mean and standard deviation for given period of time
output_data = ms.get_all_data_by_satellite()
signame = 'rate_electron_measured';
signal = np.asarray(output_data[n][signame])[:,2];
avg = np.mean(signal)
stddev = np.std(signal)
#print avg, stddev
print "--- avg, stddev: %s seconds ---" % (time.clock() - start_time)
######

r = output_data[n][signame]
#calculations performed w.r.t. channel 2 (electron rates)
ch2 = np.asarray(r)[:,2]
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
print "--- Get indices of Particle Bursts: %s seconds ---" % (time.clock() - start_time)

#######

data = []
    
for x in satlist:
    for y in L_thres:
        data.append(output_data[x]) # append output data
        data.append(x) # append n
        data.append(y) # append lthres
        print x,y
print "--- Pre-MT: %s seconds ---" % (time.clock() - start_time)

#######

import multiprocessing


def mp_worker((output_data, n, lthres,L_shells)):
    # setup the current file we are using
    # removes deciaml point for lthres
    slthres = ''.join(e for e in str(lthres) if e.isalnum())
    # file...
    current_file = 'Ltemp_' + str(n) + '_' + slthres + '.ascii'
    
    print '=== %s --- START' % (current_file)

    his_data = [] #not sure this one is necessary?
    dday = output_data[n]['decimal_day']
    ls = output_data[n]['L_shell']
    #trying to match EQ and PB based on two conditions: delta T < 0.5 days and delta L (in this case) < 1
    for i in indices:
        for j in range(len(L_shells)):
            date = datetime.strptime(str(eq_datetimes[j])[:10], "%Y-%m-%d")
            int_diy = date.timetuple().tm_yday
            rest = (float(str(eq_datetimes[j])[11:13])/24) + (float(str(eq_datetimes[j])[14:16])/(24*60))+(float(str(eq_datetimes[j])[17:19])/(24*3600))
            diy = int_diy + rest
            del_T = dday[i]-diy
            del_L = ls[i]-L_shells[j]
            if abs(del_L) < lthres and  abs(del_T) < 0.5: # lthres use to be 1.
                dT = del_T*24
                #print dT, ls[i]
                #append it to the file
                with open(current_file, 'a') as f:
                    np.savetxt(f, dT)
    print '=== %s COMPLETED' % (current_file)

def mp_handler():
    p = multiprocessing.Pool(4)
    p.map(mp_worker, data)

if __name__ == '__main__':
    mp_handler()
    print ' '
    print "--- Total time taken: %s seconds ---" % (time.clock() - start_time)

#######    
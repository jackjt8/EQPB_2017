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
from multiprocessing import Pool
from itertools import repeat
import shutil

# This warning suppression is NOT a good idea by any means.
# https://docs.python.org/2/library/warnings.html#temporarily-suppressing-warnings
# need to put part of code that causes the issue into a function.
import warnings
warnings.simplefilter("ignore", RuntimeWarning) 

#%matplotlib inline 

#%%

def tc_fw((localpath, n, dday, ls, indices, L_shells, eq_datetimes, satalt, bcoord, lthres)):
    print 'Working on %s' % (lthres)
    start_time = time.clock()
    # setup the current file we are using
    # removes deciaml point for lthres
    slthres = ''.join(e for e in str(lthres) if e.isalnum())
    # file...
    current_file = 'Ltemp_' + str(n) + '_' + slthres + '.ascii'

    his_data = [] #not sure this one is necessary?
    #trying to match EQ and PB based on two conditions: delta T < 0.5 days and delta L (in this case) < 1
    print 'indices = %s ; L_shells = %s ; indices*L_shells = %s' % (len(indices),len(L_shells),len(indices)*len(L_shells))
    for i in indices:
        for j in range(len(L_shells)):
            #datet was date
            datet = datetime.strptime(str(eq_datetimes[j])[:10], "%Y-%m-%d")
            int_diy = datet.timetuple().tm_yday
            rest = (float(str(eq_datetimes[j])[11:13])/24) + (float(str(eq_datetimes[j])[14:16])/(24*60))+(float(str(eq_datetimes[j])[17:19])/(24*3600))
            diy = int_diy + rest
            #del_T = dday[i]-diy
            del_T = diy-dday[i]
            #del_L = ls[i]-L_shells[j]
            del_L = L_shells[j]-ls[i]
            if abs(del_L) < lthres and  abs(del_T) < 2: # lthres use to be 1.
                dT = del_T*24
                #append it to the file
                with open(localpath + current_file, 'a') as f:
                    # Save satalt[i] bcoord[i]
                    #np.savetxt(f, dT)
                    #https://stackoverflow.com/questions/16621351/how-to-use-python-numpy-savetxt-to-write-strings-and-float-number-to-an-ascii-fi
                    DAT = np.asarray([dT, satalt[i], bcoord[i]])
                    np.savetxt(f, DAT[None], delimiter=' ')
    if os.path.isfile(localpath + current_file) == True:
        dst = localpath + 'data\\var_dL\\' + 'ns' + str(n) + '\\'
        shutil.move(localpath + current_file, dst + current_file)
                    
    print 'Finished working on %s. Time taken: %s' % (lthres,(time.clock() - start_time))
                    
#https://stackoverflow.com/questions/25553919/passing-multiple-parameters-to-pool-map-function-in-python
def mthandler(localpath,n,dday,ls,indices,L_shells,eq_datetimes,satalt,bcoord,L_thres,threads):
    pool = Pool(threads)
    #L_thres is our iterable
    temp = zip(repeat(localpath),repeat(n), repeat(dday), repeat(ls), repeat(indices), repeat(L_shells), repeat(eq_datetimes),repeat(satalt),repeat(bcoord),L_thres)
    pool.map(tc_fw, temp)
    pool.close()
    pool.join()
    
def main(start_date,end_date,localpath,satlist,L_thres,maxsizeondisk,threads):
    timeforend = time.clock()
    
#    start_date = datetime(2001,1,1,0,0,0);
#    end_date = datetime(2017,1,1,0,0,0);
#    localpath = 'D:\\jackj\\Documents\\GitHub\\EQPB_2017\\'
#    satlist = [41]
#    #L_thres = np.arange(0.01,0.21,0.01)
#    #L_thres = [0.022, 0.024, 0.026, 0.028, 0.032, 0.034, 0.036, 0.038]
#    #L_thres = [0.122, 0.124, 0.126, 0.128, 0.132, 0.134, 0.136, 0.138]
#    #alt = [1,2,3,4,5,6,7,8,16,32,64,96,128,150,192,224,256,288]*100
#    maxsizeondisk = 100 # given in GB.
#    threads = 8
    
    #%%
    localfolder = 'data\\'
    rawf = 'raw\\'
    vdl = 'var_dL\\'
    valt = 'var_alt\\'
        
    print 'Path on disk: %s' % (localpath)
    print 'Satlist: %s' % (satlist)
    print 'Start datetime: %s end datetime: %s' % (start_date, end_date)
    print 'dL Values to test: %s' % (L_thres)
    print '###'
    
    #%%
    #Check if gps sat data exists. Download if missing.
    gps_particle_data.gps_satellite_data_download(start_date,end_date,satlist,localpath,maxsizeondisk)
    
    #main loop
    for this_sat in satlist:
        print ''
        print 'Working on %s...' % (this_sat)
        #%%
        start_time = time.clock()
        # Load data.
        ms = gps_particle_data.meta_search(this_sat,localpath) # Do not pass meta_search satlist. Single sat ~12GB of RAM.
        ms.load_local_data(start_date,end_date)
        ms.clean_up() #deletes json files.
        print ''
    
        #%%
    
        #Get earthquakes for given conditions
        eq_s = gps_particle_data.earthquake_search(start_date,end_date, min_magnitude=4,min_lat=-90,max_lat=90,min_lon=-180,max_lon=180)
        print ''
        #Calculate L-shells of the earthquakes
        L_shells = eq_s.get_L_shells(400.0)
        #EQ datetimes
        eq_datetimes = eq_s.get_datetimes()
    
        #%%
    
        output_data = ms.get_all_data_by_satellite()
        
        ddata = output_data[this_sat]['dropped_data']
        index2drop = [i for i, j in enumerate(ddata) if j == 1]
        
        #load data into temp array
        temp_rem2 = np.asarray(output_data[this_sat]['rate_electron_measured'])[:,2]
        ch2 = np.delete(temp_rem2,index2drop)
        
        temp_dday =  output_data[this_sat]['decimal_day']
        dday = np.delete(temp_dday,index2drop)
        
        temp_ls = output_data[this_sat]['L_shell']
        ls = np.delete(temp_ls,index2drop)
        
        temp_alt = output_data[this_sat]['Rad_Re']
        satalt = np.delete(temp_alt,index2drop)
        
        temp_bcoord = output_data[this_sat]['b_coord_radius']
        bcoord = np.delete(temp_bcoord,index2drop)
        
        #%%
        
        #get avg and stddev
        avg = np.mean(ch2)
        stddev = np.std(ch2)
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
    
        #%%
    
        #Need to clear ms and eq_s to save memory.
        
        #%%
        
        print 'Time to complete prep for %s: %s' % (this_sat, time.clock() - start_time)
        print ''
        
        start_time = time.clock()
        #n,dday,ls,indices,L_shells,eq_datetimes,L_thres,threads
        #n,dday,ls,indices,L_shells,eq_datetimes,satalt,bcoord,L_thres,threads
        mthandler(localpath,this_sat,dday,ls,indices,L_shells,eq_datetimes,satalt,bcoord,L_thres,threads)
        print 'Time to complete dL testing for %s: %s' % (this_sat, time.clock() - start_time)
        print '%s finished, moving on...' % (this_sat)
        print ''
        
    #end
    print '###'
    print 'Finished job in %s' % (time.clock() - timeforend)
    print 'Path on disk: %s' % (localpath)
    print 'Satlist: %s' % (satlist)
    print 'Start datetime: %s end datetime: %s' % (start_date, end_date)
    print 'dL Values to tested: %s' % (L_thres)

if __name__ == '__main__':
    start_date = datetime(2012,1,1,0,0,0);
    end_date = datetime(2017,1,1,0,0,0);
    localpath = 'D:\\jackj\\Documents\\GitHub\\EQPB_2017\\'
    satlist = [41]
    L_thres = np.arange(0.01,0.21,0.01)
    maxsizeondisk = 100 # given in GB.
    threads = 8
    
    #%%
    main(start_date,end_date,localpath,satlist,L_thres,maxsizeondisk,threads)


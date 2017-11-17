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
#from multiprocessing import Pool
from pathos.multiprocessing import ProcessingPool as Pool
from itertools import repeat
import shutil
import peakutils

class temporal_correlation():
    def __init__(self, start_date, end_date, satlist, localpath, maxsizeondisk, threads):
        self.start_date = start_date
        self.end_date = end_date
        self.satlist = satlist
        self.localpath = localpath
        self.maxsizeondisk = maxsizeondisk
        self.threads = threads
        
        self.localfolder = 'data\\'
        self.rawf = 'raw\\'
        self.prof = 'processed\\'
        
        #Check if gps sat data exists. Download if missing.
        gps_particle_data.gps_satellite_data_download(self.start_date, self.end_date, self.satlist, self.localpath, self.maxsizeondisk)
        
    def runtc(self, intalt, alt2test, L_thres):
        for this_sat in self.satlist:
            dday, ls, satalt, bcoord, indices, eq_datetimes, L_shells = self.dataprep(this_sat,intalt)
            self.mthandler(this_sat, dday, ls, satalt, bcoord, indices, eq_datetimes, L_shells, L_thres, intalt)
        #%%
        tcp = temporal_correlation_plot(self.localpath, self.satlist)
        new_L = tcp.get_confpeaks(intalt)
        #%%
        i = 0
        for this_sat in self.satlist:
            dday, ls, satalt, bcoord, indices, eq_datetimes, L_shells = self.dataprep(this_sat, alt2test)
            self.mthandler(dday, ls, satalt, bcoord, indices, eq_datetimes, L_shells, new_L[i], alt2test)
            i += 1
    
    def dataprep(self, this_sat, alt2test):
        print ''
        print 'Path on disk: %s' % (self.localpath)
        print 'Satlist: %s' % (self.satlist)
        print 'Start datetime: %s end datetime: %s' % (self.start_date, self.end_date)
        print '###'
        
        print ''
        print 'Working on %s...' % (this_sat)
        #%%
        start_time = time.clock()
        # Load data.
        ms = gps_particle_data.meta_search(this_sat, self.localpath) # Do not pass meta_search satlist. Single sat ~12GB of RAM.
        ms.load_local_data(self.start_date, self.end_date)
        ms.clean_up() #deletes json files.
        print ''
    
        #%%
    
        #Get earthquakes for given conditions
        eq_s = gps_particle_data.earthquake_search(self.start_date, self.end_date, min_magnitude=4,min_lat=-90,max_lat=90,min_lon=-180,max_lon=180)
        print ''
        #Calculate L-shells of the earthquakes
        L_shells = []
        for alt in alt2test:
            L_shells.append(eq_s.get_L_shells(alt))
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
        
        """ Sat - dday, ls, satalt, bcoord, indices
            other  - eq_datetimes, L_shells
        """
        return dday, ls, satalt, bcoord, indices, eq_datetimes, L_shells
        
    def mthandler(self, this_sat, dday, ls, satalt, bcoord, indices, eq_datetimes, L_shells, L_thres, alt2test): 
        if len(alt2test) == 1:
            #for L_thres in msL_thres[self.satlist.index(this_sat)]:
            print 'Case alt2test = 1'
            #print L_shells
            pool = Pool(self.threads)
            #temp = zip(repeat(self.localpath), repeat(this_sat), repeat(dday), repeat(ls), repeat(satalt),repeat(bcoord), repeat(indices), repeat(eq_datetimes), repeat(L_thres), L_shells, alt2test)
            pool.map(self.tc_fw, repeat(self.localpath), repeat(this_sat), repeat(dday), repeat(ls), repeat(satalt),repeat(bcoord), repeat(indices), repeat(eq_datetimes), L_thres, repeat(L_shells[0]), repeat(alt2test))
            #pool.close()
            #pool.join()
            pool.clear()
        else:
            print 'Case alt2test != 1'
            pool = Pool(self.threads)
            #temp = zip(repeat(self.localpath), repeat(this_sat), repeat(dday), repeat(ls), repeat(satalt),repeat(bcoord), repeat(indices), repeat(eq_datetimes), repeat(L_thres), L_shells, alt2test)
            pool.map(self.tc_fw, repeat(self.localpath), repeat(this_sat), repeat(dday), repeat(ls), repeat(satalt),repeat(bcoord), repeat(indices), repeat(eq_datetimes), repeat(L_thres), L_shells, alt2test)
            #pool.close()
            #pool.join()
            pool.clear()
                
    def tc_fw(self, localpath, this_sat, dday, ls, satalt, bcoord, indices, eq_datetimes, lthres, L_shells, alt):
        print 'Working on %s with dL=%s at %s km | Total tests: %s' % (this_sat,lthres,alt,len(indices)*len(L_shells))
        start_time = time.clock()
        # setup the current file we are using
        # removes deciaml point for lthres
        # file...
        slthres = str(lthres).replace('.','d')
        salt = ''.join(e for e in str(alt) if e.isalnum())
        current_file = 'tc_ns' + str(this_sat) + '_' + salt + '_' + slthres + '.ascii'

        his_data = [] #not sure this one is necessary?
        #trying to match EQ and PB based on two conditions: delta T < 0.5 days and delta L (in this case) < 1
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
                if abs(del_L) < lthres and  abs(del_T) < 0.5: # lthres use to be 1.
                    dT = del_T*24
                    #append it to the file
                    #print 'append'
                    with open(localpath + current_file, 'a') as f:
                        #print 'write'
                        # Save satalt[i] bcoord[i]
                        #np.savetxt(f, dT)
                        #https://stackoverflow.com/questions/16621351/how-to-use-python-numpy-savetxt-to-write-strings-and-float-number-to-an-ascii-fi
                        DAT = np.asarray([dT, satalt[i], bcoord[i]])
                        np.savetxt(f, DAT[None], delimiter=' ')
        if os.path.isfile(localpath + current_file) == True:
            dst = localpath + self.localfolder + self.prof + 'ns' + str(this_sat) + '\\'
            shutil.move(localpath + current_file, dst + current_file)
                        
        print 'Finished working on %s-%s. Time taken: %s' % (lthres,alt,(time.clock() - start_time))
                                    
                
class temporal_correlation_plot():
    def __init__(self, localpath, satlist):
        self.localpath = localpath
        self.satlist = satlist
    
    
    def get_confpeaks(self, alt):
        new_L = []
        for this_sat in self.satlist:
            #print 'get_confpeaks'
            localfolder = 'data\\'
            rawf = 'raw\\'
            prof = 'processed\\'
            
            path = self.localpath + localfolder + prof + 'ns' + str(this_sat) + '\\'
            filelist,L_thres,altvals = self.get_FL_L_A(path)
            
            conflvl = []
            tempL = []
            
            for i in range(len(filelist)):
                if i == altvals.index(alt):
                    conflvl.append(self.get_conflvl(path,filelist[i],this_sat,L_thres[i]))
            #cb = np.array(smooth(conflvl,5))
            print conflvl
            cb = np.array(conflvl)
            indices = peakutils.indexes(cb, thres=0.02/max(cb), min_dist=0.1)
            for lthres in indices:
                tempL.append(L_thres[lthres])
            new_L.append(tempL)
        return new_L
    
    
    def get_FL_L_A(self, path):
        extension = '.ascii'
        dirlist = os.listdir(path)
        
        filelist = []
        L_thres = []
        altvals = []
        
        for item in dirlist:
            if item.endswith(extension):
                filelist.append(item)
                L_thres.append(float(str(item[12:-6]).replace('d','.')))
                altvals.append(int(item[8:-12]))

        return filelist,L_thres,altvals
    
    
    def get_conflvl(path, current_file, this_sat, lthres):
        # setup the current file we are using
        
        print '=== %s' % (current_file)
        
        curdata = np.loadtxt(path + current_file)
        #convert the data into histogram bins.
        bins = np.arange(min(curdata[:,0]), max(curdata[:,0])+1)
        hist, bin_edges = np.histogram(curdata[:,0],bins)
        
        # n{sig} = (Nmax - Nbg/{sig})     taken from S. Yu Aleksandrin et al.: High-energy charged particle bursts
        Nmax = max(hist)
        Nbg = np.median(hist)
        sig = np.std(hist) 
        nsig = (Nmax - Nbg)/sig
        return nsig
                
#    
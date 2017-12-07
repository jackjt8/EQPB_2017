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
from pathos.helpers import freeze_support 
import os
from inspect import getsourcefile
from os.path import abspath

def main():
    #start_date = datetime(2016,1,1,0,0,0);
    #end_date = datetime(2016,6,1,0,0,0);
    # Give dates +/- 7 days at least as a buffer.
    start_date = datetime(2001,1,1,0,0,0);
    end_date = datetime(2001,6,1,0,0,0); # 2017,1,10,0,0,0 (general end point for all sats)
    #localpath = 'D:\\jackj\\Documents\\GitHub\\EQPB_2017\\'
    #localpath = os.path.dirname(os.path.realpath(__file__)) #has issues if ran from IDE/interp
    localpath = abspath(getsourcefile(lambda:0))[:-10] # gets path and removes file from it
    satlist = [53]
    
    L_thres = np.arange(1.0,70.0,1.0) / 1000 # 0.001-->0.07
    #L_thres = np.linspace(0.0001,0.2,50)
    #alt2test = [i * 100 for i in [0,1,2,3,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20]]
    intalt = 400
    alt2test = [i * 100 for i in range(1,20,1)]
    alt2test.remove(intalt)
    maxsizeondisk = 100 # given in GB.
    threads = 6
    
    
    print ''
    print 'Path on disk: %s' % (localpath)
    print 'Satlist: %s' % (satlist)
    #print 'Intalt: %s' % (intalt)
    #print 'Altitudes to test: %s' % (alt2test)
    #print 'dLs to test: %s' % (L_thres)
    print 'Start datetime: %s end datetime: %s' % (start_date,end_date)
    print '=Threads to use: %s' % (threads)
    print '###'
    
    
    ### Download EQs ###
    #Get earthquakes for given conditions
    #print "Getting EQs..."
    #eq_s = gps_particle_data.earthquake_search()
    #eq_s.eq_search(start_date, end_date, min_magnitude=4,min_lat=-90,max_lat=90,min_lon=-180,max_lon=180)
    #Save info to file
    #eq_s.save_info()
    #sys.exit()


    for this_sat in satlist:

	### Dataprep ###

        print ''
        print 'Working on %s...' % (this_sat)
	print ''
    
        #%%
        start_time = time.clock()
        # Load data.
	print "Waiting on meta search... (GPS data load)"
        ms = gps_particle_data.meta_search(this_sat,localpath) # Do not pass meta_search satlist. Single sat ~12GB of RAM.
        ms.load_local_data(start_date,end_date)
        ms.clean_up() #deletes json files.
	print "Finished loading GPS data"

        #Load EQ info
	print "Loading EQs..."
        eq_s = gps_particle_data.earthquake_search()
        eq_s.load_info()
	print "Finished loading EQs"

        #Calculate L-shells of the earthquakes
	print "Calculating L-shells.."
        L_shells = []
        for alt in alt2test:
	    #print alt
            L_shells.append(eq_s.get_L_shells(alt))
	print "Calculated L-shells"

        #EQ datetimes
        eq_datetimes = eq_s.get_datetimes() 
    	print "Finished working with EQs"
    
	print "Working on data to ignore..."
	print 'bbb'
        output_data = ms.get_all_data_by_satellite()
        
        # improved drop data -- gets indices of data to drop. (numpy works with indices mainly)
        ddata = np.array([i for i, j in enumerate(output_data[this_sat]['dropped_data']) if j == 1])
        temp_ch2 = np.asarray(output_data[this_sat]['rate_electron_measured'])[:,2]
        dch2 = np.where(temp_ch2 > 50000)[0]
        dalt = np.array([i for i, j in enumerate(output_data[this_sat]['Rad_Re']) if j <= 3.5 or j >= 4.75])
    
        # combines to create new drop list
        index2drop = np.unique(np.concatenate((ddata,dch2,dalt)))
        #print index2drop
    
        # applies drop to data    
        ch2 = np.delete(temp_ch2,index2drop)
        dday = np.delete(output_data[this_sat]['decimal_day'],index2drop)
        ls = np.delete(output_data[this_sat]['L_shell'],index2drop)
        satalt = np.delete(output_data[this_sat]['Rad_Re'],index2drop)
        bcoord = np.delete(output_data[this_sat]['b_coord_radius'],index2drop)
        
        #%%
        
	print "Finding particle burts..."
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
    


    ### TC ###
	#!!! Run this after dataprep

    	tc = temporal_correlation(start_date, end_date, satlist, localpath, maxsizeondisk, threads)
        tc.mthandler(this_sat, dday, ls, satalt, bcoord, indices, eq_datetimes, [eq_s.get_L_shells(intalt)], L_thres, [intalt], i) # We need to pass mthandler a single L_shells list


    ### plot dT histo ###

    tcp = temporal_correlation_plot(localpath,satlist)
    # dT histo, conf, confpeaks
    for this_sat in satlist:
        tcp.plot_dT(intalt,this_sat)

    ### plot conf-dL (also conf-dL peaks) ###
    
    tcp = temporal_correlation_plot(localpath, satlist)
    for this_sat in satlist:
	tcp.plot_conf_dL(intalt,this_sat)
	temp = tcp.get_confpeaks(intalt, vsmooth=8) #vsmooth is amount to smooth data by. (helps reduces peaks, but moves them.)
	filename = "confpeaks_ns%s.txt" % (this_sat)
        with open(filename,"w") as output:
	    output.write(str(temp))

    ### Var alt ###
	#!!! Run this after dataprep
	#!!! Recommended that you also run this after TC and conf-dL and use the L values written to the file: confpeaks_ns41.txt etc.

    	#tc = temporal_correlation(start_date, end_date, satlist, localpath, maxsizeondisk, threads)
    	#for this_sat in satlist:
        #	tc.mthandler(this_sat, dday, ls, satalt, bcoord, indices, eq_datetimes, L_shells, new_L, alt2test, i) # L_shells needs to be list with alt2test number of L_shell lists. new_L are obtained from conf-dL peaks.
        #	i += 1

    ### plot dT (alt) ###
    
    #tcp = temporal_correlation_plot(self.localpath, self.satlist)
    #for alt in alt2test:
    #    for this_sat in self.satlist:
    #        tcp.plot_dT(alt,this_sat)

    ### plot conf-alt ###

    #tcp = temporal_correlation_plot(self.localpath, self.satlist)
    #for this_sat in self.satlist:
    #    tcp.plot_conf_alt(this_sat)
    

class temporal_correlation():
    def __init__(self, start_date, end_date, satlist, localpath, maxsizeondisk, threads):
        self.start_date = start_date
        self.end_date = end_date
        self.satlist = satlist
        self.localpath = localpath
        self.maxsizeondisk = maxsizeondisk
        self.threads = threads
        
        self.localfolder = 'data'
        self.rawf = 'raw'
        self.prof = 'processed'
        
        #Check if gps sat data exists. Download if missing.
        gps_particle_data.gps_satellite_data_download(self.start_date, self.end_date, self.satlist, self.localpath, self.maxsizeondisk)
    

    def runtc(self, alt2test, L_thres, intalt = 400, new_L = None, karg = 1, vsmooth = 9):
        #check if new_L has a legit value
        if karg == 3 and new_L == None:
            raise Exception("In order to use mode 3 you need to define new_L")
        
        
        i = 0
        #%%
        #TC
        if karg == 0 or karg == 1:
            print 'TC'
            for this_sat in self.satlist:
                dday, ls, satalt, bcoord, indices, eq_datetimes, L_shells = self.dataprep(this_sat,[intalt]) 
                self.mthandler(this_sat, dday, ls, satalt, bcoord, indices, eq_datetimes, L_shells, L_thres, [intalt], i)
                
        #%%
        #confpeak
        if karg == 0 or karg == 1 or karg == 2 or karg == 4 or karg == 5 or karg == 6:
            print 'confpeak'
            tcp = temporal_correlation_plot(self.localpath, self.satlist)
            new_L = tcp.get_confpeaks(intalt,vsmooth)
        
        if karg == 6:
            print new_L
        #%%
        #alt
        #i = 0
        #if karg == 3:
            #new_L = [[0.007]]
        if karg == 0 or karg == 2 or karg == 3:
            'print alt'
            for this_sat in self.satlist:
                dday, ls, satalt, bcoord, indices, eq_datetimes, L_shells = self.dataprep(this_sat, alt2test)
                self.mthandler(this_sat, dday, ls, satalt, bcoord, indices, eq_datetimes, L_shells, new_L, alt2test, i)
                i += 1
                
        #%%
        #plot tc/alt/conf
        if karg == 0 or karg == 1 or karg == 3 or karg == 4 or karg == 5:
            print 'plot tc/alt/conf'
            tcp = temporal_correlation_plot(self.localpath, self.satlist)
            tcp.auto_plot(intalt, karg, vsmooth)
        
        #%%
        #plot conf
        
        ###
    
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
        
        # improved drop data
        ddata = np.array([i for i, j in enumerate(output_data[this_sat]['dropped_data']) if j == 1])
        temp_ch2 = np.asarray(output_data[this_sat]['rate_electron_measured'])[:,2]
        dch2 = np.where(temp_ch2 > 50000)[0]
        dalt = np.array([i for i, j in enumerate(output_data[this_sat]['Rad_Re']) if j <= 3.5 or j >= 4.75])
    
        index2drop = np.unique(np.concatenate((ddata,dch2,dalt)))
        #print index2drop
        
        ch2 = np.delete(temp_ch2,index2drop)
        dday = np.delete(output_data[this_sat]['decimal_day'],index2drop)
        ls = np.delete(output_data[this_sat]['L_shell'],index2drop)
        satalt = np.delete(output_data[this_sat]['Rad_Re'],index2drop)
        bcoord = np.delete(output_data[this_sat]['b_coord_radius'],index2drop)
        
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
        
    def mthandler(self, this_sat, dday, ls, satalt, bcoord, indices, eq_datetimes, L_shells, L_thres, alt2test, i): 
        if len(alt2test) == 1:
            pool = Pool(self.threads)
            #temp = zip(repeat(self.localpath), repeat(this_sat), repeat(dday), repeat(ls), repeat(satalt),repeat(bcoord), repeat(indices), repeat(eq_datetimes), repeat(L_thres), L_shells, alt2test)
            pool.map(self.tc_fw, repeat(self.localpath), repeat(this_sat), repeat(dday), repeat(ls), repeat(satalt),repeat(bcoord), repeat(indices), repeat(eq_datetimes), L_thres, repeat(L_shells[0]), repeat(alt2test[0]))
            #pool.close()
            #pool.join()
            pool.clear()
        else:
            pool = Pool(self.threads)
            #temp = zip(repeat(self.localpath), repeat(this_sat), repeat(dday), repeat(ls), repeat(satalt),repeat(bcoord), repeat(indices), repeat(eq_datetimes), repeat(L_thres), L_shells, alt2test)
            for a in L_thres[i]:
                pool.map(self.tc_fw, repeat(self.localpath), repeat(this_sat), repeat(dday), repeat(ls), repeat(satalt),repeat(bcoord), repeat(indices), repeat(eq_datetimes), repeat(a), L_shells, alt2test)
            #pool.close()
            #pool.join()
            pool.clear()
                
    def tc_fw(self, localpath, this_sat, dday, ls, satalt, bcoord, indices, eq_datetimes, lthres, L_shells, alt):
        ils = len(indices)*len(L_shells)
        print 'Working on %s with dL=%s at %s km | Total tests: %s' % (this_sat,lthres,alt,ils)
        start_time = time.clock()
        # setup the current file we are using
        # removes deciaml point for lthres
        # file...
        #temp1 = str(lthres).replace('.','d')
	slthres = str(1000.0*lthres).zfill(5)
        #len(temp1) == 5:
        #    slthres = temp1 + '0' #0d029 -> 0d0290
        #elif len(temp1) == 4:
        #    slthres = temp1 + '00' #0d02 -> 0d0200
        #slthres = str(lthres).replace('.','d')
        temp2 = ''.join(e for e in str(alt) if e.isalnum())
        if len(temp2) == 3:
            salt = '0' + temp2
        else:
            salt = temp2
        current_file = 'tc_ns%s_%s_%s.ascii' % (this_sat,salt,slthres)

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
                if abs(del_L) < lthres and  abs(del_T) < 2: # lthres use to be 1.
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
            dst = os.path.join(localpath , self.localfolder , self.prof , 'ns' + str(this_sat) )
            shutil.move(os.path.join(localpath , current_file), os.path.join(dst , current_file) )
        
        timetaken = time.clock() - start_time   
        jobspersec = ils / timetaken           
        print 'Finished working on %s-%s. Time taken: %s | %s Jobs per second' % (lthres,alt,timetaken, jobspersec)
                                    
                
class temporal_correlation_plot():
    def __init__(self, localpath, satlist):
        self.localpath = localpath
        self.satlist = satlist
        self.localfolder = 'data'
        self.rawf = 'raw'
        self.prof = 'processed'
    
    
    def get_confpeaks(self, alt, vsmooth):
        new_L = []
        for this_sat in self.satlist:
            #print 'get_confpeaks'
            #localfolder = 'data'
            #rawf = 'raw'
            #prof = 'processed'
            
            path = os.path.join(self.localpath , self.localfolder , self.prof , 'ns' + str(this_sat) )
            filelist,L_thres,altvals = self.get_FL_L_A(path)
            
            conflvl = []
            tempL = []
            
            intindex = [i for i, j in enumerate(altvals) if j == alt]
        
            for i in intindex:
                conflvl.append(self.get_conflvl(path,filelist[i],this_sat,L_thres[i]))
            cb = np.array(self.smooth(conflvl,vsmooth))
            #cb = np.array(conflvl)
            indices = peakutils.indexes(cb, thres=0.02/max(cb), min_dist=0.1)
            for lthres in indices:
                    tempL.append(L_thres[intindex[lthres]])
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
                
                L_thres.append(float(str(((item.split("_")[3]).split(".")[0])).replace('d','.')))
                altvals.append(int(item.split("_")[2]))
        
        #print altvals
        return filelist,L_thres,altvals
    
    def smooth(self,y, box_pts):
        box = np.ones(box_pts)/box_pts
        y_smooth = np.convolve(y, box, mode='same')
        return y_smooth
        
    def get_conflvl(self, path, current_file, this_sat, lthres):
        # setup the current file we are using
        
        print '=== %s' % (current_file)
        
        curdata = np.loadtxt(path + current_file)
        #print curdata
        #convert the data into histogram bins.
        #if curdata hold just 1 values, this throws error--- IndexError: too many indices for array
        if curdata.ndim == 2:
            bins = np.arange(min(curdata[:,0]), max(curdata[:,0])+1)
        else:
            print 'WARN %s only contains a single line. Increase dataset size.' % (current_file)
            return 0
        hist, bin_edges = np.histogram(curdata[:,0],bins)
        
        # n{sig} = (Nmax - Nbg/{sig})     taken from S. Yu Aleksandrin et al.: High-energy charged particle bursts
        Nmax = max(hist)
        Nbg = np.median(hist)
        sig = np.std(hist) 
        nsig = (Nmax - Nbg)/sig
        return nsig
                
    
    def plot_dT(self,alt,this_sat):
        path = os.path.join(self.localpath , self.localfolder , self.prof , 'ns' +str(this_sat) )
        filelist,L_thres,alt = self.get_FL_L_A(path)
        for i in range(len(filelist)):
            self.plotdata(path,filelist[i],this_sat,L_thres[i])

    def plot_conf_dL(self,alt,this_sat):
        intindex = [i for i, j in enumerate(alt) if j == intalt]
        conflvl = []
        x = []
        for i in intindex:
            #self.plotdata(path,filelist[i],this_sat,L_thres[i])
            conflvl.append(self.get_conflvl(path,filelist[i],this_sat,L_thres[i]))
            x.append(L_thres[i])
        #print conflvl
        fig = plt.figure(figsize=(13, 13)) 
        plt.plot(x, conflvl)
        plt.plot(x,self.smooth(conflvl,9))  
        plt.xticks(np.arange(0.0, max(L_thres)+0.01, 0.01))
        plt.grid(True)
        plttitle = 'Confidence level with differing {delta}L values for Satellite %s at %skm' % (this_sat,intalt)
        plt.title(plttitle)
        plt.xlabel('{delta}L')
        plt.ylabel('Confidence level')
        temp2 = ''.join(e for e in str(intalt) if e.isalnum())
        if len(temp2) == 3:
            salt = '0' + temp2
        else:
            salt = temp2
        plt.savefig(os.path.join(path , 'L'+salt+'_confplot.png'))
        fig.clear() #cleanup
        plt.close(fig) #cleanup

    def plot_conf_alt(self,this_sat):
        # Plot conf - alt
        ualt = list(set(alt))
        if len(ualt) >= 1:
            print 'CONF-ALT'
            # unique alts
            index0 = [i for i, j in enumerate(alt) if j == ualt[1]] # gets us the indexes of tested dL's
            Lstested = [L_thres[i] for i in index0] # get us the dL's tested
                
            for j in index0:
                print filelist[j]
                
            confLstested = []
            Lindex = 0
            for L in Lstested:
                temp = []
                x=[]
                for i in range(len(filelist)):
                    if L_thres[i] == L:
                        temp.append(self.get_conflvl(path,filelist[i],this_sat,L_thres[i]))
                        x.append(alt[i])
                #print temp
                confLstested.append(temp)

                #print conflvl
                fig = plt.figure(figsize=(13, 13)) 
                plt.scatter(x, confLstested[Lindex])
                #plt.plot(x,self.smooth(confLstested[Lindex],vsmooth))  
                #plt.xticks(np.arange(0.0, max(L_thres)+0.01, 0.01))
                plt.grid(True)
                plttitle = 'Confidence level with a {delta}L of %s for Satellite %s with different coupling altitudes' % (L,this_sat)
                plt.title(plttitle)
                plt.xlabel('Coupling altitude')
                plt.ylabel('Confidence level')
                #temp1 = str(L).replace('.','d')
		slthres = str(1000.0*L).zfill(5)
                #if len(temp1) == 5:
                #    slthres = temp1 + '0' #0d029 -> 0d0290
                #elif len(temp1) == 4:
                #    slthres = temp1 + '00' #0d02 -> 0d0200
                plt.savefig(os.path.join(path , 'A'+slthres+'_confplot.png'))
                fig.clear() #cleanup
                plt.close(fig) #cleanup
                #plt.show()
                Lindex += 1


    def auto_plot(self,intalt,karg,vsmooth):
        for this_sat in self.satlist:
            #localfolder = 'data\\'
            #rawf = 'raw\\'
            #prof = 'processed\\'
            path = os.path.join(self.localpath , self.localfolder , self.prof , 'ns' +str(this_sat) )
            

            
            filelist,L_thres,alt = self.get_FL_L_A(path)
            
            #%%
            # Plots histograms
            if karg == 4:
                for i in range(len(filelist)):
                    self.plotdata(path,filelist[i],this_sat,L_thres[i])
            
            #%%
            # This plots conf - dL
            
            if karg == 0 or karg == 1 or karg == 4 or karg == 5:
                intindex = [i for i, j in enumerate(alt) if j == intalt]
                conflvl = []
                x = []
                for i in intindex:
                    #self.plotdata(path,filelist[i],this_sat,L_thres[i])
                    conflvl.append(self.get_conflvl(path,filelist[i],this_sat,L_thres[i]))
                    x.append(L_thres[i])
                #print conflvl
                fig = plt.figure(figsize=(13, 13)) 
                plt.plot(x, conflvl)
                plt.plot(x,self.smooth(conflvl,9))  
                plt.xticks(np.arange(0.0, max(L_thres)+0.01, 0.01))
                plt.grid(True)
                plttitle = 'Confidence level with differing {delta}L values for Satellite %s at %skm' % (this_sat,intalt)
                plt.title(plttitle)
                plt.xlabel('{delta}L')
                plt.ylabel('Confidence level')
                temp2 = ''.join(e for e in str(intalt) if e.isalnum())
                if len(temp2) == 3:
                    salt = '0' + temp2
                else:
                    salt = temp2
                plt.savefig(os.path.join(path , 'L'+salt+'_confplot.png'))
                fig.clear() #cleanup
                plt.close(fig) #cleanup
                #plt.show()
                
                
            
            #%%
            # Plot conf - alt
            ualt = list(set(alt))
            if (karg == 0 or karg == 2 or karg == 3 or karg == 4 or karg == 5) and len(ualt) > 1:
                print 'CONF-ALT'
                 # unique alts
                index0 = [i for i, j in enumerate(alt) if j == ualt[1]] # gets us the indexes of tested dL's
                Lstested = [L_thres[i] for i in index0] # get us the dL's tested
                
                for j in index0:
                    print filelist[j]
                
                confLstested = []
                Lindex = 0
                for L in Lstested:
                    temp = []
                    x=[]
                    for i in range(len(filelist)):
                        if L_thres[i] == L:
                            temp.append(self.get_conflvl(path,filelist[i],this_sat,L_thres[i]))
                            x.append(alt[i])
                    #print temp
                    confLstested.append(temp)

                    #print conflvl
                    fig = plt.figure(figsize=(13, 13)) 
                    plt.scatter(x, confLstested[Lindex])
                    #plt.plot(x,self.smooth(confLstested[Lindex],vsmooth))  
                    #plt.xticks(np.arange(0.0, max(L_thres)+0.01, 0.01))
                    plt.grid(True)
                    plttitle = 'Confidence level with a {delta}L of %s for Satellite %s with different coupling altitudes' % (L,this_sat)
                    plt.title(plttitle)
                    plt.xlabel('Coupling altitude')
                    plt.ylabel('Confidence level')
                    temp1 = str(L).replace('.','d')
                    if len(temp1) == 5:
                        slthres = temp1 + '0' #0d029 -> 0d0290
                    elif len(temp1) == 4:
                        slthres = temp1 + '00' #0d02 -> 0d0200
                    plt.savefig(os.path.join(path , 'A'+slthres+'_confplot.png'))
                    fig.clear() #cleanup
                    plt.close(fig) #cleanup
                    #plt.show()
                    Lindex += 1
            else:
                print 'You need to run alt testing.'
                
    
    
    def plotdata(self, path, current_file, this_sat, lthres):
        #plot the data so far
        fig = plt.figure(figsize=(13, 13))
        gs1 = gridspec.GridSpec(3, 1)
        gs1.update(wspace=0.0, hspace=0.05)
        
        #slthres = str(lthres).replace('.','d')
        temp1 = str(L).replace('.','d')
        if len(temp1) == 5:
            slthres = temp1 + '0' #0d029 -> 0d0290
        elif len(temp1) == 4:
            slthres = temp1 + '00' #0d02 -> 0d0200
        his = np.loadtxt(os.path.join(path , current_file))
        # his[:,0] contains dt
        # his[:,1] contains satalt
        # his[:,2] contains bcoord
        
        
        titletext = 'Temporal correlation of detected particle\nbursts (from ns%s) to earthquakes\nwith dL of %s' % (this_sat,lthres)
        plt.suptitle(titletext, fontsize=20)
        fig.canvas.draw()
        
        ax1 = plt.subplot(gs1[0])
        #
        xcoords = np.arange(min(his[:,0]), max(his[:,0])+1)
        for xc in xcoords:
            plt.axvline(x=xc, color='0.75')
        plt.axvline(x=0, color='r')
        #
        plt.hist(his[:,0], bins = np.arange(min(his[:,0]), max(his[:,0])+1))
        #plt.xlabel(u'dT / hours', fontsize  = 30)
        plt.ylabel('Number of events', fontsize = 16)
        plt.setp(ax1.get_xticklabels(), visible=False)
        
        ax2 = plt.subplot(gs1[1],sharex=ax1)
        #
        xcoords = np.arange(min(his[:,0]), max(his[:,0])+1)
        for xc in xcoords:
            plt.axvline(x=xc, color='0.75')
        plt.axvline(x=0, color='r')
        #
        plt.scatter(his[:,0], his[:,1])
        plt.ylabel('Satellite Altitude\n(In Earth Radii)', fontsize = 16)
        plt.setp(ax2.get_xticklabels(), visible=False)
        
        ax3 = plt.subplot(gs1[2],sharex=ax1)
        #
        xcoords = np.arange(min(his[:,0]), max(his[:,0])+1)
        for xc in xcoords:
            plt.axvline(x=xc, color='0.75')
        plt.axvline(x=0, color='r')
        #
        plt.scatter(his[:,0], his[:,2])
        plt.ylabel('Satellite b_coord_radius', fontsize = 16)
        plt.xlabel(u'dT / hours', fontsize  = 16)
        
        plt.savefig(os.path.join(path , slthres+'_histo.png'))
        #plt.show()
        fig.clear() #cleanup
        plt.close(fig) #cleanup
    
    
    
  
if __name__ == '__main__':
    freeze_support()
    main()
    
    
#


# -*- coding: utf-8 -*-
"""
Created on Wed Feb 21 17:14:14 2018

@author: jackj

Title: dataplot2 - Refined dataplot.py
"""

import gps_particle_data
import numpy as np
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mpld
import matplotlib.gridspec as gridspec
from matplotlib.ticker import AutoMinorLocator

#signal comparison
from scipy import signal
from scipy.stats.stats import pearsonr
import scipy.fftpack
from scipy import interpolate
from scipy.optimize import curve_fit
import scipy

from lmfit import  Model

from inspect import getsourcefile
from os.path import abspath
import sys

#in order to address memory issues...
import gc

#2.777000000000029445e-03
#dt = 2.77700000000000000e-03 # fixing dt
dt = 1.38500000000000000e-03 # fixing dt



def load_data(this_sat,cdstart,cdend,localpath):
    # Load data.
    ms = gps_particle_data.meta_search(this_sat,localpath) # Do not pass meta_search satlist. Single sat ~12GB of RAM.
    ms.load_local_data(cdstart,cdend)
    ms.clean_up() #deletes json files.
    print ''
    
    output_data = ms.get_all_data_by_satellite()
    del ms # save RAM once we are finished.
    gc.collect()
    
#    print output_data
#    print len(output_data[this_sat])
#    print output_data[this_sat] is not None
    
    
    if len(output_data[this_sat]) != 0: # Seems to throw NoneType for 2005-08-14 ->20
        ddata = output_data[this_sat]['dropped_data']
        index2drop = [i for i, j in enumerate(ddata) if j == 1]
        
        if len(ddata) * 0.5 <= len(index2drop): # ie we must have at least 50% usuable data.
            print 'High drop rate. Skipping.'
            return [0], [0], [0], [0], [0], [0], [0], [0], [0]
        
        del ddata # save RAM once we are finished.
        
        dday =  output_data[this_sat]['decimal_day']
        dday[:] = [x - 1 for x in dday] # apply the -1 offset to dday as well..
        dday_dropped = np.delete(dday,index2drop)

        #%%
        """ Seems there's an issue with the collection interval being not uniform, despite the
            240s provided. Therefore dday needs to be interp'ed to fix this. We double the number of values
            in dday in order to maintain fine structure.
        """
        dday = np.array(dday)
        dday_old = dday # Save dday for comparision.
        dday = dday.flatten()
        ddayx = np.array(range(len(dday)))
        ddayx_new = np.linspace(0,len(dday),len(dday)*2)
        dday = np.interp(ddayx_new, ddayx, dday)      
        
        #%%

        year = output_data[this_sat]['year']
        year = np.delete(year,index2drop)
        year = np.interp(dday,dday_dropped,year) # Needs to be interp'ed.
        
        temp_ecr = np.asarray(output_data[this_sat]['rate_electron_measured']) 
        temp2_ecr = np.delete(temp_ecr,index2drop,0)
        temp3_ecr = np.array([np.interp(dday, dday_dropped, temp2_ecr[:,i]) for i in range(int(temp2_ecr.shape[1]))])
        ecr = temp3_ecr.T
        # save RAM once we are finished.
        del temp_ecr 
        del temp2_ecr
        
        temp_pcr = np.asarray(output_data[this_sat]['rate_proton_measured'])
        temp2_pcr = np.delete(temp_pcr,index2drop,0)
        temp3_pcr = np.array([np.interp(dday, dday_dropped, temp2_pcr[:,i]) for i in range(int(temp2_pcr.shape[1]))])
        pcr = temp3_pcr.T
        del temp_pcr # save RAM once we are finished.
        del temp2_pcr # save RAM once we are finished.
        
        temp_alt = output_data[this_sat]['Rad_Re']
        temp2_alt = np.delete(temp_alt,index2drop)
        satalt = np.interp(dday, dday_dropped, temp2_alt)
        del temp_alt # save RAM once we are finished.
        del temp2_alt # save RAM once we are finished.
        
        temp_bheight = output_data[this_sat]['b_coord_height']
        temp2_bheight = np.delete(temp_bheight,index2drop)
        bheight = np.interp(dday, dday_dropped, temp2_bheight)
        del temp_bheight # save RAM once we are finished.
        del temp2_bheight # save RAM once we are finished.
        
        temp_lon = output_data[this_sat]['Geographic_Longitude']
        temp2_lon = np.delete(temp_lon,index2drop)
        sat_lon = np.interp(dday, dday_dropped, temp2_lon)
        del temp_lon
        del temp2_lon
        
        del output_data # save RAM once we are finished.
        del index2drop # save RAM once we are finished.
        del dday_dropped # save RAM once we are finished.
        gc.collect()
        
        ourdates = []
        for i in range(len(dday)):
            ourdates.append(datetime(int(year[i]),1,1,0,0,0) + timedelta(days=dday[i]))
        
        # convert between datetime objects and matplotlib format
        ourmpldates = mpld.date2num(ourdates)
        #del ourdates # save RAM once we are finished.
        
        #Get angles from height and alt.
        angle = np.degrees(np.arcsin((bheight/satalt)))

        return ecr, pcr, dday, year, satalt, bheight, ourmpldates, angle, sat_lon
    else:
        return [0], [0], [0], [0], [0], [0], [0], [0], [0]
    
    
    # Fall back failure.
    return [0], [0], [0], [0], [0], [0], [0], [0], [0]




#%%
def turning_points(array):
    ''' https://stackoverflow.com/questions/19936033/finding-turning-points-of-an-array-in-python
    turning_points(array) -> min_indices, max_indices
    Finds the turning points within an 1D array and returns the indices of the minimum and 
    maximum turning points in two separate lists.
    '''
    idx_max, idx_min = [], []
    if (len(array) < 3): 
        return idx_min, idx_max

    NEUTRAL, RISING, FALLING = range(3)
    def get_state(a, b):
        if a < b: return RISING
        if a > b: return FALLING
        return NEUTRAL

    ps = get_state(array[0], array[1])
    begin = 1
    for i in range(2, len(array)):
        s = get_state(array[i - 1], array[i])
        if s != NEUTRAL:
            if ps != NEUTRAL and ps != s:
                if s == FALLING: 
                    idx_max.append((begin + i - 1) // 2)
                else:
                    idx_min.append((begin + i - 1) // 2)
            begin = i
            ps = s
    return idx_min, idx_max
        


def plot(this_sat, ecr, pcr, dday, year, satalt, bheight, ourmpldates, angle):
    #%%
        #!!!
        fig = plt.figure(figsize=(40, 30), dpi=160)
        #fig = plt.figure(figsize=(4, 3), dpi=80)
        gs1 = gridspec.GridSpec(11, 6) #7,6
        gs1.update(wspace=0.15, hspace=0.15)
        plt.tight_layout()
        
        titletext = 'Raw data plots for svn%s' % (this_sat)
        plt.suptitle(titletext, fontsize=20)
        fig.canvas.draw()
        
        #%%
        ax1 = plt.subplot(gs1[0,:])
        #!!! Need horizontal line for global CH2 stddev * 4
        
        for i in range(int(ecr.shape[1])):
            curlabel = 'Electron Channel %s' % (i)
            plt.plot_date(ourmpldates,ecr[:,i], label=curlabel)
        
        #plt.plot_date(ourmpldates,ch2)
        plt.ylabel('Electron rate', fontsize = 16)
        plt.setp(ax1.get_xticklabels(), visible=False)
        # Setup grids
        plt.minorticks_on()
        minorLocator = AutoMinorLocator(4)
        ax1.xaxis.set_minor_locator(minorLocator)
        plt.grid(True, which='both')
        ax1.yaxis.grid(False, which='minor')
        # Shrink current axis by 20%
        box = ax1.get_position()
        ax1.set_position([box.x0, box.y0, box.width * 0.9, box.height])
        # Put a legend to the right of the current axis
        ax1.legend(loc='center left', bbox_to_anchor=(1, 0.5), shadow=True)
        
        #%%
        ax2 = plt.subplot(gs1[1,:],sharex=ax1)
        for i in range(int(pcr.shape[1])):
            curlabel = 'Proton Channel %s' % (i)
            plt.plot_date(ourmpldates,pcr[:,i], label=curlabel)
        
        plt.ylabel('Proton rate', fontsize = 16)
        plt.setp(ax2.get_xticklabels(), visible=False)
        # Setup grids
        plt.minorticks_on()
        minorLocator = AutoMinorLocator(4)
        ax2.xaxis.set_minor_locator(minorLocator)
        plt.grid(True, which='both')
        ax2.yaxis.grid(False, which='minor') 
    
        # Shrink current axis by 20%
        box = ax2.get_position()
        ax2.set_position([box.x0, box.y0, box.width * 0.9, box.height])
        # Put a legend to the right of the current axis
        ax2.legend(loc='center left', bbox_to_anchor=(1, 0.5), shadow=True)
        
        # change axis location of ax2
        pos1 = ax1.get_position()
        pos2 = ax2.get_position()
        points1 = pos1.get_points()
        points2 = pos2.get_points()
        points2[1][1]=points1[0][1]
        pos2.set_points(points2)
        ax2.set_position(pos2)
        
        
        #%%
        ax3 = plt.subplot(gs1[2,:],sharex=ax1)
        plt.plot_date(ourmpldates,satalt)
        plt.ylabel('Altitude in Earth Radii', fontsize = 16)
        plt.setp(ax2.get_xticklabels(), visible=False)
        #plt.xlabel('Date', fontsize  = 16)
        # Setup grids
        plt.minorticks_on()
        minorLocator = AutoMinorLocator(4)
        ax3.xaxis.set_minor_locator(minorLocator)
        plt.grid(True, which='both')
        ax3.yaxis.grid(False, which='minor') 
        
        # Shrink current axis by 20%
        box = ax3.get_position()
        ax3.set_position([box.x0, box.y0, box.width * 0.9, box.height])
        # Put a legend to the right of the current axis
        ax3.legend(loc='center left', bbox_to_anchor=(1, 0.5), shadow=True)
         
        # change axis location of ax3
        pos2 = ax2.get_position()
        pos3 = ax3.get_position()
        points2 = pos2.get_points()
        points3 = pos3.get_points()
        points3[1][1]=points2[0][1]
        pos3.set_points(points3)
        ax3.set_position(pos3)
        
        #!!!
        #ax1.set_xlim(mpld.date2num([cdstart,cdend]))
        
        #%%
        
        ax9 = plt.subplot(gs1[3,:])
        plt.plot_date(ourmpldates,angle)
        plt.ylabel('Satellite angle from horizon', fontsize = 16)
        plt.xlabel('Date', fontsize  = 16)
        # Setup grids
        plt.minorticks_on()
        minorLocator = AutoMinorLocator(4)
        ax9.xaxis.set_minor_locator(minorLocator)
        plt.grid(True, which='both')
        ax9.yaxis.grid(False, which='minor') 
        
        # Shrink current axis by 20%
        box = ax9.get_position()
        ax9.set_position([box.x0, box.y0, box.width * 0.9, box.height])
        # Put a legend to the right of the current axis
        ax9.legend(loc='center left', bbox_to_anchor=(1, 0.5), shadow=True)
         
        # change axis location of ax9
        pos3 = ax3.get_position()
        pos9 = ax9.get_position()
        points3 = pos3.get_points()
        points9 = pos9.get_points()
        points9[1][1]=points3[0][1]
        pos9.set_points(points9)
        ax9.set_position(pos9)
        
        #%%
        ax4 = plt.subplot(gs1[4,:-3])
        for i in range(int(ecr.shape[1])):
            curlabel = 'Electron Channel %s' % (i)
            plt.scatter(satalt,ecr[:,i], label=curlabel)
        plt.ylabel('Electron rates', fontsize  = 16)
        #plt.xlabel('Altitude in Earth Radii', fontsize = 16)
        plt.setp(ax4.get_xticklabels(), visible=False)
        
        # Setup grids
        plt.minorticks_on()
        minorLocator = AutoMinorLocator(5)
        ax4.xaxis.set_minor_locator(minorLocator)
        plt.grid(True, which='both')
        ax4.yaxis.grid(False, which='minor') 
        
        # Shrink current axis by 20%
        box = ax4.get_position()
        ax4.set_position([box.x0, box.y0, box.width * 0.8, box.height])
        # Put a legend to the right of the current axis
        ax4.legend(loc='center left', bbox_to_anchor=(1, 0.5), shadow=True)
        
    
        
        #%%
        ax5 = plt.subplot(gs1[5,:-3],sharex=ax4)
        for i in range(int(pcr.shape[1])):
            curlabel = 'Proton Channel %s' % (i)
            plt.scatter(satalt,pcr[:,i], label=curlabel)
        plt.ylabel('Proton rates', fontsize  = 16)
        plt.xlabel('Altitude in Earth Radii', fontsize = 16)
        
        # Setup grids
        plt.minorticks_on()
        minorLocator = AutoMinorLocator(5)
        ax5.xaxis.set_minor_locator(minorLocator)
        plt.grid(True, which='both')
        ax5.yaxis.grid(False, which='minor') 
        
        # Shrink current axis by 20%
        box = ax5.get_position()
        ax5.set_position([box.x0, box.y0, box.width * 0.8, box.height])
        # Put a legend to the right of the current axis
        ax5.legend(loc='center left', bbox_to_anchor=(1, 0.5), shadow=True)
        
        # change axis location of ax5
        pos4 = ax4.get_position()
        pos5 = ax5.get_position()
        points4 = pos4.get_points()
        points5 = pos5.get_points()
        points5[1][1]=points4[0][1]
        pos5.set_points(points5)
        ax5.set_position(pos5)
        
        #%%
        
        ax10 = plt.subplot(gs1[6,:-3])
        
        plt.scatter(satalt,bheight)   
        plt.ylabel('Height above plane in Re', fontsize = 16)
        plt.xlabel('Altitude in Earth Radii', fontsize  = 16)
        # Setup grids
        plt.minorticks_on()
        minorLocator = AutoMinorLocator(5)
        ax10.xaxis.set_minor_locator(minorLocator)
        plt.grid(True, which='both')
        ax10.yaxis.grid(False, which='minor') 
        
        # Shrink current axis by 20%
        box = ax10.get_position()
        ax10.set_position([box.x0, box.y0, box.width * 0.8, box.height])
        # Put a legend to the right of the current axis
        ax10.legend(loc='center left', bbox_to_anchor=(1, 0.5), shadow=True)
        
        # change axis location of ax10
        pos5 = ax5.get_position()
        pos10 = ax10.get_position()
        points5 = pos5.get_points()
        points10 = pos10.get_points()
        points10[1][1]=points5[0][1]
        pos10.set_points(points10)
        ax10.set_position(pos10)
        
        #%%
        ax6 = plt.subplot(gs1[4,3:])
        
        for i in range(int(ecr.shape[1])):
            curlabel = 'Electron Channel %s' % (i)
            plt.scatter(angle,ecr[:,i], label=curlabel)
            
        plt.ylabel('Electron rate', fontsize = 16)
        plt.xlabel('Angle from horizon', fontsize  = 16)
        # Setup grids
        plt.minorticks_on()
        minorLocator = AutoMinorLocator(4)
        ax6.xaxis.set_minor_locator(minorLocator)
        plt.grid(True, which='both')
        ax6.yaxis.grid(False, which='minor') 
        
        # Shrink current axis by 20%
        box = ax6.get_position()
        ax6.set_position([box.x0, box.y0, box.width * 0.8, box.height])
        # Put a legend to the right of the current axis
        ax6.legend(loc='center left', bbox_to_anchor=(1, 0.5), shadow=True)
        
        #%%
        
        ax7 = plt.subplot(gs1[5,3:])
        
        for i in range(int(pcr.shape[1])):
            curlabel = 'Proton Channel %s' % (i)
            plt.scatter(angle,pcr[:,i], label=curlabel)
            
        plt.ylabel('Proton rate', fontsize = 16)
        plt.xlabel('Angle from horizon', fontsize  = 16)
        # Setup grids
        plt.minorticks_on()
        minorLocator = AutoMinorLocator(4)
        ax7.xaxis.set_minor_locator(minorLocator)
        plt.grid(True, which='both')
        ax7.yaxis.grid(False, which='minor') 
        
        # Shrink current axis by 20%
        box = ax7.get_position()
        ax7.set_position([box.x0, box.y0, box.width * 0.8, box.height])
        # Put a legend to the right of the current axis
        ax7.legend(loc='center left', bbox_to_anchor=(1, 0.5), shadow=True)
        
        # change axis location of ax5
        pos6 = ax6.get_position()
        pos7 = ax7.get_position()
        points6 = pos6.get_points()
        points7 = pos7.get_points()
        points7[1][1]=points6[0][1]
        pos7.set_points(points7)
        ax7.set_position(pos7)
        
        #%%
        
        ax8 = plt.subplot(gs1[6,3:])
        
        plt.scatter(angle,satalt)   
        plt.ylabel('Altitude in Re', fontsize = 16)
        plt.xlabel('Angle from horizon', fontsize  = 16)
        # Setup grids
        plt.minorticks_on()
        minorLocator = AutoMinorLocator(4)
        ax8.xaxis.set_minor_locator(minorLocator)
        plt.grid(True, which='both')
        ax8.yaxis.grid(False, which='minor') 
        
        # Shrink current axis by 20%
        box = ax8.get_position()
        ax8.set_position([box.x0, box.y0, box.width * 0.8, box.height])
        # Put a legend to the right of the current axis
        ax8.legend(loc='center left', bbox_to_anchor=(1, 0.5), shadow=True)
        
        # change axis location of ax5
        pos7 = ax7.get_position()
        pos8 = ax8.get_position()
        points7 = pos7.get_points()
        points8 = pos8.get_points()
        points8[1][1]=points7[0][1]
        pos8.set_points(points8)
        ax8.set_position(pos8)
        
        #%%
        """ grad plot
        """
        
        ax30 = plt.subplot(gs1[7,:]) #not sharable with ax1 etc. as not date info
        plt.plot(ecr[:,0]/np.gradient(satalt[:,0]))
        #plt.ylabel('Amplitude?', fontsize = 16)
        #plt.xlabel('Frequency', fontsize  = 16)
        
        plt.minorticks_on()
        minorLocator = AutoMinorLocator(4)
        ax30.xaxis.set_minor_locator(minorLocator)
        plt.grid(True, which='both')
        #ax30.yaxis.grid(False, which='minor')
        
        # Shrink current axis by 20%
        box = ax30.get_position()
        ax30.set_position([box.x0, box.y0, box.width * 0.9, box.height])
        # Put a legend to the right of the current axis
        ax30.legend(loc='center left', bbox_to_anchor=(1, 0.5), shadow=True)
        
        #%%
        #!!!
        """ Plots of Fourier Transforms
            based on:
                https://stackoverflow.com/questions/9456037/scipy-numpy-fft-frequency-analysis
        """
        N = len(ecr[:,0])
        #T = 1.0 / (4.0 * 60)  # 4 minutes in seconds
        T = 1.0 / (4.0 / 60) # 4 minutes in hours
        #T = 4 # minutes
        #T = 1.0 * 4/60 # 4 minutes in terms of hours
        
        #a = scipy.fftpack.fft(ecr[:,0])
        #b = scipy.fftpack.fft(satalt)
        #c = scipy.fftpack.fft(angle)
        
        mag_a = np.fft.rfft(ecr[:,0]/ecr[:,0].max()) #normalise values
        freq_a = np.fft.rfftfreq(N,T) # length,time diff
        
        mag_b = np.fft.rfft(satalt[:,0]/satalt[:,0].max()) #normalise values
        freq_b = np.fft.rfftfreq(N,T) # length,time diff
        
        mag_c = np.fft.rfft(angle[:,0]/angle[:,0].max()) #normalise values
        freq_c = np.fft.rfftfreq(N,T) # length,time diff
        
        #%%
        
        ax20 = plt.subplot(gs1[8,:])   # 3:   :-3
        plt.plot(freq_a, mag_a)
        plt.ylabel('Magnitude', fontsize = 16)
        plt.xlabel('Frequency (Hz)', fontsize  = 16)
        
        plt.grid(True, which='both')
        
        # Shrink current axis by 20%
        box = ax20.get_position()
        ax20.set_position([box.x0, box.y0, box.width * 0.9, box.height])
        # Put a legend to the right of the current axis
        ax20.legend(loc='center left', bbox_to_anchor=(1, 0.5), shadow=True)
        
        #%%
        ax21 = plt.subplot(gs1[9,:])
        plt.plot(freq_b, mag_b)
        plt.ylabel('Magnitude', fontsize = 16)
        plt.xlabel('Frequency (Hz)', fontsize  = 16)
        
        plt.grid(True, which='both')
        
        # Shrink current axis by 20%
        box = ax21.get_position()
        ax21.set_position([box.x0, box.y0, box.width * 0.9, box.height])
        # Put a legend to the right of the current axis
        ax21.legend(loc='center left', bbox_to_anchor=(1, 0.5), shadow=True)
        
        #%%
        ax22 = plt.subplot(gs1[10,:])
        plt.plot(freq_c, mag_c)
        plt.ylabel('Magnitude', fontsize = 16)
        plt.xlabel('Frequency (Hz)', fontsize  = 16)
        
        plt.grid(True, which='both')
        
        # Shrink current axis by 20%
        box = ax22.get_position()
        ax22.set_position([box.x0, box.y0, box.width * 0.9, box.height])
        # Put a legend to the right of the current axis
        ax22.legend(loc='center left', bbox_to_anchor=(1, 0.5), shadow=True)
        

        
        #%%
        print '###PRE-SAVE###'
        stemp = localpath + 'svn' + str(this_sat) + 'rawplot_' + str(cdstart.year) + '_' + str(cdstart.month) + '_' + str(cdstart.day) + '___' + str(cdend.year) + '_' + str(cdend.month) + '_' + str(cdend.day) + '.png'
        #plt.show()
        plt.savefig(stemp,bbox_inches="tight")
        fig.clear() #cleanup
        plt.clf() #cleanup
        plt.cla() #cleanup
        plt.close(fig) #cleanup
    
#%%
  
def smooth(y, box_pts):
    box = np.ones(box_pts)/box_pts
    y_smooth = np.convolve(y, box, mode='same')
    return y_smooth

      
def fit(this_sat, ecr, pcr, dday, year, satalt, bheight, ourmpldates, angle, sat_lon):
    """ Gaussian fit for ecr 0 
    Based upon http://cars9.uchicago.edu/software/python/lmfit/model.html"""
    # get index of minimums
    #ecr0_tpmin, ecr0_tpmax = turning_points(ecr[:,0])
    lon_tpmin, lon_tpmax = turning_points(sat_lon) # True single orbit
    
    # values between first and second sat_lon min
    #!!!
    tempv = [] # angle
    tempw = [] # bheight
    tempx = [] # ecr
    tempy = [] # sat_lon
    tempz = [] # sat alt
    tempt = [] # sat dday
    tempyy = [] # year
    
    """ Get a single orbit """
    
    if len(lon_tpmin) < 2: # making sure lon_tpmin has values, else skip data point
        print 'not getting enough min lon..? Likily due to loading two data files.'
        return
    
    for i in range(lon_tpmin[0],lon_tpmin[1]):
        tempv.append(angle[i])
        tempw.append(bheight[i]) # Given angle is derived from bheight and sat alt.
        tempx.append(ecr[:,0][i])
        tempy.append(sat_lon[i])
        tempz.append(satalt[i])
        tempt.append(dday[i])
        tempyy.append(year[i])
    
    tempe = []
    tempa = []
    tempb = []
    tempc = []
    tempd = []
    tempt2 = []
    tempyy2 = []
    
    tempx2 = np.copy(tempx)
    tempx2[tempx2 < 50] = 0 # remove noise from tempx
                            # It seems there are peaks at ~20. 
        
    tempx2_stpmin, tempx2_stpmax = turning_points(smooth(tempx2,20)) # Removes stuff.
    
    if not tempx2_stpmin: # making sure tempx2_stpmin has values, else skip data point
        print 'unable to find any minimums to work with'
        return
    
    # this is to fix for turning_points incorrectly marking certain peaks as minimums...
    temp = []
    for i in tempx2_stpmin:
        if tempx2[i] <= 50:
            temp.append(i)         
    tempx2_stpmin = temp
    
    if len(tempx2_stpmin) < 2: # making sure tempx2_stpmin has values, else skip data point
        print 'not enough minimums to work with'
        return
    
    for i in range(tempx2_stpmin[0],tempx2_stpmin[1]):
        tempe.append(tempv[i]) # angle v
        tempa.append(tempw[i]) # bheight w
        tempb.append(tempx2[i]) # ecr x
        tempc.append(tempy[i]) # lon y
        tempd.append(tempz[i]) # alt z
        tempt2.append(tempt[i]) # time t
        tempyy2.append(tempyy[i]) # year yy
        
        
    #def gaussian(x, amp, cen, wid):
    #    "1-d gaussian: gaussian(x, amp, cen, wid)"
    #    return (amp/(np.sqrt(2*np.pi)*wid)) * np.exp(-(x-cen)**2 /(2*wid**2))
    #
    #def func(x, a, x0, sigma):
    #    return a*np.exp(-(x-x0)**2/(2*sigma**2))
        
    def gaussian(x, *p):
        A, mu, sigma_squared = p
        return A*np.exp(-(x-mu)**2/(2.*sigma_squared))
        
    tempb = np.array(tempb) # As it's not a true np array...
    tempt2 = np.array(tempt2) # As it's not a true np array...
    
    """ gaussian sigma -> sigma_squared
    test sigma -> peak max min
    https://stackoverflow.com/questions/47773178/gaussian-fit-returning-negative-sigma"""        
    
    # dday - ecr
#    peak = tempt2[tempb > (np.exp(-0.5)*tempb.max())]
#    if len(peak) < 5: # 2 is min, 5 to be safe.
#        print 'not enough data in peak'
#        return
#    guess_sigma = 0.5*(peak.max() - peak.min()) 
#    p0_vals = [max(tempb),tempt2[np.argmax(tempb)],guess_sigma**2] # ie amp = max ; cen = max position in time ; wid = optimise
    
    # angle - ecr
    tempe = np.array(tempe) # As it's not a true np array...
    peak = tempe[tempb > (np.exp(-0.5)*tempb.max())]
    guess_sigma = 0.5*(peak.max() - peak.min())
    p0_vals = [max(tempb),tempe[np.argmax(tempb)],guess_sigma**2] # ie amp = max ; cen = max position in time ; wid = optimise

    
    
    try:
        # dday - ecr
        #popt, pcov = curve_fit(gaussian, np.concatenate(tempt2, axis=0 ), np.asarray(tempb), p0_vals, maxfev = 6400)
        #popt, pcov, infodict, errmsg, ier = curve_fit(gaussian, np.concatenate(tempt2, axis=0 ), np.asarray(tempb), p0_vals, maxfev = 6400, full_output = True)
        
        # angle - ecr
        popt, pcov, infodict, errmsg, ier = curve_fit(gaussian, np.concatenate(tempe, axis=0 ), np.asarray(tempb), p0_vals, maxfev = 6400, full_output = True)
        
        #0 popt, 1 pcov, 2 infodict, 3 errmsg, 4 ier
    except RuntimeError:
        print("Error - curve_fit failed")
        plt.clf()
        plt.plot(tempb)
        print max(tempb)
        plt.savefig("failed.png")
        return # Report error but don't crash.
    
    #%%
    
    # 
    s_sq = (infodict['fvec']**2).sum()/ (len(infodict['fvec'])-len(popt))
    
    gaussfile = "gaussfit" + str(this_sat) + ".txt"
    with open(gaussfile, 'a') as f:
        DAT = np.asarray([this_sat, tempyy2[np.argmax(tempb)], popt[0], popt[1], np.sqrt(popt[2]), s_sq])
        #print DAT
        #fmt='%i %i %f %f %f %f'
        np.savetxt(f, DAT[None], fmt='%i %i %f %f %f %f')
        print 'Data writen to file.'
    return # end function


def gauss_plot(satlist):
    for this_sat in satlist:        
        gaussfile = "gaussfit" + str(this_sat) + ".txt"        
        satnum, yyyy, amp, cen, sig, rsquared, s_sq = np.loadtxt(gaussfile,delimiter=' ', unpack=True)
        
        ourdates = []
        for i in range(len(cen)):
            ourdates.append(datetime(int(yyyy[i]),1,1,0,0,0) + timedelta(days=cen[i]))
        # convert between datetime objects and matplotlib format
        ourmpldates = mpld.date2num(ourdates)
        
        def yearline(yyyy):
            for i in range(len(yyyy)):
                datetime(int(yyyy[i]),1,1,0,0,0)
                plt.axvline(x=datetime(int(yyyy[i]),1,1,0,0,0))
        
#        fig = plt.figure(figsize=(30, 30), dpi=80)
#        plt.subplot(411)
#        plt.plot_date(ourmpldates,sig, label='Sig')
#        yearline(yyyy)
#        #plt.legend(loc='center left')
#        plt.subplot(412)
#        plt.plot_date(ourmpldates,amp, label='Amp')
#        yearline(yyyy)
#        plt.subplot(413)
#        plt.plot_date(ourmpldates,rsquared, label='rsquared of fit')
#        yearline(yyyy)
#        plt.axhline(y=1)
#        plt.subplot(414)
#        plt.hist(amp, label='distribution of amp values')
        
        #%%
        
        fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1, figsize=(20,10), dpi=80)
        
        L1, = ax1.plot_date(ourmpldates,sig, label='Sig')
        L2, = ax2.plot_date(ourmpldates,amp, label='Amp')
        L3, = ax3.plot_date(ourmpldates,rsquared, label='rsquared of fit')
        L4, = ax4.hist(amp, label='distribution of amp values')
        
        lgd = ax1.legend( handles=[L1, L2, L3, L4], loc="upper left", bbox_to_anchor=[1.1, 1.05],
           ncol=2, shadow=True, title="Legend", fancybox=True)
        
        #fig.show()
        plt.savefig('foo.png', bbox_extra_artists=(lgd,), bbox_inches='tight')
        #%%

        
        stemp = "gaussfit" + str(this_sat) + "_plot.png"
        plt.savefig(stemp,bbox_inches="tight")
        fig.clear() #cleanup
        plt.clf() #cleanup
        plt.cla() #cleanup
        plt.close(fig) #cleanup


def method2(this_sat, ecr, pcr, dday, year, satalt, bheight, ourmpldates, angle, sat_lon):
    """ 
        1) ecr average    np.mean(ch0)
        2) ecr maximum averaged    np.mean(ch0[ch0_maxf])
        3) ecr-dday width at 100 counts    peak_dday_width
        4) ecr-angle width at 100 counts?     peak_angle_width
        5) flight velocity    velocity
        6) orbital period    period (s), periodm (m), periodh (h)
    """
    
    if len(np.unique(sat_lon)) < len(sat_lon)*0.5: # making sure lon_tpmin has values, else skip data point
        print 'Low data quality or loaded two data files.'
        return
    
    ch0 = np.copy(ecr[:,0])
    ch0[ch0 < 50] = 0 # removes noise
    
    ch0_min, ch0_max = turning_points(smooth(ch0,20))
    
    temp = []
    for i in ch0_max: # filter maximums that are below the mean
        if ch0[i] >= np.mean(ch0):
            temp.append(i) 
    ch0_maxf = temp
    
    temp = []
    for i in ch0_min:
        if ch0[i] <= 10:
            temp.append(i)
    ch0_minf = temp
    
    #%%
    
    if len(ch0_minf) >= 2:
        i = 0
        peak_dday_width = []
        peak_angle_width = []
        while True:
            # Lower 100 count check
            tempL = ch0_minf[i]
            while True:
                tempL += 1
                if ch0[tempL] >= 200: # ie lock value when ch0 exceedes 100 counts
                    break
                elif tempL+1 >= len(ch0):
                    print 'unable to lock'
                    return
            
            # Upper 100 count check
            tempU = ch0_minf[i + 1]
            while True:
                tempU -= 1
                if ch0[tempU] >= 200: # ie lock value when ch0 exceedes 100 counts
                    break
                elif tempU-1 >= len(ch0):
                    print 'unable to lock'
                    return
            
            i += 1
            peak_dday_width.append(dday[tempU] - dday[tempL])
            peak_angle_width.append([angle[tempL], angle[tempU]])
            if i+1 >= len(ch0_minf): # checking if secondary condition exceeds size.
                break
    else:
        print 'ch0_minf less than 2.'
        return
    
    #tempx = []
    #tempy = []
    #
    #for i in range(ch0_minf[0],ch0_minf[1]):
    #    tempx.append(angle[i])
    #    tempy.append(ch0[i])
    #    
    #    
    #plt.plot(tempx,tempy)
    #plt.show()
    
    #%%
    # Conversion http://keisan.casio.com/exec/system/1224665242    
        
    Re = 6378.14 # km
    
    velocity = np.sqrt(398600.5 / (Re * satalt)) # km/s
    period = 2 * np.pi * (Re * satalt) / velocity # sec
    periodm = period / 60
    periodh = periodm / 60
    
    #%%
    
    #temp2 = []
    #for i in range(len(dday)-1):
    #    temp2.append(dday[i+1] - dday[i])
    #
    #
    ## dt is set globally now...
    ##dt = 0.0666667 # 4 minutes in hours
    ##dt = 0.066672
    ##dt = 4.0 / 60.0 / 24.0
    #
    ## Do FFT analysis of array
    #FFT = scipy.fft(smooth(ch0,20))
    #
    ## Getting the related frequencies
    #freqs = scipy.fftpack.fftfreq(len(ch0), dt)
    #
    #plt.subplot(211)
    #plt.plot(dday,smooth(ch0,20))
    #plt.xlabel('dday')
    #plt.ylabel('ch0')
    #plt.subplot(212)
    #plt.plot(freqs, scipy.log10(abs(FFT)), '.')
    #plt.xlim(-50, 50)   
    #plt.show()
    
    """
        1) ecr average    np.mean(ch0)
        2) ecr maximum averaged    np.mean(ch0[ch0_maxf])
        3) ecr-dday width at 100 counts    peak_dday_width
        4) ecr-angle width at 100 counts?     peak_angle_width
        5) flight velocity    velocity
        6) orbital period    period (s), periodm (m), periodh (h)
    """
    
    peak_angle_width_f = peak_angle_width
    #toggle = 0
    for i in range(len(peak_angle_width)):
        if peak_angle_width[i][1] > peak_angle_width[i][0]: # -35, 65
            pass
        else: # i[0] > i[1] ie 35, -65
            peak_angle_width_f[i] = [-peak_angle_width[i][0], -peak_angle_width[i][1]] # ie invert points.
    peak_angle_width_f = np.array(peak_angle_width_f)       
    
    
    #print dday[int(len(dday)/2)]
    #print year[int(len(dday)/2)]
    #
    #print np.mean(ch0)
    #print scipy.stats.sem(ch0) # standard error in ch0
    #print np.mean(ch0[ch0_maxf])
    #print scipy.stats.sem(ch0[ch0_maxf]) # standard error in peaks ch0
    #print np.mean(peak_dday_width)
    #print scipy.stats.sem(peak_dday_width) # standard error in dday width
    #
    #print peak_angle_width_f.min()
    #print scipy.stats.sem(peak_angle_width_f)[0] # standard error in angle width min
    #print peak_angle_width_f.mean()
    #print scipy.stats.sem(peak_angle_width_f).mean() # standard error in angle width mean
    #print peak_angle_width_f.max()
    #print scipy.stats.sem(peak_angle_width_f)[1] # standard error in angle width max
    #
    #
    #print np.mean(velocity)
    #print scipy.stats.sem(velocity) #standard error in width
    #print np.mean(periodm)
    #print scipy.stats.sem(periodm) #standard error in width
    
    #DAT = np.asarray([dday[int(len(dday)/2)], year[int(len(dday)/2)], 
    #                       np.mean(ch0), scipy.stats.sem(ch0), 
    #                       np.mean(ch0[ch0_maxf]), scipy.stats.sem(ch0[ch0_maxf]), 
    #                       np.mean(peak_dday_width), scipy.stats.sem(peak_dday_width),
    #                       peak_angle_width_f.min(), scipy.stats.sem(peak_angle_width_f)[0],
    #                       peak_angle_width_f.mean(), scipy.stats.sem(peak_angle_width_f).mean(),
    #                       peak_angle_width_f.max(), scipy.stats.sem(peak_angle_width_f)[1],
    #                       np.mean(velocity), scipy.stats.sem(velocity),
    #                       np.mean(periodm), scipy.stats.sem(periodm)
    #                       ])
    
    statdata = "statdata" + str(this_sat) + ".txt"
    with open(statdata, 'a') as f:
        DAT = np.asarray([dday[int(len(dday)/2)], year[int(len(dday)/2)], 
                           np.mean(ch0), scipy.stats.sem(ch0), 
                           np.mean(ch0[ch0_maxf]), scipy.stats.sem(ch0[ch0_maxf]), 
                           np.mean(peak_dday_width), scipy.stats.sem(peak_dday_width),
                           peak_angle_width_f.min(), scipy.stats.sem(peak_angle_width_f)[0],
                           peak_angle_width_f.mean(), scipy.stats.sem(peak_angle_width_f).mean(),
                           peak_angle_width_f.max(), scipy.stats.sem(peak_angle_width_f)[1],
                           (np.mean(peak_angle_width_f[:,1]) - np.mean(peak_angle_width_f[:,0])), scipy.stats.sem(np.mean(peak_angle_width_f[:,1]) - np.mean(peak_angle_width_f[:,0])),
                           np.mean(velocity), scipy.stats.sem(velocity),
                           np.mean(periodm), scipy.stats.sem(periodm)
                           ]) # 10 x 2
        #print DAT
        #fmt='%i %i %f %f %f %f'
        np.savetxt(f, DAT[None], fmt='%f %i %f %f %f %f %f %f %f %f %f %f %f %f %f %f %f %f %f %f')
        print 'Data writen to file.'

def method2_plot(satlist):
    for this_sat in satlist:        
        statfile = "statdata" + str(this_sat) + ".txt"
        # This assignment is silly... but I don't believe I can shorten it.        
        dday, year, ch0mean, ch0meanse, peakmean, peakmeanse, pdw, pdwse, pawmin, pawminse, pawmean, pawmeanse, pawmax, pawmaxse, paww, pawwse, vel, velse, periodm, periodmse = np.loadtxt(statfile, delimiter=' ', unpack=True) # 18
        
        ourdates = []
        for i in range(len(dday)):
            ourdates.append(datetime(int(year[i]),1,1,0,0,0) + timedelta(days=dday[i]))
        # convert between datetime objects and matplotlib format
        ourmpldates = mpld.date2num(ourdates)
        
        def yearline(yyyy):
            for i in range(len(yyyy)):
                datetime(int(yyyy[i]),1,1,0,0,0)
                plt.axvline(x=datetime(int(yyyy[i]),1,1,0,0,0))
        
#        fig = plt.figure(figsize=(30, 30), dpi=80)
#        plt.subplot(411)
#        plt.plot_date(ourmpldates,sig, label='Sig')
#        yearline(yyyy)
#        #plt.legend(loc='center left')
#        plt.subplot(412)
#        plt.plot_date(ourmpldates,amp, label='Amp')
#        yearline(yyyy)
#        plt.subplot(413)
#        plt.plot_date(ourmpldates,rsquared, label='rsquared of fit')
#        yearline(yyyy)
#        plt.axhline(y=1)
#        plt.subplot(414)
#        plt.hist(amp, label='distribution of amp values')
        
        #%%
        
        fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1, figsize=(20,10), dpi=80)
        
        L1, = ax1.plot_date(ourmpldates,sig, label='Sig')
        L2, = ax2.plot_date(ourmpldates,amp, label='Amp')
        L3, = ax3.plot_date(ourmpldates,rsquared, label='rsquared of fit')
        L4, = ax4.hist(amp, label='distribution of amp values')
        
        lgd = ax1.legend( handles=[L1, L2, L3, L4], loc="upper left", bbox_to_anchor=[1.1, 1.05],
           ncol=2, shadow=True, title="Legend", fancybox=True)
        
        #fig.show()
        plt.savefig('foo.png', bbox_extra_artists=(lgd,), bbox_inches='tight')
        #%%

        
        stemp = "gaussfit" + str(this_sat) + "_plot.png"
        plt.savefig(stemp,bbox_inches="tight")
        fig.clear() #cleanup
        plt.clf() #cleanup
        plt.cla() #cleanup
        plt.close(fig) #cleanup


def main():
    truestart = datetime(2000,12,31,0,0,0) # 2001,1,7,0,0,0
    
    start_date = datetime(2001,1,7,0,0,0);
    end_date = datetime(2017,1,10,0,0,0);
    #start_date = datetime(2001,3,4,0,0,0);
    #end_date = datetime(2001,3,10,0,0,0);
    
    localpath = abspath(getsourcefile(lambda:0))[:-12]
    satlist = []
#    satlist.extend([41,48])
#    satlist.extend([53,54,55,56,57,58,59])
#    satlist.extend([60,61,62,63,64,65,66,67,68,69])
    satlist.extend([70,71,72,73])
#    satlist = [41]
    
    maxsizeondisk = 100 # given in GB.
    
    print 'Path on disk: %s' % (localpath)
    print 'Satlist: %s' % (satlist)
    print 'Start datetime: %s end datetime: %s' % (start_date, end_date)
    print '###'
    
    #%%
    
    cdstart = truestart # Current Date we are looking at.
    while True:
        cdstart += relativedelta(days=7)
        if cdstart >= start_date:
            break
    
    #cdstart = start_date
    #cdend = end_date
    cdend = cdstart + relativedelta(days=6)
    
    #%%
    
    while True:
        
        print 'cdstart - %s' % (cdstart)
        print 'cdend - %s' % (cdend)
        
        # do stuff
        for this_sat in satlist:
            ecr, pcr, dday, year, satalt, bheight, ourmpldates, angle, sat_lon = load_data(this_sat,cdstart,cdend,localpath)
            if len(ecr) > 10:
                #fit(this_sat, ecr, pcr, dday, year, satalt, bheight, ourmpldates, angle, sat_lon)
                method2(this_sat, ecr, pcr, dday, year, satalt, bheight, ourmpldates, angle, sat_lon)
            print ' '
        # plot
        
        #cdstart += relativedelta(weeks=+52)
        cdstart += relativedelta(weeks=+1)
        cdend = cdstart + relativedelta(days=+6)
    
        if cdend.year >= end_date.year and cdend.month >= end_date.month:
            gc.collect()
            break
        
if __name__ == '__main__':
    main()
            

##satlist = []
##satlist.extend([41,48])
##satlist.extend([53,54,55,56,57,58,59])
##satlist.extend([60,61,62,63,64,65,66,67,68,69])
##satlist.extend([70,71,72,73])
#
##
##gauss_plot([41])
#            
#truestart = datetime(2000,12,31,0,0,0) # 2001,1,7,0,0,0
#
#start_date = datetime(2001,1,7,0,0,0);
#end_date = datetime(2017,1,10,0,0,0);
##start_date = datetime(2001,3,4,0,0,0);
##end_date = datetime(2001,3,10,0,0,0);
#
#localpath = abspath(getsourcefile(lambda:0))[:-12]
#satlist = [41]
#this_sat = 41
#
#cdstart = truestart # Current Date we are looking at.
#while True:
#    cdstart += relativedelta(days=7)
#    if cdstart >= start_date:
#        break
#
##cdstart = start_date
##cdend = end_date
#cdend = cdstart + relativedelta(days=6)
#       
#ecr, pcr, dday, year, satalt, bheight, ourmpldates, angle, sat_lon = load_data(this_sat,cdstart,cdend,localpath)
#
##def method2(this_sat, ecr, pcr, dday, year, satalt, bheight, ourmpldates, angle, sat_lon):
#""" 
#    1) ecr average    np.mean(ch0)
#    2) ecr maximum averaged    np.mean(ch0[ch0_maxf])
#    3) ecr-dday width at 100 counts    peak_dday_width
#    4) ecr-angle width at 100 counts?     peak_angle_width
#    5) flight velocity    velocity
#    6) orbital period    period (s), periodm (m), periodh (h)
#"""
#
#if len(np.unique(sat_lon)) < len(sat_lon)*0.5: # making sure lon_tpmin has values, else skip data point
#    print 'Low data quality or loaded two data files.'
##    return
#
#ch0 = np.copy(ecr[:,0])
#ch0[ch0 < 50] = 0 # removes noise
#
#ch0_min, ch0_max = turning_points(smooth(ch0,20))
#
#temp = []
#for i in ch0_max: # filter maximums that are below the mean
#    if ch0[i] >= np.mean(ch0):
#        temp.append(i) 
#ch0_maxf = temp
#
#temp = []
#for i in ch0_min:
#    if ch0[i] <= 10:
#        temp.append(i)
#ch0_minf = temp
#
##%%
#
#if len(ch0_minf) >= 2:
#    i = 0
#    peak_dday_width = []
#    peak_angle_width = []
#    while True:
#        # Lower 100 count check
#        tempL = ch0_minf[i]
#        while True:
#            tempL += 1
#            if ch0[tempL] >= 200: # ie lock value when ch0 exceedes 100 counts
#                break
#        
#        # Upper 100 count check
#        tempU = ch0_minf[i + 1]
#        while True:
#            tempU -= 1
#            if ch0[tempL] >= 200: # ie lock value when ch0 exceedes 100 counts
#                break
#        
#        i += 1
#        peak_dday_width.append(dday[tempU] - dday[tempL])
#        peak_angle_width.append([angle[tempL], angle[tempU]])
#        if i+1 >= len(ch0_minf): # checking if secondary condition exceeds size.
#            break
#
##tempx = []
##tempy = []
##
##for i in range(ch0_minf[0],ch0_minf[1]):
##    tempx.append(angle[i])
##    tempy.append(ch0[i])
##    
##    
##plt.plot(tempx,tempy)
##plt.show()
#
##%%
## Conversion http://keisan.casio.com/exec/system/1224665242    
#    
#Re = 6378.14 # km
#
#velocity = np.sqrt(398600.5 / (Re * satalt)) # km/s
#period = 2 * np.pi * (Re * satalt) / velocity # sec
#periodm = period / 60
#periodh = periodm / 60
#
##%%
#
##temp2 = []
##for i in range(len(dday)-1):
##    temp2.append(dday[i+1] - dday[i])
##
##
### dt is set globally now...
###dt = 0.0666667 # 4 minutes in hours
###dt = 0.066672
###dt = 4.0 / 60.0 / 24.0
##
### Do FFT analysis of array
##FFT = scipy.fft(smooth(ch0,20))
##
### Getting the related frequencies
##freqs = scipy.fftpack.fftfreq(len(ch0), dt)
##
##plt.subplot(211)
##plt.plot(dday,smooth(ch0,20))
##plt.xlabel('dday')
##plt.ylabel('ch0')
##plt.subplot(212)
##plt.plot(freqs, scipy.log10(abs(FFT)), '.')
##plt.xlim(-50, 50)   
##plt.show()
#
#"""
#    1) ecr average    np.mean(ch0)
#    2) ecr maximum averaged    np.mean(ch0[ch0_maxf])
#    3) ecr-dday width at 100 counts    peak_dday_width
#    4) ecr-angle width at 100 counts?     peak_angle_width
#    5) flight velocity    velocity
#    6) orbital period    period (s), periodm (m), periodh (h)
#"""
#
#peak_angle_width_f = peak_angle_width
#toggle = 0
#for i in range(len(peak_angle_width)):
#    if peak_angle_width[i][1] > peak_angle_width[i][0]: # -35, 65
#        pass
#    else: # i[0] > i[1] ie 35, -65
#        peak_angle_width_f[i] = [-peak_angle_width[i][0], -peak_angle_width[i][1]] # ie invert points.
#peak_angle_width_f = np.array(peak_angle_width_f)       
#
#
##print dday[int(len(dday)/2)]
##print year[int(len(dday)/2)]
##
##print np.mean(ch0)
##print scipy.stats.sem(ch0) # standard error in ch0
##print np.mean(ch0[ch0_maxf])
##print scipy.stats.sem(ch0[ch0_maxf]) # standard error in peaks ch0
##print np.mean(peak_dday_width)
##print scipy.stats.sem(peak_dday_width) # standard error in dday width
##
##print peak_angle_width_f.min()
##print scipy.stats.sem(peak_angle_width_f)[0] # standard error in angle width min
##print peak_angle_width_f.mean()
##print scipy.stats.sem(peak_angle_width_f).mean() # standard error in angle width mean
##print peak_angle_width_f.max()
##print scipy.stats.sem(peak_angle_width_f)[1] # standard error in angle width max
##
##
##print np.mean(velocity)
##print scipy.stats.sem(velocity) #standard error in width
##print np.mean(periodm)
##print scipy.stats.sem(periodm) #standard error in width
#
##DAT = np.asarray([dday[int(len(dday)/2)], year[int(len(dday)/2)], 
##                       np.mean(ch0), scipy.stats.sem(ch0), 
##                       np.mean(ch0[ch0_maxf]), scipy.stats.sem(ch0[ch0_maxf]), 
##                       np.mean(peak_dday_width), scipy.stats.sem(peak_dday_width),
##                       peak_angle_width_f.min(), scipy.stats.sem(peak_angle_width_f)[0],
##                       peak_angle_width_f.mean(), scipy.stats.sem(peak_angle_width_f).mean(),
##                       peak_angle_width_f.max(), scipy.stats.sem(peak_angle_width_f)[1],
##                       np.mean(velocity), scipy.stats.sem(velocity),
##                       np.mean(periodm), scipy.stats.sem(periodm)
##                       ])
#
#statdata = "statdata" + str(this_sat) + ".txt"
#with open(statdata, 'a') as f:
#    DAT = np.asarray([dday[int(len(dday)/2)], year[int(len(dday)/2)], 
#                       np.mean(ch0), scipy.stats.sem(ch0), 
#                       np.mean(ch0[ch0_maxf]), scipy.stats.sem(ch0[ch0_maxf]), 
#                       np.mean(peak_dday_width), scipy.stats.sem(peak_dday_width),
#                       peak_angle_width_f.min(), scipy.stats.sem(peak_angle_width_f)[0],
#                       peak_angle_width_f.mean(), scipy.stats.sem(peak_angle_width_f).mean(),
#                       peak_angle_width_f.max(), scipy.stats.sem(peak_angle_width_f)[1],
#                       np.mean(velocity), scipy.stats.sem(velocity),
#                       np.mean(periodm), scipy.stats.sem(periodm)
#                       ])
#    #print DAT
#    #fmt='%i %i %f %f %f %f'
#    np.savetxt(f, DAT[None], fmt='%f %i %f %f %f %f %f %f %f %f %f %f %f %f %f %f %f %f')
#    print 'Data writen to file.'
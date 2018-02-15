# -*- coding: utf-8 -*-
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

from inspect import getsourcefile
from os.path import abspath

#in order to address memory issues...
import gc
 
#start_date = datetime(2001,1,7,0,0,0);
#end_date = datetime(2001,1,13,0,0,0);
start_date = datetime(2015,1,7,0,0,0);
end_date = datetime(2015,1,13,0,0,0);
#localpath = 'D:\\jackj\\Documents\\GitHub\\EQPB_2017\\'
localpath = abspath(getsourcefile(lambda:0))[:-11]
satlist = []
satlist.extend([41,48])
satlist.extend([53,54,55,56,57,58,59])
satlist.extend([60,61,62,63,64,65,66,67,68,69])
satlist.extend([70,71,72,73])
#satlist = [41]

maxsizeondisk = 100 # given in GB.

print 'Path on disk: %s' % (localpath)
print 'Satlist: %s' % (satlist)
print 'Start datetime: %s end datetime: %s' % (start_date, end_date)
print '###'

#%%
#Check if gps sat data exists. Download if missing.
#gps_particle_data.gps_satellite_data_download(start_date,end_date,satlist,localpath,maxsizeondisk)

def add_years(d, years):
    """Return a date that's `years` years after the date (or datetime)
    object `d`. Return the same calendar date (month and day) in the
    destination year, if it exists, otherwise use the following day
    (thus changing February 29 to March 1).

    """
    try:
        return d.replace(year = d.year + years)
    except ValueError:
        return d + (date(d.year + years, 1, 1) - date(d.year, 1, 1))

truestart = datetime(2000,12,31,0,0,0) # 2001,1,7,0,0,0
cdstart = truestart
while True:
    cdstart += relativedelta(days=7)
    if cdstart >= start_date:
        break

#cdstart = start_date
cdend = end_date #cdstart + relativedelta(days=6)



while True:
    print 'cdstart - %s' % (cdstart)
    print 'cdend - %s' % (cdend)
    for this_sat in satlist:
        # Load data.
        ms = gps_particle_data.meta_search(this_sat,localpath) # Do not pass meta_search satlist. Single sat ~12GB of RAM.
        ms.load_local_data(cdstart,cdend)
        ms.clean_up() #deletes json files.
        print ''
        
        output_data = ms.get_all_data_by_satellite()
        del ms # save RAM once we are finished.
        gc.collect()
        
        if len(output_data[this_sat]) != 0:
    
            ddata = output_data[this_sat]['dropped_data']
            index2drop = [i for i, j in enumerate(ddata) if j == 1]
            del ddata # save RAM once we are finished.
            
            #temp_rem2 = np.asarray(output_data[this_sat]['rate_electron_measured'])[:,2]
            #ch2 = np.delete(temp_rem2,index2drop)
            #del temp_rem2 # save RAM once we are finished.
            
            temp_ecr = np.asarray(output_data[this_sat]['rate_electron_measured'])
            ecr = np.delete(temp_ecr,index2drop,0)
            del temp_ecr # save RAM once we are finished.
            
            temp_pcr = np.asarray(output_data[this_sat]['rate_proton_measured'])
            pcr = np.delete(temp_pcr,index2drop,0)
            del temp_pcr # save RAM once we are finished.
            
            temp_dday =  output_data[this_sat]['decimal_day']
            dday = np.delete(temp_dday,index2drop) - 1 # offset dday by -1 to let it work with timedelta better.
            del temp_dday # save RAM once we are finished.
            
            temp_year = output_data[this_sat]['year']
            year = np.delete(temp_year,index2drop)
            del temp_year # save RAM once we are finished.
            
            temp_alt = output_data[this_sat]['Rad_Re']
            satalt = np.delete(temp_alt,index2drop)
            del temp_alt # save RAM once we are finished.
            
            temp_bheight = output_data[this_sat]['b_coord_height']
            bheight = np.delete(temp_bheight,index2drop)
            del temp_bheight # save RAM once we are finished.
            
            del output_data # save RAM once we are finished.
            del index2drop # save RAM once we are finished.
            gc.collect()
            
            ourdates = []
            for i in range(len(dday)):
                ourdates.append(datetime(int(year[i]),1,1,0,0,0) + timedelta(days=dday[i]))
            
            # convert between datetime objects and matplotlib format
            ourmpldates = mpld.date2num(ourdates)
            #del ourdates # save RAM once we are finished.
            
            #Get angles from height and alt.
            angle = np.degrees(np.arcsin((bheight/satalt)))
            
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
            plt.plot(ecr[:,0]/np.gradient(satalt))
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
            T = 4.0 * 60.0 # 4 minutes in seconds
            #T = 4 # minutes
            #T = 1.0 * 4/60 # 4 minutes in terms of hours
            
            #a = scipy.fftpack.fft(ecr[:,0])
            #b = scipy.fftpack.fft(satalt)
            #c = scipy.fftpack.fft(angle)
            
            mag_a = np.fft.rfft(ecr[:,0]/ecr[:,0].max()) #normalise values
            freq_a = np.fft.rfftfreq(N,T) # length,time diff
            
            mag_b = np.fft.rfft(satalt/satalt.max()) #normalise values
            freq_b = np.fft.rfftfreq(N,T) # length,time diff
            
            mag_c = np.fft.rfft(angle/angle.max()) #normalise values
            freq_c = np.fft.rfftfreq(N,T) # length,time diff
            #%%
            
            ax20 = plt.subplot(gs1[8,:])   # 3:   :-3
            plt.plot(freq_a, mag_a)
            plt.ylabel('Magnitude', fontsize = 16)
            plt.xlabel('Frequency (sec)', fontsize  = 16)
            
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
            plt.xlabel('Frequency (sec)', fontsize  = 16)
            
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
            plt.xlabel('Frequency (sec)', fontsize  = 16)
            
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
            
#            del angle
#            del bheight
#            del curlabel
#            del dday
#            del ecr
#            del i
#            del j
#            del ourdates
#            del ourmpldates
#            del pcr
#            del points1
#            del points2
#            del points3
#            del points4
#            del points5
#            del points6
#            del points7
#            del points8
#            del points9
#            del stemp
#            del titletext
#            del year
#            del fig
            
            gc.collect()
        
        else:
            print 'Skipping %s as it has no data for this timeframe' % (this_sat)
            
    #cdstart = add_years(cdstart,1)
    #cdend = add_years(cdend,1)
    cdstart += relativedelta(weeks=+52)
    cdend = cdstart + relativedelta(days=+6)

    if cdend.year >= end_date.year and cdend.month >= end_date.month:
        gc.collect()
        break
    
def comparison():
    
    #print 'Numpy Cross-correlation: %s' % (np.correlate(ecr[:,0],satalt))
    #print 'Scipy pearsonr: %s' % (pearsonr(ecr[:,0],satalt))
    #print 'Numpy corrcoef: %s' % (np.corrcoef(ecr[:,0],satalt))

    #plt.plot(ecr[:,0]/np.gradient(satalt))

    #plt.plot(signal.correlate(ecr[:,0], np.gradient(satalt), mode='same'))
    
    print '###'
    
    a = scipy.fftpack.fft(ecr[:,0])
    b = scipy.fftpack.fft(satalt)
    
    print 'Numpy Cross-correlation:'
    print np.correlate(a,b)
    print 'Scipy pearsonr:' 
    print pearsonr(a,b)
    print 'Numpy corrcoef:'
    print np.corrcoef(a,b)
    

    plt.plot(signal.correlate(a,b,mode='same'))
        
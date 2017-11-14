# -*- coding: utf-8 -*-
import gps_particle_data
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mpld
import matplotlib.gridspec as gridspec
 

start_date = datetime(2001,1,1,0,0,0);
end_date = datetime(2017,1,1,0,0,0);
localpath = 'D:\\jackj\\Documents\\GitHub\\EQPB_2017\\'
satlist = []
satlist.extend([41,48])
satlist.extend([53,54,55,56,57,58,59])
satlist.extend([60,61,62,63,64,65,66,67,68,69])
satlist.extend([70,71,72,73])

maxsizeondisk = 100 # given in GB.

localfolder = 'data\\'
rawf = 'raw\\'
vdl = 'var_dL\\'
valt = 'var_alt\\'


print 'Path on disk: %s' % (localpath)
print 'Satlist: %s' % (satlist)
print 'Start datetime: %s end datetime: %s' % (start_date, end_date)
print '###'

#%%
#Check if gps sat data exists. Download if missing.
gps_particle_data.gps_satellite_data_download(start_date,end_date,satlist,localpath,maxsizeondisk)


for this_sat in satlist:
    # Load data.
    ms = gps_particle_data.meta_search(this_sat,localpath) # Do not pass meta_search satlist. Single sat ~12GB of RAM.
    ms.load_local_data(start_date,end_date)
    ms.clean_up() #deletes json files.
    print ''
    
    output_data = ms.get_all_data_by_satellite()
    del ms # save RAM once we are finished.
    
    ddata = output_data[this_sat]['dropped_data']
    index2drop = [i for i, j in enumerate(ddata) if j == 1]
    del ddata # save RAM once we are finished.
    
    temp_rem2 = np.asarray(output_data[this_sat]['rate_electron_measured'])[:,2]
    ch2 = np.delete(temp_rem2,index2drop)
    del temp_rem2 # save RAM once we are finished.
    
    temp_dday =  output_data[this_sat]['decimal_day']
    dday = np.delete(temp_dday,index2drop) - 1 # offset dday by -1 to let it work with timedelta better.
    del temp_dday # save RAM once we are finished.
    
    temp_year = output_data[this_sat]['year']
    year = np.delete(temp_year,index2drop)
    del temp_year # save RAM once we are finished.
    
    temp_alt = output_data[this_sat]['Rad_Re']
    satalt = np.delete(temp_alt,index2drop)
    del temp_alt # save RAM once we are finished.
    
    del output_data # save RAM once we are finished.
    del index2drop # save RAM once we are finished.
    
    ourdates = []
    for i in range(len(dday)):
         ourdates.append(datetime(int(year[i]),1,1,0,0,0) + timedelta(days=dday[i]))
    
    # convert between datetime objects and matplotlib format
    ourmpldates = mpld.date2num(ourdates)
    #del ourdates # save RAM once we are finished.
    
    #%%
    fig = plt.figure(figsize=(20, 13), dpi=160)
    gs1 = gridspec.GridSpec(2, 1)
    gs1.update(wspace=0.0, hspace=0.05)
    
    titletext = 'Raw CH2 data for ns%s' % (this_sat)
    plt.suptitle(titletext, fontsize=20)
    fig.canvas.draw()
    
    ax1 = plt.subplot(gs1[0])
    # Need horizontal line for global CH2 stddev * 4

    #   ch2 - global CH2 avg
    #   ch2 / global CH2 stddev
    plt.plot_date(ourmpldates,ch2)
    plt.ylabel('Electron rate', fontsize = 16)
    plt.setp(ax1.get_xticklabels(), visible=False)
    plt.grid(True)
    
    ax2 = plt.subplot(gs1[1],sharex=ax1)
    plt.plot_date(ourmpldates,satalt)
    plt.ylabel('Earth Radii', fontsize = 16)
    plt.xlabel('Date', fontsize  = 16)
    plt.grid(True)
    
    ax1.set_xlim(mpld.date2num([start_date,end_date]))
    
    stemp = localpath + 'ns' + str(this_sat) + 'ch2plot' + str(start_date.year) + '_' + str(start_date.month) + '_' + str(end_date.year) + '_' + str(end_date.month) + '.png'
    plt.savefig(stemp)
    fig.clear() #cleanup
    plt.close(fig) #cleanup
    
    
#https://plot.ly/python/peak-finding/
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
#from matplotlib import gridspec
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import peakutils

def get_conflvl(path, current_file, this_sat, lthres):
    # setup the current file we are using
    
    print '=== %s' % (current_file)
    
    curdata = np.loadtxt(path + current_file)
    #convert the data into histogram bins.
    bins = np.arange(min(curdata[:,0]), max(curdata[:,0])+1)
    hist, bin_edges = np.histogram(curdata[:,0],bins)
    
    print hist # number of items per bin
    #print bin_edges # interval of each bin.
    
    # n{sig} = (Nmax - Nbg/{sig})     taken from S. Yu Aleksandrin et al.: High-energy charged particle bursts
    
    Nmax = max(hist)
    Nbg = np.median(hist)
    #Nbg = min(hist)
    sig = np.std(hist) #Should be from the background value...
    
    #nsig = (Nmax - Nbg/sig) # Confidence between 10~70 :: approx the plot we want.
    #nsig = (Nmax - Nbg/sig)/sig # -- We want it in a number of standard deviations...
    #nsig = (max(hist) - min(hist[hist!=0]))/float(len(hist))
    nsig = (Nmax - Nbg)/sig # Confidence between 2~2.5 :: wrong shape.
    
    ourstring = 'dL value: %s --- Conf Level: %s' % (lthres, nsig)
    print ourstring
    print 'Nmax, Nbg, sig, nsig'
    print Nmax, Nbg, sig, nsig
    #print min(hist[hist!=0])
    return nsig

def plotdata(path,current_file,this_sat,lthres):
    #plot the data so far
    fig = plt.figure(figsize=(13, 13))
    gs1 = gridspec.GridSpec(3, 1)
    gs1.update(wspace=0.0, hspace=0.05)
    
    slthres = ''.join(e for e in str(lthres) if e.isalnum())
    his = np.loadtxt(path + current_file)
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
    #plt.xlabel(u'ΔT / hours', fontsize  = 30)
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
    plt.ylabel('Satellite L shell', fontsize = 16)
    plt.xlabel(u'ΔT / hours', fontsize  = 16)
    
    plt.savefig(path+slthres+'_histo.png')
    #plt.show()
    fig.clear() #cleanup
    plt.close(fig) #cleanup
  
def getFLandL(path):
    extension = '.ascii'
    dirlist = os.listdir(path)
    
    filelist = []
    L_thres = []
    
    for item in dirlist:
        if item.endswith(extension):
            filelist.append(item)
            if len(item) == 18:
                L_thres.append(float(item[9]+'.'+item[10]+item[11]))
            elif len(item) == 19:
                L_thres.append(float(item[9]+'.'+item[10]+item[11]+item[12]))
            else:
                L_thres.append(float(item[9]+'.'+item[10]+'0'))
    return filelist,L_thres

def smooth(y, box_pts):
    box = np.ones(box_pts)/box_pts
    y_smooth = np.convolve(y, box, mode='same')
    return y_smooth

def get_confpeaks(localpath,this_sat):
    localfolder = 'data\\'
    rawf = 'raw\\'
    vdl = 'var_dL\\'
    valt = 'var_alt\\'
    path = localpath+localfolder+vdl+'ns'+str(this_sat)+'\\'
    filelist,L_thres = getFLandL(path)
    
    conflvl = []
    new_L = []
    
    for i in range(len(filelist)):
        conflvl.append(get_conflvl(path,filelist[i],this_sat,L_thres[i]))
    cb = np.array(smooth(conflvl,5))
    indices = peakutils.indexes(cb, thres=0.02/max(cb), min_dist=0.1)
    for lthres in indices:
        new_L.append(L_thres[lthres])
    
    return new_L

def auto_plot(localpath,this_sat):
    start_time = time.clock()
    localfolder = 'data\\'
    rawf = 'raw\\'
    vdl = 'var_dL\\'
    valt = 'var_alt\\'
    path = localpath+localfolder+vdl+'ns'+str(this_sat)+'\\'
    
    conflvl = []
    
    filelist,L_thres = getFLandL(path)
    
    for i in range(len(filelist)):
        plotdata(path,filelist[i],this_sat,L_thres[i])
        conflvl.append(get_conflvl(path,filelist[i],this_sat,L_thres[i]))
    
    fig = plt.figure(figsize=(13, 13))
    plt.plot(L_thres, conflvl)    
    plt.xticks(np.arange(0.0, max(L_thres)+0.01, 0.01))
    plt.grid(True)
    plttitle = 'Confidence level with differing {delta}L values for Satellite %s' % (this_sat)
    plt.title(plttitle)
    plt.xlabel('{delta}L')
    plt.ylabel('Confidence level')
    plt.savefig(path+'confplot.png')
    plt.show()
    
    print " "
    print "--- %s seconds ---" % (time.clock() - start_time)

#if __name__ == '__main__':
#    localpath = 'D:\\jackj\\Documents\\GitHub\\EQPB_2017\\'
#    this_sat=41
#    auto_plot(localpath,this_sat)
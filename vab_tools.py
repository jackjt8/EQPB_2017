# -*- coding: utf-8 -*-
"""
Created on Fri Feb 02 11:29:21 2018

@author: jackj

vab tools : Van Allen Belt tools
"""

import gps_particle_data
import tc_full

class vab():
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
        
    def loadsat(self, this_sat):
        ms = gps_particle_data.meta_search(this_sat, self.localpath) # Do not pass meta_search satlist. Single sat ~12GB of RAM.
        ms.load_local_data(self.start_date, self.end_date)
        ms.clean_up() #deletes json files.
        
        #!!! Uses too much memory copying data...
        output_data = ms.get_all_data_by_satellite()
        #cleanup
        del ms
        
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
        
    def p_countradii(self, this_sat):
        # plot electron & proton count rates for each channel against sat altitude.
        pass
    
    def p_countlatlon(self, this_sat):
        # plot electron & proton count rates for each channel against sat lat and lon (also mag)
        pass
        
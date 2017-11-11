import gps_particle_data
import tc_dlmp
import tc_conplot
import tc_alt

from datetime import datetime
import numpy as np 


def main():
    start_date = datetime(2008,1,1,0,0,0);
    end_date = datetime(2017,1,1,0,0,0);
    localpath = 'D:\\jackj\\Documents\\GitHub\\EQPB_2017\\'
    satlist = [48]
    #41
    #48 2008-1-1
    L_thres = np.arange(0.01,0.23,0.01)
    #L_thres = [0.005,0.03,0.07,0.10,0.13,0.17]
    alt2test = [i * 100 for i in [1,4,8,12,16,20]]
    maxsizeondisk = 100 # given in GB.
    threads = 6
    
    #%%
    #Check if gps sat data exists. Download if missing.
    gps_particle_data.gps_satellite_data_download(start_date,end_date,satlist,localpath,maxsizeondisk)

    #%%
    # Run the initial temporal correlation
    tc_dlmp.main(start_date,end_date,localpath,satlist,L_thres,maxsizeondisk,threads)
    
    # Get the L value(s) corrisponding to the peak confidence level for each satellite
    msL_thres = []
    i = 0
    for this_sat in satlist:
        msL_thres.append(tc_conplot.get_confpeaks(localpath,this_sat))
        print 'Peaks for ns%s: %s' % (this_sat,msL_thres[i])
        i += 1
    # Rerun temporal correlation with new L values.
    # Need to tweak/add new function to tc_dlmp
    
    # Test the L value(s) that produce the peak confidence
    # msL_thres needs to be a list of len(satlist) long containing lists of dL's.
    tc_alt.main(start_date,end_date,localpath,satlist,msL_thres,maxsizeondisk,alt2test,threads)
    
    print '###'
    print 'Finished all tasks'

if __name__ == '__main__':
    main()


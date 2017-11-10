import tc_dlmp
import tc_alt
import tc_conplot

from datetime import datetime
import numpy as np 


def main():
    start_date = datetime(2015,1,1,0,0,0);
    end_date = datetime(2017,1,1,0,0,0);
    localpath = 'D:\\jackj\\Documents\\GitHub\\EQPB_2017\\'
    satlist = [48,53,54]
    #41,48 + 53-73
    #L_thres = np.arange(0.01,0.21,0.01)
    L_thres = [0.01,0.03,0.07,0.10,0.13,0.20]
    alt2test = [i * 100 for i in [1,4,8,12,16,20]]
    maxsizeondisk = 100 # given in GB.
    threads = 6
    
    #%%
    # Run the initial temporal correlation
    tc_dlmp.main(start_date,end_date,localpath,satlist,L_thres,maxsizeondisk,threads)
    
    # Get the L value(s) corrisponding to the peak confidence level for each satellite
    msL_thres = []
    for this_sat in satlist:
        msL_thres.append(tc_conplot.get_confpeaks(localpath,this_sat))
    print msL_thres
    # Rerun temporal correlation with new L values.
    # Need to tweak/add new function to tc_dlmp
    
    # Test the L value(s) that produce the peak confidence
    # msL_thres needs to be a list of len(satlist) long containing lists of dL's.
    tc_alt.main(start_date,end_date,localpath,satlist,msL_thres,maxsizeondisk,alt2test,threads)

if __name__ == '__main__':
    main()
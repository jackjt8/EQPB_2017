import tc_dlmp
import tc_alt
import tc_conplot

from datetime import datetime
import numpy as np 


def main():
    start_date = datetime(2001,1,1,0,0,0);
    end_date = datetime(2017,1,1,0,0,0);
    localpath = 'D:\\jackj\\Documents\\GitHub\\EQPB_2017\\'
    satlist = [41,48,53]
    L_thres = np.arange(0.01,0.21,0.01)
    #L_thres = [0.022, 0.024, 0.026, 0.028, 0.032, 0.034, 0.036, 0.038]
    alt2test = [i * 100 for i in [1,2,3,4,5,6,7,8,12,16,18,20]]
    maxsizeondisk = 100 # given in GB.
    threads = 8
    
    #%%
    # Run the initial temporal correlation
    tc_dlmp.main(start_date,end_date,localpath,satlist,L_thres,maxsizeondisk,threads)
    
    # Get the L value(s) corrisponding to the peak confidence level for each satellite
    new_L = []
    for this_sat in satlist:
        new_L.append(tc_conplot.get_confpeaks(localpath,this_sat))
    
    # Rerun temporal correlation with new L values.
    # Need to tweak/add new function to tc_dlmp
    
    # Test the L value(s) that produce the peak confidence
    tc_alt.main(start_date,end_date,localpath,satlist,new_L,maxsizeondisk,alt2test,threads)

if __name__ == '__main__':
    main()
# EQPB_2017

Built in/for Python 2.7.13

## Requirements:

- upto 16GB of RAM (worse case)

### Modules

- wget (included)

- numpy

- aacgmv2

- scipy

- matplotlib

- mpl_toolkits.basemap

- PeakUtils

- pathos

## Main modules:

- gps_particle_data

	- Obtains and manages GPS data 
	
	- Obtains and manages earthquake data
	
- tc_dlmp
	
	- Temporal correlation of particle bursts and EQs.
	
	- Saves results to file(s).
	
	- Multithreaded

- tc_conplot

	- Plots TC histograms

	- Plots peak confidence from the TC histogram peak against the dL value.

	- Returns any peaks in the confidence plot as array.

- tc_alt

	- Tests a set of dL values at different altitudes.

	- Saves results to file(s).

## Usage

See below for example use (this code is a mirror of auto.py which is included.)

```
import gps_particle_data
import tc_dlmp
import tc_conplot
import tc_alt
from datetime import datetime

start_date = datetime(2015,1,1,0,0,0);
end_date = datetime(2017,1,1,0,0,0);
localpath = 'D:\\...\\EQPB_2017\\'
satlist = [48,53,54]
L_thres = [0.01,0.03,0.07,0.10,0.13,0.20]
alt2test = [i * 100 for i in [1,4,8,12,16,20]]
maxsizeondisk = 100 # given in GB.
threads = 6

#Check if gps sat data exists. Download if missing.
gps_particle_data.gps_satellite_data_download(start_date,end_date,satlist,localpath,maxsizeondisk)

# Run the initial temporal correlation
tc_dlmp.main(start_date,end_date,localpath,satlist,L_thres,maxsizeondisk,threads)
    
# Get the L value(s) corrisponding to the peak confidence level for each satellite
msL_thres = []
i = 0
for this_sat in satlist:
    msL_thres.append(tc_conplot.get_confpeaks(localpath,this_sat))
    print 'Peaks for ns%s: %s' % (this_sat,msL_thres[i])
    i += 1
    
# Test the L value(s) that produce the peak confidence
# msL_thres needs to be a list of len(satlist) long containing lists of dL's.
tc_alt.main(start_date,end_date,localpath,satlist,msL_thres,maxsizeondisk,alt2test,threads)
    
```

Do not set threads equal to the number of threads you have. Run a test with 1 thread to see what percentage a single thread is, and work from there. Setting threads too high can lead to increased processing time and your system freezing (it should recover). Also recommended that L_thres and alt2test are integer multiple of threads so you do not waste processing time as generally speaking, each element of L_thres should take the same amount of time to process.

L_thres values should be greater than 0.00 and I recommend a limit of 0.30 (Higher values should lead to more noise and reduced confidence). Further recommendation is to test all 0.01 step values from 0.01 to 0.30(or 0.20). Using numpy this can be achieved with: numpy.arange(0.01,0.21,0.01) where the maximum value, 0.20 in this case, needs to be one higher increment, 0.21, in order to be tested.

While this is something that will be included in later builds, you can estimate the runtime of your data set. This can be achieved with a short benchmark of tc_dlmp.main(..) with a single satellite for a year and for a small set of L_thres. The console should print out the result of indices.L_shells, by dividing this result by the average time it takes to complete we have the 'number of calculations per second' (ncps). When you run your full dataset, you can then multiply your ncps by the outputted indices.L_shells value, for an estimate of the run time. (At least for that set of L_thres values)  








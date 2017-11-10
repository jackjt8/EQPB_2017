# EQPB_2017

Built in/for Python 2.7.13

## Requirements:

- upto 16GB of RAM (worse case)

###Modules

- wget (included)

- numpy

- aacgmv2

- scipy

- matplotlib

- mpl_toolkits.basemap

- PeakUtils

## Main modules:

- gps_particle_data

	- Obtains and manages GPS data 
	
	- Obtains and manages earthquake data
	
- tc_dlmp
	
	- Temporal correlation of particle bursts and EQs.
	
	- Saves results to file(s).
	
	- Multithreaded

## Usage

See below for example use.

```
import tc_dlmp

start_date = datetime(2015,1,1,0,0,0);
end_date = datetime(2017,1,1,0,0,0);
localpath = 'D:\\...\\EQPB_2017\\'
satlist = [48,53,54]
L_thres = [0.01,0.03,0.07,0.10,0.13,0.20]
maxsizeondisk = 100 # given in GB.
threads = 6

tc_dlmp.main(start_date,end_date,localpath,satlist,L_thres,maxsizeondisk,threads)
```

Do not set threads equal to the number of threads you have. Run a test with 1 thread to see what percentage a single thread is, and work from there. Setting threads too high can lead to increased processing time and your system freezing (it should recover). Also recommended that L_thres is an integer multiple of threads so you do not waste processing time as generally speaking, each element of L_thres should take the same amount of time to process.


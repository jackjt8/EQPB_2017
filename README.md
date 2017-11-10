# EQPB_2017

Built in/for Python 2.7.13

Do not set threads equal to the number of threads you have. Run a test with 1 thread to see what percentage a single thread is, and work from there. Setting threads too high can lead to increased processing time and your system freezing (it should recover). Also recommended that L_thres is an integer multiple of threads so you do not waste processing time as generally speaking, each element of L_thres should take the same amount of time to process.

### Requires:

- 16GB of RAM or more

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

	- Set conditions in this file: start_date, end_date, localpath, satlist, L_thres, maxsizeondisk
	
	- Temporal correlation of particle bursts and EQs.
	
	- Saves results to file(s).
	
	- Multithreading




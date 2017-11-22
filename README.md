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
    
- tc_full

    - Temporal correlation of particle bursts and EQs with varying dL and altitude
    
    - Saves results to file(s).
	
	- Multithreaded

- tc_conplot (replaced by tc_full)

	- Plots TC histograms

	- Plots peak confidence from the TC histogram peak against the dL value.

	- Returns any peaks in the confidence plot as array.
    
	
- tc_dlmp (replaced by tc_full)
	
	- Temporal correlation of particle bursts and EQs.
	
	- Saves results to file(s).
	
	- Multithreaded

- tc_alt (replaced by tc_full)

	- Tests a set of dL values at different altitudes.

	- Saves results to file(s).

## Usage

Please run 'auto2.py' from commandline to make use of this application.

Do not set threads equal to the number of threads you have. Run a test with 1 thread to see what percentage a single thread is, and work from there. Setting threads too high can lead to increased processing time and your system freezing (it should recover). Also recommended that L_thres and alt2test are integer multiple of threads so you do not waste processing time as generally speaking, each element of L_thres/alt2test should take the same amount of time to process.

L_thres values should be greater than 0.000 and reach to around 0.300. Based upon the geometry, we expect that small dL's, sub 0.07, would be most interesting. I highly recommend if you use any range() function that you use an integer range, using a small float range can lead to floating-point arithmetic issues, and then dividing by say 1000 to get floats.








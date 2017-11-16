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

- tc_conplot

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

Do not set threads equal to the number of threads you have. Run a test with 1 thread to see what percentage a single thread is, and work from there. Setting threads too high can lead to increased processing time and your system freezing (it should recover). Also recommended that L_thres and alt2test are integer multiple of threads so you do not waste processing time as generally speaking, each element of L_thres should take the same amount of time to process.

L_thres values should be greater than 0.00 and I recommend a limit of 0.30 (Higher values should lead to more noise and reduced confidence). Further recommendation is to test all 0.01 step values from 0.01 to 0.30(or 0.20). Using numpy this can be achieved with: numpy.arange(0.01,0.21,0.01) where the maximum value, 0.20 in this case, needs to be one higher increment, 0.21, in order to be tested. NB- Based upon initial findings and the orbit of GPS satellites, it would be prudent to test much more around 0.01, trailing off to 0.07.

While this is something that will be included in later builds, you can estimate the runtime of your data set. This can be achieved with a short benchmark of tc_dlmp.main(..) with a single satellite for a year and for a small set of L_thres. The console should print out the result of indices.L_shells, by dividing this result by the average time it takes to complete we have the 'number of calculations per second' (ncps). When you run your full dataset, you can then multiply your ncps by the outputted indices.L_shells value, for an estimate of the run time. (At least for that set of L_thres values)  








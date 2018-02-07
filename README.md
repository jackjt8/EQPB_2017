# EQPB_2017

Built in/for Python 2.7.13 (64 bit) -- Anaconda

## Requirements:

- 16GB (or more) RAM

Loading all data for SVN41 (16 years 01-01-01 -> 17-01-10) uses 6GB (takes ~50 minutes); when extracting data from metasearch(ms), it is duplicated into output_data, when this occurs memory usage will double (12-14GB) until ms is removed from memory.



### Libraries

- wget (included)

- numpy

- aacgmv2

- scipy

- matplotlib

- mpl_toolkits.basemap

- PeakUtils

- pathos

### Libraries with Anaconda

conda install -c anaconda basemap

pip install aacgmv2

conda install -c conda-forge pathos 

conda install -c conda-forge peakutils 


## Main modules:

- gps_particle_data

	- Obtains and manages GPS data 
	
	- Obtains and manages earthquake data
    
- tc_full

    - Temporal correlation of particle bursts and EQs with varying dL and altitude
    
    - Saves results to file(s)
    
    - Plots confidence level against dL OR against altitude
	
	- Multithreaded



## Usage

Please run 'auto2.py' from commandline to make use of this application.

Do not set threads equal to the number of threads you have. Run a test with 1 thread to see what percentage a single thread is, and work from there. Setting threads too high can lead to increased processing time and your system freezing (it should recover). Also recommended that L_thres and alt2test are integer multiple of threads so you do not waste processing time as generally speaking, each element of L_thres/alt2test should take the same amount of time to process.

L_thres values should be greater than 0.000 and reach to around 0.300. Based upon the geometry, we expect that small dL's, sub 0.070, would be most interesting. I highly recommend if you use any range() function that you use an integer range, using a small float range can lead to floating-point arithmetic issues, and then dividing by say 1000 to get floats.


## Installation for people who have never used Python...

1) Get **Python 2.7** (I recommend [Anaconda](www.anaconda.com/download/))

    - Install Python/Anaconda to the root of you `C:\` Drive. ie along side `C:\Program Files\ C:\Windows\ C:\Users\`

    - If you end up with Anaconda **3.6** you can also get a **2.7** environment with minimal extra work. [See here](conda.io/docs/user-guide/tasks/manage-python.html)

2) Get required libraries. If you have Anaconda, simply Google "anaconda <library name>" and look for anaconda.org (Recommend the conda-forge varients).

    - Once you find the page, you will be given the command to run, ie **conda install -c conda-forge pathos**
    
    - To install, open the **Anaconda Prompt (py27)** and run the command. The prompt should run you through the install.
    
3) Download the program and extract it to a drive with some room. Be sure to note the path to the scripts.

4) Edit **auto2.py** with the parameters you want. You need to define the localpath using double slashes. `localpath = 'D:\\jackj\\Documents\\GitHub\\EQPB_2017\\'`


4) To run, using Commandline (CMD), you need the path to the **\py27\python.exe** and to the script you wish to run.

    - ie `C:\Anaconda35\envs\py27\python.exe D:\jackj\Documents\GitHub\EQPB_2017\auto2.py`






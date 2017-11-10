import gps_particle_dataMOD
import wget
import os
import numpy as np 
import time
import json
import sys
import math
from datetime import datetime, timedelta, date
from itertools import compress
from random import randint
import urllib2
import aacgmv2
import scipy
import matplotlib
from matplotlib import gridspec
import numpy as np
import matplotlib.pyplot as plt

#%%
#localpath = 'D:\\jackj\\Documents\\GitHub\\'
localpath = 'D:\jackj\Documents\GitHub\EQPB_2017\\'
localfolder = 'data\\'
rawf = 'raw\\'
vdl = 'var_dL\\'
valt = 'var_alt\\'
L_thres = np.arange(0.01,0.21,0.01)
#L_thres = np.append(L_thres, [0.50])
n=41
#%%

lthres = 0.01

slthres = ''.join(e for e in str(lthres) if e.isalnum())
current_file = localpath + localfolder + vdl + 'ns41s\\' + 'Ltemp_' + str(n) + '_' + slthres + '.ascii'
print '=== %s' % (current_file)
curdata = np.loadtxt(current_file)

bins = np.arange(min(curdata[:,0]), max(curdata[:,0])+1)
hist, bin_edges = np.histogram(curdata[:,0],bins)
import wget
import os
import os.path
import time
import re
from datetime import datetime
from urllib2 import urlopen
import shutil

localfolder = 'data\\'
rawf = 'raw\\'
prof = 'processed\\'
jsonf = 'json\\'
    
def download_sat (this_sat, start_date, end_date):
    filenames = get_datafiles_in_date(this_sat, start_date, end_date)
    if(filenames==list()):
        return;
        
    print; 
    print '====================================';
    print 'Downloading data for satellite %s to %s' % (this_sat, '...\\' + localfolder + rawf + 'ns' + str(this_sat) + '\\')

    base = 'https://www.ngdc.noaa.gov/stp/space-weather/satellite-data/satellite-systems/gps/data/';
    folder_path = base + 'ns' + str(this_sat) + '/';

    # Load each file
    file_url_list = []
    for f in filenames:

        # Open the particular file 
        full_file_path = folder_path+f;
        # Append the first datafile into the list 
        file_url_list.append(full_file_path)
        
    i = 0
    currentsizeondisk = 0
    for f in file_url_list:
        currentsizeondisk += download(filenames[i],file_url_list[i], this_sat)
        i += 1
        #this checks on a per-file level if we have exceeded maxsizeondisk
        if (totalsizeondisk + currentsizeondisk) >= maxsizeondisk:
            return currentsizeondisk;
    return currentsizeondisk;

def get_datefile_list(this_sat):
    base = 'https://www.ngdc.noaa.gov/stp/space-weather/satellite-data/satellite-systems/gps/data/'
    folder_path = base + 'ns' + str(this_sat) + '/';
    urlpath = urlopen(folder_path);
    files = urlpath.read().decode('utf-8');
        
    start_file_positions = re.finditer('ns' + str(this_sat), files);
        
    # Search for the filenames 
    filelist=[];
    for m in start_file_positions:
        filename = files[m.start():m.start()+23];
        filelist.append(filename);
    return filelist[1::2]; 

def get_datafiles_in_date(this_sat, start_date, end_date):
    filelist = get_datefile_list(this_sat);
    cut_list = [];
        
    for f in filelist:
        year = int(f[5:7])+2000;
        month = int(f[7:9]);
        day = int(f[9:11]);
        d = datetime(year,month,day);
        if ( (d >= start_date ) and (d <= end_date) ):
            cut_list.append(f);
                
    return cut_list;

def download(filename, URL, this_sat):
    src = 'D:\\jackj\\Documents\\GitHub\\SP_2017\\'
    dst = localpath + localfolder + rawf + 'ns' + str(this_sat) + '\\'
    
    # check if we need to download
    if os.path.isfile(dst + filename) != True:
        print '%s is missing, downloading...' % (filename),
        wget.download(URL);
        # moves the file to \data\
        shutil.move(src + filename, dst + filename)
    else:
        print '%s already exists... skipping' % (filename)
        # skips download, but we still want the filesize for later
        fs = file_size(dst + filename)
        return fs;

    # Check if we've downloaded the 404 notice or actual data
    fs = file_size(dst + filename);#This throws an error when wget hasn't finished 
    if(fs<10000):
        print ' |    Failed! Check internet connection or filename',
        print '... deleting file'
        os.remove(dst + filename);
        return 0;
    else:
        print ' |    Success! runtime: %s' % (time.clock() - start_time)
        return fs;

# Helper function to find the file size
def file_size(fname):  
    statinfo = os.stat(fname)  
    return statinfo.st_size 

# Cleans up tmp files from Wget if the download process is interrupted.
def clean_up():
    src = 'D:\\jackj\\Documents\\GitHub\\SP_2017\\'
    extension = '.tmp'
    dirlist = os.listdir(src)
    
    for item in dirlist:
        if item.endswith(extension):
            print 'Cleaning up... %s' % (item)
            os.remove(os.path.join(src, item))

#create folders if they are missing
def createfolders(path):
    try: 
        os.makedirs(path)
    except OSError:
        if not os.path.isdir(path):
            raise

###

start_time = time.clock()
start_date = datetime(2000,1,1,0,0,0);
end_date = datetime(2017,1,1,0,0,0);
#easy to look at sat list...
satlist = []
satlist.extend([41,48])
satlist.extend([53,54,55,56,57,58,59])
satlist.extend([60,61,62,63,64,65,66,67,68,69])
satlist.extend([70,71,72,72,73])
# -- Globally define base and src?
#base = 'https://www.ngdc.noaa.gov/stp/space-weather/satellite-data/satellite-systems/gps/data/' # URL
#src = 'D:\\jackj\\Documents\\GitHub\\SP_2017\\'
localpath = 'D:\\jackj\\Documents\\GitHub\\'
#localfolder = 'data\\'
maxsizeondisk = 100 * 1024 * 1024 * 1024 # GB -> MB -> KB -> B
totalsizeondisk = 0

print 'Satlist: %s' % (satlist)
print 'Start datetime: %s end datetime: %s' % (start_date, end_date)
print 'Location on disk: %s' % (localpath+localfolder)
print 'Maximum size on disk: %s GB' % (float(maxsizeondisk) / 1024 / 1024 / 1024)
print ''

# cleans up files from previous run
clean_up()
print ''

start_time = time.clock()

createfolders(localpath + localfolder)
createfolders(localpath + localfolder + rawf)
createfolders(localpath + localfolder + prof)
createfolders(localpath + localfolder + jsonf)
        
# for each satellite..
for this_sat in satlist:
    #create folders if missing
    createfolders(localpath + localfolder + rawf + 'ns' + str(this_sat) + '\\')
    createfolders(localpath + localfolder + prof + 'ns' + str(this_sat) + '\\')
    createfolders(localpath + localfolder + jsonf + 'ns' + str(this_sat) + '\\')
    temp = 0
    #ensure we don't exceed (by much) the maximum size on disk
    if totalsizeondisk < maxsizeondisk:
        #download file(s) - NOTE - we can be up to 4GB over budget. Need to check
        #totalsizeondisk in download function.
        temp = download_sat(this_sat,start_date,end_date)
        totalsizeondisk += temp
        #for nicer console display....
        temp1 = round((float(temp) / 1024 / 1024 / 1024),4)
        temp2 = round((float(totalsizeondisk) / 1024 / 1024 / 1024),4)
        print '=== Got all data for satellite %s | size %s / %s GB' % (this_sat, temp1, temp2)
    else:
        #if we exceede size limits...
        #print totalsizeondisk / 1024 / 1024 / 1024
        break
    
stemp = float(totalsizeondisk) / 1024 / 1024 / 1024 # B -> KB -> MB -> GB

if totalsizeondisk < maxsizeondisk:
    print ''
    print 'Database download completed in %s. Total size on disk: %s' % ((time.clock() - start_time),stemp)
else:
    print 'Database size limit reached! %s' % (totalsizeondisk)
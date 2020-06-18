#!/usr/bin/env python
u"""
get_hist.py

Download user-requested histograms and save as numpy array.
All strong beams are extracted and saved.

History
    06/16/2020  Written (Yara Mohajerani)
"""
import os
import sys
import h5py
import getopt
import shutil
import numpy as np
from icepyx import icesat2data as ipd

#-- help function
def run_help():
    print("Commandline options:")
    print("Type '--HELP' or '-H' flag for help.")
    print("Type '--DIR=' or '-D:' flag to specify data directory.")
    print("Type '--EXTENT=' or '-E:' flag to specify data spatial extent.")
    print("Type '--DATE=' or '-T:' to specify data date range.")
    print("Type '--USER=' or '-U:' flag to specify EarthData username.")
    print("Type '--EMAIL=' or '-E:' flag to specify EarthData email.")
    print("Type '--noDownload' or '-N' flag to skip downloading data if it's already there.")
    
#-- main function
def main():
    #-- Read the system arguments listed after the program
    long_options=['HELP','DIR=','EXTENT=','DATE=','USER=','EMAIL=','noDownload']
    optlist,arglist = getopt.getopt(sys.argv[1:],'HD:E:T:U:E:N',long_options)

    #-- Set default settings
    ddir = '/home/jovyan/data'
    short_name = 'ATL06'
    spatial_extent = [31.5, -70.56, 33.73, -69.29]
    date_range = ['2020-03-30','2020-04-1']
    user = ''
    email = ''
    download = True

    #-- read commandline inputs
    for opt, arg in optlist:
        if opt in ("-H","--HELP"):
            run_help()
            sys.exit('Done.')
        elif opt in ("-D","--DIR"):
            ddir = os.path.expanduser(arg)
        elif opt in ("-E","--EXTENT"):
            spatial_extent = [float(i) for i in arg.replace('[','').replace(']','').split(',')]
        elif opt in ("-T","--DATE"):
            date_range = arg.replace('[','').replace(']','').replace("'","").split(',')
        elif opt in ("-U","--USER"):
            user = arg
        elif opt in ("-E","--EMAIL"):
            email = arg
        elif opt in ("N","--noDownload"):
            download = False
    
    if download:
        #-- login to earth data and get data
        region_a = ipd.Icesat2Data(short_name, spatial_extent, date_range)
        region_a.earthdata_login(user,email)
        
        #-- put data order
        region_a.order_vars.append(var_list=['count'])
        #-- download data
        region_a.download_granules(ddir)

    #-- Get list of files
    file_list = os.listdir(ddir)
    files = [f for f in file_list if f.endswith('.h5')]

    #-- Loop through files, read specified file, and save histogram as numpy array
    for f in files:
        print(f)
        #-- read specified file
        FILE_NAME = os.path.join(ddir,f)
        fid = h5py.File(FILE_NAME, mode='r')

        #-- determine which beam is the strong beam (left or right)
        if fid['gt1l'].attrs['atlas_beam_type'] == 'strong':
            strong_id = 'l'
        else:
            strong_id = 'r'
            
        #-- loop all three beam pairs and save all three
        for i in range(1,4):
            #-- read count
            count = fid['gt%i%s/residual_histogram/count'%(i,strong_id)][:]
            lat_mean = fid['gt%i%s/residual_histogram/lat_mean'%(i,strong_id)][:]
            lon_mean = fid['gt%i%s/residual_histogram/lon_mean'%(i,strong_id)][:]
            h_li = fid['gt%i%s/land_ice_segments/h_li'%(i,strong_id)][:]
            h_lat = fid['gt%i%s/land_ice_segments/latitude'%(i,strong_id)][:]
            h_lon = fid['gt%i%s/land_ice_segments/longitude'%(i,strong_id)][:]
            
            path_hist = os.path.join(ddir,'hist')
            if not os.path.exists(path_hist):
                os.makedirs(path_hist)
                
            path_lon = os.path.join(ddir,'lon')
            if not os.path.exists(path_lon):
                os.makedirs(path_lon)
                
            path_lat = os.path.join(ddir,'lat')
            if not os.path.exists(path_lat):
                os.makedirs(path_lat)
            
            #-- save numpy arrays
            np.save(os.path.join(path_hist, f.replace('.h5','_hist_gt%i%s.npy'%(i,strong_id))),count)
            np.save(os.path.join(path_lat,f.replace('.h5','_lat_mean_gt%i%s.npy'%(i,strong_id))),lat_mean)
            np.save(os.path.join(path_lon,f.replace('.h5','_lon_mean_gt%i%s.npy'%(i,strong_id))),lon_mean)
            np.save(os.path.join(ddir,f.replace('.h5','_h_li_gt%i%s.npy'%(i,strong_id))),h_li)
            np.save(os.path.join(ddir,f.replace('.h5','_h_lat_gt%i%s.npy'%(i,strong_id))),h_lat)
            np.save(os.path.join(ddir,f.replace('.h5','_h_lon_gt%i%s.npy'%(i,strong_id))),h_lon)

        #-- close hdf5 file
        fid.close()

#-- run main program
if __name__ == '__main__':
    main()

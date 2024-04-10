#-------------------------------------------------------------------------------
# Name:        netcdf_funcs.py
# Purpose:     Functions to create and write to netCDF files and return latitude and longitude indices
# Author:      Mike Martin
# Created:     25/01/2017
# Description: create dimensions: "longitude", "latitude" and "time"
#              create four ECOSSE variables i.e. 'n2o','soc','co2', and 'ch4'
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#!/usr/bin/env python

__prog__ = 'netcdf_funcs.py'
__version__ = '0.0.0'
__author__ = 's03mm5'

import os
import sys
from time import time
import netCDF4 as cdf
from datetime import datetime
import numpy as np
from csv import writer

missing_value = -999.0
sleepTime = 3.5
granularity = 120   # based on HWSD

def getNC_coords(id_, bbox, granularity):

    ll_lon, ll_lat, ur_lon, ur_lat = bbox
    gran_lat, gran_lon, mu_global, fut_clim_scen, soil_num, lu_change = id_

    laty = 90.0 - (float(gran_lat)/granularity)
    lonx = (float(gran_lon)/granularity) - 180.0

    lat_indx = round((laty - ll_lat)*granularity)
    lon_indx = round((lonx - ll_lon)*granularity)

    return list([lat_indx, lon_indx])

def writeNC_set(var_name, ncfile, lat_indx, lon_indx, res):

    # use Python list comprehension to convert res
    # TODO: check length of res
    res_flt_list = [float(sval) for sval in res]
    ncfile.variables[var_name][lat_indx, lon_indx, :] = res_flt_list

    return

def create_netcdf_file(nc_fname_inp, nc_fname_out, metric, data_frame, overwrite_flag):
    """
    create a new NC weather file based on EObs - overwrite starting from December 2000
    """
    func_name =  __prog__ + ' create_netcdf_file'

    season_months = {1:[12,1,2], 2:[3,4,5], 3:[6,7,8], 4:[9,10,11] }
    permitted_seasons = season_months.keys()

    # identify patch
    # ==============
    lat_max = data_frame['latitude'].max()
    lat_min = data_frame['latitude'].min()
    lon_max = data_frame['longitude'].max()
    lon_min = data_frame['longitude'].min()

    # construct new file name for weather
    # ===================================
    if os.path.isfile(nc_fname_out):
        if overwrite_flag:
            try:
                os.remove(nc_fname_out)
                print('Deleted: ' + nc_fname_out)
            except PermissionError as e:
                print(str(e) + ' -could not delete: ' + nc_fname_out)
                return None
        else:
            print(nc_fname_out + ' already exists - cannot continue...')
            return None

    print('\nOpening the ' + metric + ' output NetCDF file ' + nc_fname_out)
    nc_obj_out = cdf.Dataset(nc_fname_out,'w', format='NETCDF4')        # create netCDF4 dataset object

    # output NC file is modelled on EObs
    # ==================================
    print('Opening the ' + metric + ' input NetCDF file ' + nc_fname_inp)
    nc_obj_inp = cdf.Dataset(nc_fname_inp,'r', format='NETCDF4')

    date_str = '31/12/2000'
    day, month, year = date_str.split('/')
    date_obj = datetime(int(year), int(month), int(day), 0, 0)      # TODO: tidy up
    time_var = nc_obj_inp.variables['time']
    date_indx_31_12_2000 = cdf.date2index(date_obj, time_var)

    # copy attributes
    # ===============
    for attr_name in nc_obj_inp.ncattrs():
        nc_obj_out.setncatts({attr_name: nc_obj_inp.getncattr(attr_name)})

    print('Copied attributes ')

    # copy dimensions - lat, long and time
    # ====================================
    for dname in nc_obj_inp.dimensions:
        len_dim = len(nc_obj_inp.dimensions[dname])
        nc_obj_out.createDimension(dname, len_dim)

    print('Created dimensions')

    # copy variables
    # ==============
    for variable in nc_obj_inp.variables:

        if variable == metric:
            continue

        print('\tProcessing var: ' + variable)
        varin = nc_obj_inp.variables[variable]
        var_dims = varin.dimensions
        outVar = nc_obj_out.createVariable(variable, varin.datatype, var_dims)

        # copy variable attributes
        # ========================
        for attr_name in varin.ncattrs():
            outVar.setncatts({attr_name: varin.getncattr(attr_name)})

        outVar[:] = varin[:]

    # identify patch
    # ==============
    lats = nc_obj_out.variables['latitude']
    lons = nc_obj_out.variables['longitude']
    resol = lats[1] - lats[0]
    lat_indx1 = int((lat_min - lats[0])/resol)
    lat_indx2 = int((lat_max - lats[0])/resol)
    lon_indx1 = int((lon_min - lons[0])/resol)
    lon_indx2 = int((lon_max - lons[0])/resol)
    print('Will replace patch with lat indices: {} {}\tlong indices: {} {}'\
                                                            .format(lat_indx1, lat_indx2, lon_indx1, lon_indx2))
    # copy metric variable
    # ====================
    print('\tProcessing var: ' + metric)
    varin = nc_obj_inp.variables[metric]
    var_dims = varin.dimensions
    outVar = nc_obj_out.createVariable(metric, varin.datatype, var_dims)

    # copy variable attributes
    # ========================
    for attr_name in varin.ncattrs():
        outVar.setncatts({attr_name: varin.getncattr(attr_name)})

    # edit metric variable with data frame records
    # ============================================
    trans_var = varin[:, :, :]
    lat_long_pairs = []

    # start date for beginning of data editing - this will be incremented by 3 as season changes
    # ========================================
    date_curr_indx = date_indx_31_12_2000
    num_recs = len(data_frame.values)
    last_season = None
    nspliced = 0
    save_flag = True
    last_time = time()
    for ic, record in enumerate(data_frame.values):
        season, latitude, longitude, date_str, rr_tg, season_diff = record
        if last_season == None:
            last_season = season

        # skip empty rain or temperature value
        # ====================================
        if rr_tg == np.nan:
            continue

        # check season and increment on change
        # ====================================
        if season not in permitted_seasons:
            print('Season error in record {}: {}'.format(ic, record))
            save_flag = False
            break

        if season != last_season:
            date_curr_indx += 3
            last_season = season

        valid_months = season_months[season]

        # validate month
        # ==============
        day, month, year = date_str.split('/')
        month = int(month)
        if month not in valid_months:
            print('Month {} not in valid months {} for season error in record {}: {}'
                  .format(month, valid_months, ic, record))
            save_flag = False
            break

        date_sub_indx = valid_months.index(month)

        lat_indx = int((latitude - lats[0])/resol)
        lon_indx = int((longitude - lons[0])/resol)
        lat_long_pair = [lat_indx, lon_indx]
        if lat_long_pair not in lat_long_pairs:
            lat_long_pairs.append(lat_long_pair)

        try:
            trans_var[date_curr_indx + date_sub_indx, lat_indx, lon_indx] = rr_tg
            nspliced += 1
        except(IndexError) as e:
            print(e)
            save_flag = False
            break


        this_time = time()
        if (this_time - last_time) > sleepTime:
            sys.stdout.flush()
            sys.stdout.write('\rhave spliced {} values, number remaining: {}'.format(nspliced, num_recs - nspliced))
            last_time = this_time

    if save_flag:
        outVar[:, :, :] = trans_var[:, :, :]  # should save on exit
        print('Copied variable ' + metric + ' to ' + nc_fname_out + ' having spliced {} values from {} records'
                                                                                    .format(nspliced, num_recs))
        print('start and end time indices: {} {}'.format(date_indx_31_12_2000, date_curr_indx))

        # write file of lat/longs:
        # ========================
        results_fname = 'E:\\temp\\results.csv'
        if os.path.isfile(results_fname):

            os.remove(results_fname)
            print('Deleted: ' + results_fname)

        # create and write csv file
        # =========================
        print('Creating ' + results_fname + ' - will write {} pairs'.format(len(lat_long_pairs)))
        fpout = open(results_fname, 'w', newline='')
        csv_writer = writer(fpout, delimiter=',')
        output = []
        for lat_long_pair in lat_long_pairs:
            lat_indx, lon_indx = lat_long_pair
            output.append([lats[lat_indx], lons[lon_indx]])
        csv_writer.writerows(output)

    # close netCDF files
    # ==================
    nc_obj_out.sync()
    nc_obj_out.close()
    nc_obj_inp.close()

    print('Exiting ' + func_name)

    return nc_fname_out
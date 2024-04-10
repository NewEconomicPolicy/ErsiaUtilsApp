#-------------------------------------------------------------------------------
# Name:        spec_NCfuncs.py
# Purpose:     Functions to create and write to netCDF files and return latitude and longitude indices
# Author:      Mike Martin
# Created:     25/01/2017
# Description: create dimensions: "longitude", "latitude" and "time"
#              create four ECOSSE variables i.e. 'n2o','soc','co2', and 'ch4'
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#!/usr/bin/env python

__prog__ = 'spec_NCfuncs.py'
__version__ = '0.0.0'
__author__ = 's03mm5'

import os
import sys
import time
import netCDF4 as cdf
import numpy as np
from numpy import arange, full

missing_value = -999.0
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

def create_NCfile(form, summary_varnames):
    """
    #    call this function before running spec against simulation files
    #    output_variables = list(['soc', 'co2', 'ch4', 'n2o'])
    #    for var_name in output_variables[0:1]:
    """
    func_name =  __prog__ + ' create_netcdf_file'

    # set up NC parameters based on contents of first line of the manifest summary file

    sim_dir, study = os.path.split(form.sims_dir)

    fname = study + '_summary_manifest.csv'
    full_fname = os.path.join(sim_dir, fname)
    fut_clim_scen = form.fut_clim_scen

    # read first line of study manifest to retrieive lat/lon extents
    # ==============================================================
    if not os.path.isfile(full_fname):
        print('Function: {}\tstudy manifest file: {} does not exist - cannot proceed'.format(func_name, full_fname))
        return 1

    fmani = open(full_fname, 'r')
    record = fmani.readline()
    fmani.close()

    rec = record.split('\t')
    if len(rec) < 10:
        print('Function: {}\terror in study manifest file: {}\tmust have 10 elements, {} found - cannot proceed'
                                                                        .format(func_name, full_fname, len(rec)))
        return 1

    # push lower left latitude southwards by 0.1 degree to make sure all results are included
    adjustment = 0.1
    dummy, dummy, sll_lat, sll_lon, dummy, dummy,  sur_lat, sur_lon, = rec[0:-2]
    bbox = list([float(sll_lon), float(sll_lat) - adjustment, float(sur_lon), float(sur_lat)])

    # build lat long arrays ilon goes from 0 to 719
    inverse_granularity = 1.0/granularity

    # TODO: might want to consider this....
    # alons = arange(-179.75,180.0,granularity, dtype=np.float32)
    # alats = arange(89.75,-90.0,-granularity, dtype=np.float32)
    alons = arange(bbox[0], bbox[2], inverse_granularity, dtype=np.float32)
    alats = arange(bbox[1], bbox[3], inverse_granularity, dtype=np.float32)
    num_alons = len(alons)
    num_alats = len(alats)

    ll_lon, ll_lat, ur_lon, ur_lat = bbox

    gur_lat = round((90.0 - ur_lat)*granularity)
    gll_lat = round((90.0 - ll_lat)*granularity)

    gur_lon = round((180.0 + ur_lon)*granularity)
    gll_lon = round((180.0 + ll_lon)*granularity)

    gran_alons = arange(gll_lon, gur_lon)
    gran_alats = arange(gll_lat, gur_lat)
    num_gran_alats = len(gran_alats)
    num_gran_alons = len(gran_alons)

    # generate mu_globals
    sys.stdout.write('Number of rows: {}/{} and columns: {}/{}\n'.
                     format(num_alats, num_gran_alats, num_alons, num_gran_alons))
    sys.stdout.flush()

    years = arange(form.fut_start_year, form.fut_end_year + 1)
    nmnths = 12
    nyears = len(years)
    num_mnths = nyears*nmnths       # expect 1140 for 95 years
    atimes = arange(num_mnths)

    # construct the output file name and delete if it already exists
    var_names = summary_varnames.keys()
    out_dir =   form.outdir

    fout_name = os.path.join(out_dir, study + '.nc')
    # NC file already exists
    if os.path.isfile(fout_name):
        try:
            os.remove(fout_name)
            print('Deleted file: ' + fout_name)
        except PermissionError:
            print('Function: {}\tcould not delete file: {}'.format(func_name, fout_name))
            return 1

    # call the Dataset constructor to create file
    ncfile = cdf.Dataset(fout_name,'w', format='NETCDF4')

    # create global attributes for this dataset TODO: make meaningful
    ncfile.history = study + ' consisting of ' + study + ' study'
    date_stamp = time.strftime('%H:%M %d-%m-%Y')
    ncfile.attributation = 'Created at ' + date_stamp + ' from Spatial Ecosse '
    ncfile.future_climate_scenario = fut_clim_scen
    ncfile.land_use_change = form.land_use
    data_used = 'Data used: HWSD soil, '
    if fut_clim_scen == 'CORDEX':
        data_used += '{} past weather and {} future climate'.format(fut_clim_scen,fut_clim_scen)
    else:
        data_used += 'CRU past weather and CRU future climate, scenario: {} '.format(fut_clim_scen)
    ncfile.dataUsed = data_used

    # we create the dimensions using the createDimension method of a Group (or Dataset) instance
    ncfile.createDimension('lat', num_alats)
    ncfile.createDimension('lon', num_alons)
    ncfile.createDimension('time', num_mnths)

    # create the variable (4 byte float in this case)
    # to create a netCDF variable, use the createVariable method of a Dataset (or Group) instance.
    # first argument is name of the variable, second is datatype, third is a tuple with the name (s) of the dimension(s).
    # lats = ncfile.createVariable('latitude',dtype('float32').char,('lat',))
    #
    lats = ncfile.createVariable('latitude','f4',('lat',))
    lats.units = 'degrees of latitude North to South in 30 arc seconds steps'
    lats.long_name = 'latitude'
    lats[:] = alats

    lons = ncfile.createVariable('longitude','f4',('lon',))
    lons.units = 'degrees of longitude West to East in 30 arc seconds steps'
    lons.long_name = 'longitude'
    lons[:] = alons

    # TODO: check these
    times = ncfile.createVariable('time','i2',('time',))
    times.units = 'months from January {} - {} years'.format(form.fut_start_year, nyears)
    times[:] = atimes

    # feedback initialisation
    t1 = time.time()

    # create the metrics and assign default data
    for var_name in var_names:
        var_varia = ncfile.createVariable(var_name,'f4',('lat','lon','time'),fill_value = -999.0)
        var_varia.units = 'kg/ha'
        var_varia.missing_value = missing_value

    # close netCDF file
    ncfile.sync()
    ncfile.close()
    form.lgr.info('Closed {0} netCDF file'.format(fout_name))
    form.granularity = granularity
    form.bbox = bbox

    return fout_name
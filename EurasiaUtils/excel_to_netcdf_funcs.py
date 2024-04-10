"""
#-------------------------------------------------------------------------------
# Name:         spec_post_process_nc.py
# Purpose:      post process spatial simulation results from SUMMARY.OUT files generated by the
#               Spatial Parallel ECosse Simulator
# Author:      Mike Martin
# Created:     25/01/2017
# Licence:     <your licence>
# Description: data is aggregated into NetCDF files
#-------------------------------------------------------------------------------
"""

__prog__ = 'spec_post_process_nc.py'
__version__ = '1.0.1'

# Version history
# ---------------
# 1.0.1

from glob import glob
from csv import writer
import os
import time
from xlrd import open_workbook, xldate
import netCDF4 as cdf
from netcdf_funcs import create_netcdf_file, writeNC_set, getNC_coords
from pandas import read_csv
from numpy import int32, float64

csv_headers = list(['season', 'latitude', 'longitude', 'date', 'rr_tg', 'seasdif'])
metric_dict = {'Tg':'tg', 'Precip': 'rr'}

def convert_csv_file(form):

    '''
    read Csv file and create NetCDF based on EObs data
    NB the presumption is that the data set is pre-sorted
        in case this changes then: data_frame = data_frame.sort_values(by=["latitude","longitude",'date'])
    '''
    excel_fname = form.w_lbl05.text()
    if not os.path.isfile(excel_fname):
        print('Excel file ' + excel_fname + ' does not exist')
        return

    # look for CSV file saved from Excel file
    # =======================================
    datasets_dir, short_fname = os.path.split(excel_fname)
    root_fname, exten = os.path.splitext(excel_fname)
    csv_fnames = glob( os.path.normpath(root_fname + '.csv') )
    if len(csv_fnames)  == 0:
        print('No derived csv file in ' + datasets_dir)
        return

    metric_name = root_fname.split('_')[-1]
    if metric_name not in metric_dict:
        print('Metric name ' + metric_name + ' not recognised - must be one of ' + str(metric_dict.keys()) )
        return

    metric = metric_dict[metric_name]

    # EObs must exist
    # ===============
    eobs_nc_fnames = glob(form.eobs_dir + '/' + metric + '*0Monthly.nc')
    if len(eobs_nc_fnames) == 0:
        print('No EObs file in ' + form.eobs_dir)
        return

    csv_fname = csv_fnames[0]
    print('Reading csv file ' + csv_fname + ' using pandas')

     # read the CSV file
    # ==================
    data_frame = read_csv(csv_fname, sep = ',', names = csv_headers, skiprows = 1)

    # create and write NetCDF file
    # ============================
    datasets_dir, short_fname = os.path.split(excel_fname)
    root_name = os.path.splitext(short_fname)[0] + '.nc'
    nc_fname_mod = os.path.normpath(os.path.join(datasets_dir, root_name))
    print('Creating ' + nc_fname_mod + '...')

    nc_fname_out = create_netcdf_file(eobs_nc_fnames[0], nc_fname_mod, metric, data_frame, overwrite_flag = True)

    return nc_fname_out

def convert_excel_file(form, overwrite_flag = True):
    '''
    read Excel file and write CSV file after filtering out all lines earlier than December 2000
    '''

    columns = {'A': 'latitude', 'B':  'longitude', 'C': 'date_time', 'D': 'year', 'E': 'season', 'F': 'tg', \
                                                                                                    'G': 'seasdif'}
    excel_fname = form.w_lbl05.text()
    if not os.path.isfile(excel_fname):
        print('Excel file ' + excel_fname + ' does not exist')
        return

    # construct new CSV file name for weather
    # ===================================
    datasets_dir, short_fname = os.path.split(excel_fname)
    root_name = os.path.splitext(short_fname)[0] + '_filtered.csv'
    csv_fname = os.path.normpath(os.path.join(datasets_dir, root_name))

    if os.path.isfile(csv_fname):
        if overwrite_flag:
            try:
                os.remove(csv_fname)
                print('Deleted: ' + csv_fname)
            except PermissionError as e:
                print(str(e) + ' -could not delete: ' + csv_fname)
                return None
        else:
            print(csv_fname + ' already exists - cannot continue...')
            return None

    print('Reading Excel file ' + excel_fname + ' - this may take several minutes...')
    try:
        work_book = open_workbook(excel_fname)
    except () as err:
        print('Exception {}'.format(err))
        return -1

    # create and write csv file
    # =========================
    print('Creating ' + csv_fname + '...')
    fpout = open(csv_fname, 'w', newline='')
    csv_writer = writer(fpout, delimiter=',')
    output = []
    output.append(csv_headers)

    # print number of sheets and some names
    nshts = work_book.nsheets
    sheet = work_book.sheet_by_index(0)

    # read column slices - data_set is a dictionary comprising lists of cells
    # ==================
    data_set = {}
    for col_num, col_name in enumerate(columns):
        # data_set[col_name] = sheet.col_slice(colx = col_num, start_rowx=1, end_rowx=100)
        data_set[columns[col_name]] = sheet.col_slice(colx = col_num, start_rowx=1)

    nrows = len(data_set['latitude'])
    print('Identified {} rows of data in Excel file'.format(nrows))

    # step through each row
    # identify unique lats and longs, discard rows before and including 2000, otherwise add to output list
    # =====================

    lat_list = []
    lon_list = []
    nbad_tg = 0; nbad_season = 0; nbad_year = 0
    for rownum in range(nrows):

        # date and time
        # =============
        date_time_cell = data_set['date_time'][rownum]
        if date_time_cell.ctype == 3:
            excel_date_time = date_time_cell.value
            # Convert an Excel date/time number into a datetime.datetime o
            # datemode – 0: 1900-based, 1: 1904-based
            date_obj = xldate.xldate_as_datetime(excel_date_time, datemode = 0)
            # skip these years
            # ================
            if date_obj.year <= 2000:
                continue
        else:
            print('Bad date time on row {}'.format(rownum))
            continue

        # lats and longs are numbers
        # ==========================
        lat_cell = data_set['latitude'][rownum]
        if lat_cell.ctype == 2:
            latitude = lat_cell.value
            if latitude not in lat_list:
                lat_list.append(latitude)

        lon_cell = data_set['longitude'][rownum]
        if lon_cell.ctype == 2:
            longitude = lon_cell.value
            if longitude not in lat_list:
                lon_list.append(longitude)

        # season is text and should be 1, 2, 3 or 4
        # =========================================
        season_cell = data_set['season'][rownum]
        if season_cell.ctype == 1:
            season = int(season_cell.value)
        else:
            nbad_season += 1

        # season difference is real number
        # ================================
        seasdif_cell = data_set['seasdif'][rownum]
        if seasdif_cell.ctype == 2:
            season_diff = seasdif_cell.value
        else:
            print('Bad season difference on row {}'.format(rownum))
            continue

        # tg is real number
        # =================
        tg_cell = data_set['tg'][rownum]
        if tg_cell.ctype == 2:
            tg = tg_cell.value
        else:
            nbad_tg += 1
            tg = None
            continue

        # year is real number
        year_cell = data_set['year'][rownum]
        if year_cell.ctype == 2:
            year_diff = year_cell.value
        else:
            nbad_year += 1
            continue

        # append
        output.append([season, date_obj.date(), latitude, longitude, season_diff, tg])
        nvals = len(output)
        if int((nvals/1000))*1000 == nvals:
            print('have generated {} values'.format(nvals))

    print('Number of bad tgs: {}\tseasons: {}\tyears: {}'.format(nbad_tg, nbad_season, nbad_year))
    csv_writer.writerows(output)
    fpout.close()

    return

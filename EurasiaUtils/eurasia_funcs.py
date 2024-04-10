"""
#-------------------------------------------------------------------------------
# Name:
# Purpose:     consist of high level functions invoked by main GUI
# Author:      Mike Martin
# Created:     11/12/2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#
"""
__prog__ = 'eurasia_funcs.py'
__version__ = '0.0.1'
__author__ = 's03mm5'

import os
import csv
import subprocess
from sbs_misc_utils import fetch_granular_lat_lons
import time
from unidecode import unidecode
from glob import glob

max_run_records_read = 400000
wetland_lus = [1, 5, 7, 11, 17, 22, 24, 28, 29]
MISSING = -9999
MAX_SOIL_TYPE = 8
MAX_LANDUSE = 35

def _reformat_modis_files(dirname):

    decompressor = 'C:\\Program Files\\7-Zip\\7z.exe'
    if not os.path.isfile(decompressor):
        print('Decompression executable ' + decompressor + ' must exist')
        return

    out_dir, dummy = os.path.split(dirname)
    flist = glob(dirname + '\\*.gz')
    for gz_fname in flist:
        fname, extens = os.path.splitext(gz_fname)
        dummy, file_name = os.path.split(fname)
        asc_fname = os.path.join(out_dir, file_name)
        if not os.path.isfile(asc_fname):
            output = subprocess.check_output([decompressor,'x','-o' + out_dir, gz_fname])
        else:
            # check number of lines
            pass

    return

def _create_codes_table(form):
    """
    Read Daycent run file and extract Code_CindyPotsdam and CountryName fields then write these to a CSV
                                                           file comprising country names and codes
    """
    func_name =  __prog__ + '\t _create_codes_table'

    # file to be created
    # ==================
    results_fname = os.path.join(form.country_codes,'country_codes_Potsdam.csv')
    if os.path.isfile(results_fname):
        os.remove(results_fname)
        print('removed country_codes file: ' + results_fname)

    # open and extract codes from the run file
    # =======================================
    run_fname = form.run_fname
    if not os.path.isfile(run_fname):
        print('File ' + run_fname + 'does not exist')
        return

    finp_run = open(form.run_fname, 'r')
    finp_run_reader = csv.reader(finp_run)
    header_row = next(finp_run_reader) # skip header

    # Read one line at at time
    # ========================
    n_china = 0
    n_undefined = 0
    nread = 0
    country_dict = {}
    for row in finp_run_reader:
        nread += 1
        globalID = row[0]
        latitude = float(row[1])
        longitude = float(row[2])
        landuse = int(row[3])    # landuse
        soiltype = int(row[4])

        # skip China
        if row[6] == 'China':
            n_china += 1
            continue

        # report only
        if not row[5].isnumeric():
            n_undefined += 1
            continue
        else:
            country_id = int(row[5])

        country = row[6]
        if country not in country_dict.keys():
            country_dict[country] = country_id

    finp_run.close()

    # write dictionary to CSV file
    # ============================
    res_obj = open(results_fname, 'w', newline='')
    for country in sorted(country_dict.keys()):
        res_obj.write('{},{}\n'.format(country,country_dict[country]))
    res_obj.close()

    print('File inspection completed, wrote {} country codes to {}\n\tnumber of China records: {}\tcountry undefined: {}'
          .format(len(country_dict), results_fname, n_china, n_undefined))

    return

def _generate_country_shape_files(form):
    """
    Main loop for generating outputs:
    """
    func_name =  __prog__ + '\t _generate_country_shape_files'

    # read codes and country names for whole world
    # ============================================
    country_codes_IS0_3166_fname = os.path.join(form.country_codes,'country_codes_IS0_3166.csv')
    fread_obj = open(country_codes_IS0_3166_fname, 'r')
    lines = fread_obj.readlines()
    fread_obj.close()

    # build dictionary with 3 letter code as key
    # ==========================================
    country_code_dict = {}
    country_code_dict_additional = {}
    for line in lines:
        line_list = line.split(',')
        country_code, country_name = line_list[0:2]
        country_tmp = unidecode(country_name.rstrip('\n'))
        country = country_tmp.strip('"').replace(' ','_')
        if country == 'A...land_Islands':
            country = 'Aland_Islands'
        country_code_dict[country_code] = country
        if len(line_list) > 2:
            more = str(line_list[2:])
            country_code_dict_additional[country_code] = more

    # add two more...
    country_code_dict['XKO'] = 'Kosovo'
    country_code_dict['XNC'] = 'Northern_Cyprus'

    # get the zip files
    # =================
    n_countries = 0
    flist = glob(form.country_zips + '\\*.zip')
    for zip_fname in flist:
        fname, extens = os.path.splitext(zip_fname)
        dummy, file_name = os.path.split(fname)
        country_code = file_name[0:3]    # first three letters
        if country_code in country_code_dict.keys():
            country = country_code_dict[country_code]
            out_dir = form.shp_dir + '\\' + country

            # check that directory exists but if not then create it
            if os.path.isdir(out_dir):
                flist = glob(out_dir + '\\*.shp')
                nshapes = len(flist)
                if nshapes > 0:
                    print('{} shape files already exist in {} - nothing to do....'.format(nshapes, out_dir ))
                    continue
            else:
                os.mkdir(out_dir)

            print('Unpacking country code: {}\tcountry: {}'.format(country_code, country))
            output = subprocess.check_output([form.decompressor,'x','-y','-o' + out_dir, zip_fname])
            n_countries += 1
        else:
            print('Country code: {} not in country codes'.format(country_code))

    print('Finished unpacking {} countries...'.format(n_countries))


    return


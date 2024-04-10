"""
#-------------------------------------------------------------------------------
# Name:        initialise_funcs.py
# Purpose:     script to read read and write the setup and configuration files
# Author:      Mike Martin
# Created:     31/07/2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------
"""

__prog__ = 'initialise_funcs.py'
__version__ = '0.0.0'

# Version history
# ---------------
# 
from os.path import isdir, join, exists, isfile, normpath
from os import makedirs, getcwd
from json import load as json_load, dump as json_dump
from time import sleep

from set_up_logging import set_up_logging

sleepTime = 5
APPLIC_STR = 'eurasia_utils'
ERROR_STR = '*** Error *** '
STTNGS_LIST = ['fname_png', 'results_dir', 'root_dir', 'glec_data_dir', 'shp_dir', 'new_shp_dir', 'log_dir', 'hwsd_dir']

def initiation(form):
    """
    this function is called to initiate the programme to process non-GUI settings.
    """
    form.settings = _read_setup_file(form)  # retrieve settings
    set_up_logging(form, APPLIC_STR, lggr_flag=True)
    form.settings['config_file'] = normpath(form.settings['config_dir'] + '/' + APPLIC_STR + '_config.json')

    stage_dir = form.settings['results_dir'] + '\\stage'
    if not isdir(stage_dir):
        makedirs(stage_dir)
    form.settings['stage_dir'] = stage_dir
    form.settings['run_fname'] = ''

    return

def _read_setup_file(form, gui_flag=False):
    """
    read settings used for programme from the setup file, if it exists,
    or create setup file using default values if file does not exist
    """
    setup_file = join(getcwd(), 'eurasia_setup.txt')
    if exists(setup_file):
        try:
            with open(setup_file, 'r') as fsetup:
                settings = json_load(fsetup)
        except (OSError, IOError) as err:
            print(err)
            return False
    else:
        settings = _write_default_setup_file(setup_file)

    for key in settings:
        if key not in STTNGS_LIST:
            print(ERROR_STR + 'attribute {} required in settings file {}'.format(key, setup_file))
            sleep(sleepTime)
            exit(0)

    # set defaults
    # ============
    settings['config_dir'] = getcwd()
    settings['shpe_fname'] = ''
    settings['country_codes'] = settings['root_dir'] + '\\Country_codes'
    settings['country_zips'] = settings['root_dir'] + '\\Country_zips'

    # zipper
    decompressor = 'C:\\Program Files\\7-Zip\\7z.exe'
    if isfile(decompressor):
        form.decompressor = decompressor
    else:
        print('Decompression executable ' + decompressor + ' must exist')
        return False

    settings['excel_fname'] = ''
    settings['setup_file'] = setup_file
    glec_data_dir = ''
    settings['glec_data_dir'] = glec_data_dir
    settings['eobs_dir'] = normpath(glec_data_dir + '\\EObs_v17\\Monthly')

    return settings


def _write_default_setup_file(setup_file):
    """
    #  stanza if setup_file needs to be created
    """
    cw_dir = getcwd()
    root_dirE = 'E:\\Dagmar\\'
    root_dirC = 'C:\\'

    _default_setup = {
        'fname_png': join(cw_dir + '\\Images', 'World.PNG'),
        'results_dir': root_dirE + 'DayCent\\Results',
        'shp_dir': root_dirC + 'Astley\\CountryShapefiles',
        'glec_data_dir': root_dirE + 'GlobalEcosseData\\',
        'new_shp_dir': root_dirE + 'CountryFilesNew',
        'root_dir': root_dirE
    }
    # if setup file does not exist then create it...
    with open(setup_file, 'w') as fsetup:
        json_dump(_default_setup, fsetup, indent=2, sort_keys=True)
        return _default_setup

def write_config_file(form):
    """
    # write current selections to config file
    """
    #
    config_json = {
        'run_csv_fname': form.w_lbl07.text(),
        'excel_csv_fname': form.w_lbl05.text()
    }
    with open(form.settings['config_file'], 'w') as fsetup:
        json_dump(config_json, fsetup, indent=2, sort_keys=True)

import os

def remove_file(lgr, fname):
    """
    write kml consisting of mu_global and soil details
    """
    if os.path.isfile(fname):
        try:
            os.remove(fname)
            lgr.info('removed weather file: ' + fname)
        except (OSError, IOError) as e:
            print('Failed to remove file: {0}'.format(e))
            return -1
    return 0

def fetch_granular_lat_lons(latitude, longitude, granularity = 120):
    """
    create study summary file and write first line
    """
    granularity = 120

    gran_lon = round((180.0 + longitude)*granularity)
    gran_lat = round((90.0 - latitude)*granularity)

    return gran_lat, gran_lon
		
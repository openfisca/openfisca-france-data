#! /usr/bin/env python

import argparse
import logging
import sys


from openfisca_france_data.erfs_fpr.input_data_builder import build

log = logging.getLogger(__name__)


def main(year = None, survey = None):
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--collection',
         help = "name of collection to build or update (erfs or erfs_fpr)", required = True)
    parser.add_argument('-d', '--replace-data', action = 'store_true', default = False,
        help = "erase existing survey data HDF5 file (instead of failing when HDF5 file already exists)")
    parser.add_argument('-s', '--survey', help = 'name of survey to build or update', required = True)
    parser.add_argument('-v', '--verbose', action = 'store_true', default = False, help = "increase output verbosity")
    args = parser.parse_args()
    logging.basicConfig(level = logging.DEBUG if args.verbose else logging.WARNING, stream = sys.stdout)

 

    pass

if __name__ == '__main__':
    import time
    start = time.time()
    logging.basicConfig(level = logging.INFO, filename = 'run_all.log', filemode = 'w')
    build(year = 2012, check = False)
    log.info("Script finished after {}".format(time.time() - start))
    print(time.time() - start)

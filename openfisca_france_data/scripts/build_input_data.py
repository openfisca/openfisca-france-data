#! /usr/bin/env python

import argparse
import logging
import time
import sys

from openfisca_france_data.erfs.input_data_builder import build as build_erfs
from openfisca_france_data.erfs_fpr.input_data_builder import build as build_erfs_fpr

log = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--collection',
         help = "name of collection to build or update (erfs or erfs_fpr)", required = True)
    parser.add_argument('-d', '--replace-data', action = 'store_true', default = False,
        help = "erase existing survey data HDF5 file (instead of failing when HDF5 file already exists)")
    parser.add_argument('-s', '--survey', help = 'name of survey (year) to build or update', required = True)
    parser.add_argument('-v', '--verbose', action = 'store_true', default = False, help = "increase output verbosity")
    args = parser.parse_args()
    logging.basicConfig(level = logging.DEBUG if args.verbose else logging.WARNING, stream = sys.stdout)
    year = int(args.survey)
    start = time.time()
    if args.collection == 'erfs_fpr':
        build_erfs_fpr(year = year, check = False)
    elif args.collection == 'erfs':
        build_erfs(year = year, check = False)

    log.info("Build lasted {}".format(time.time() - start))


if __name__ == '__main__':
    sys.exit(main())

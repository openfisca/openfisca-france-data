# -*- coding: utf-8 -*-


# OpenFisca -- A versatile microsimulation software
# By: OpenFisca Team <contact@openfisca.fr>
#
# Copyright (C) 2011, 2012, 2013, 2014, 2015 OpenFisca Team
# https://github.com/openfisca
#
# This file is part of OpenFisca.
#
# OpenFisca is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# OpenFisca is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import os
import logging

from ConfigParser import SafeConfigParser
from pandas import HDFStore
import pkg_resources

log = logging.getLogger(__name__)


openfisca_france_location = pkg_resources.get_distribution('openfisca-france-data').location
default_config_files_directory = os.path.join(openfisca_france_location)


def get_tmp_file_path(config_files_directory = default_config_files_directory):
    parser = SafeConfigParser()
    config_local_ini = os.path.join(config_files_directory, 'config_local.ini')
    config_ini = os.path.join(config_files_directory, 'config.ini')
    _ = parser.read([config_ini, config_local_ini])
    tmp_directory = parser.get('data', 'tmp_directory')
    hdf_file_path = os.path.join(tmp_directory, 'temp.h5')
    return hdf_file_path


def load_temp(name = None, year = None, variables = None, config_files_directory = default_config_files_directory):
    """
    Load a temporary saved table

    Parameters
    ----------
    name : string, default None

    year : integer, default None
           year of the data
    """
    if year is None:
        raise Exception("year is needed")
    if name is None:
        raise Exception("name is needed")
    hdf_file_path = get_tmp_file_path(config_files_directory = config_files_directory)
    print(hdf_file_path)
    store = HDFStore(hdf_file_path)
    dataframe = store["{}/{}".format(year, name)]
    store.close()
    if variables is None:
        return dataframe
    else:
        return dataframe[variables].copy()


def save_temp(dataframe, name = None, year = None, config_files_directory = default_config_files_directory):
    """
    Save a temporary table

    Parameters
    ----------
    dataframe : pandas DataFrame
                the dataframe to save
    name : string, default None

    year : integer, default None
           year of the data
    """
    if year is None:
        raise Exception("year is needed")
    if name is None:
        raise Exception("name is needed")
    hdf_file_path = get_tmp_file_path(config_files_directory = config_files_directory)
    store = HDFStore(hdf_file_path)
    log.info("{}".format(store))
    store_path = "{}/{}".format(year, name)

    if store_path in store.keys():
        del store["{}/{}".format(year, name)]

    dataframe.to_hdf(hdf_file_path, store_path)

    store.close()
    return True


def show_temp(config_files_directory = default_config_files_directory):

    hdf_file_path = get_tmp_file_path(config_files_directory = config_files_directory)
    store = HDFStore(hdf_file_path)

    log.info("{}".format(store))
    store.close()

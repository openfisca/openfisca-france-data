# -*- coding:utf-8 -*-
# Created on 16 mai 2013
# This file is part of OpenFisca.
# OpenFisca is a socio-fiscal microsimulation software
# Copyright ©2013 Clément Schaff, Mahdi Ben Jelloul
# Licensed under the terms of the GVPLv3 or later license
# (see openfisca/__init__.py for details)

import gc
import os


from ConfigParser import SafeConfigParser
from pandas import HDFStore
import pkg_resources

openfisca_france_location = pkg_resources.get_distribution('openfisca-france-data').location
default_config_files_directory = os.path.join(openfisca_france_location)

def get_tmp_file_path(config_files_directory = default_config_files_directory):
    parser = SafeConfigParser()
    config_local_ini = os.path.join(config_files_directory, 'config_local.ini')
    config_ini = os.path.join(config_files_directory, 'config.ini')
    found = parser.read([config_ini, config_local_ini])
    tmp_directory = parser.get('data', 'tmp_directory')
    hdf_file_path = os.path.join(tmp_directory,'temp.h5')
    return hdf_file_path

def load_temp(name = None, year = None):
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
    hdf_file_path = get_tmp_file_path()
    print hdf_file_path
    store = HDFStore(hdf_file_path)
    dataframe = store[str(year)+"/"+name]
    store.close()
    return dataframe


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
    hdf_file_path = get_tmp_file_path()
    store = HDFStore(hdf_file_path)
    print store
    store_path = "{}/{}".format(year, name)

    if store_path in store.keys():
        del store[str(year)+"/"+name]

    dataframe.to_hdf(hdf_file_path, store_path)

    store.close()
    return True


def show_temp():
    store = HDFStore(os.path.join(ERF_HDF5_DATA_DIR,'temp.h5'))
    print store
    store.close()

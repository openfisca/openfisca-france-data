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


def save_temp(dataframe, name=None, year=None):
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

    parser = SafeConfigParser()
    config_local_ini = os.path.join(config_files_directory, 'config_local.ini')
    config_ini = os.path.join(config_files_directory, 'config.ini')
    found = parser.read([config_local_ini, config_ini])
    input_data_directory = parser.get('data', 'input_directory')


    store = HDFStore(os.path.join(ERF_HDF5_DATA_DIR,'temp.h5'))
    if str(year)+"/"+name in store.keys():
        del store[str(year)+"/"+name]
    store[str(year)+"/"+name] = dataframe
    store.close()
    return True

def load_temp(name=None, year=None):
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
    store = HDFStore(os.path.join(ERF_HDF5_DATA_DIR,'temp.h5'))
    dataframe = store[str(year)+"/"+name]
    store.close()
    return dataframe


def show_temp():
    store = HDFStore(os.path.join(ERF_HDF5_DATA_DIR,'temp.h5'))
    print store
    store.close()

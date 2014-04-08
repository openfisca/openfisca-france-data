# -*- coding:utf-8 -*-
# Created on 7 avr. 2013
# This file is part of OpenFisca.
# OpenFisca is a socio-fiscal microsimulation software
# Copyright © #2013 Clément Schaff, Mahdi Ben Jelloul
# Licensed under the terms of the GVPLv3 or later license
# (see openfisca/__init__.py for details)

import gc
import os
import pkg_resources
import sys

from ConfigParser import SafeConfigParser
import logging
from pandas import HDFStore, DataFrame

from openfisca_france.utils import check_consistency
#    Uses rpy2.
#    On MS Windows, The environment variable R_HOME and R_USER should be set
import pandas.rpy.common as com
import rpy2.rpy_classic as rpy


rpy.set_default_mode(rpy.NO_CONVERSION)
openfisca_france_location = pkg_resources.get_distribution('openfisca-france-data').location
CONFIG_DIR = os.path.join(openfisca_france_location)


class Survey(object):
    label = None
    name = None
    tables = None
    hdf5_filename = None
    """
    An object to describe survey data
    """
    def __init__(self, name = None, label = None, hdf5_filename = None, **kwargs):

        assert name is not None, "A survey should have a name"
        self.name = name
        self.tables = dict()

        if label is not None:
            self.label = label
        else:
            self.label = self.name


        if hdf5_filename is not None:
            self.hdf5_filename = hdf5_filename
        else:
            self.hdf5_filename = "{}{}".format(self.name, ".h5")

        self.informations = kwargs


    def insert_table(self, name = None, **kwargs):
        """
        Insert a table in the Survey
        """
        if name not in self.tables.keys():
            self.tables[name] = dict()

        for key, val in kwargs.iteritems():
        ##    if key in ["Rdata_filename", "variables"]:
            self.tables[name][key] = val

    def fill_hdf_from_Rdata(self, table, verbose = False):

        assert table in self.tables, "Table {} is not a repertorid table".format(table)
        Rdata_table = self.tables[table]["Rdata_table"]
        Rdata_file = self.tables[table]["Rdata_file"]

        if not os.path.isfile(Rdata_file):
             raise Exception("filename do  not exists")

        rpy.r.load(Rdata_file)
        stored_table = com.load_data(Rdata_table)
        store_path = Rdata_table
        store = HDFStore(self.hdf5_filename)

        print 'store : ', store
        print 'store_path : ', store_path

        ## force_recreation = True
        ## if store_path in store:
        ##     if force_recreation is not True:
        ##         print store_path + "already exists, do not re-create and exit"
        ##         store.close()
        ##         return

        variables = self.tables[table]['variables']
        if variables is not None:
            print 'variables : ', variables
            variables_stored = list(set(variables).intersection(set(stored_table.columns)))
            print list(set(variables).difference((set(stored_table.columns))))
            store.append(store_path, stored_table[variables_stored], format = 'table', data_columns = stored_table.columns)
        else:
             store.append(store_path, stored_table, format = 'table', data_columns = stored_table.columns)

        store.close()
        gc.collect()


class SurveyCollection(object):
    """
    A collection of Surveys
    """
    def __init__(self):

        super(SurveyCollection, self).__init__()
        self.surveys = dict()


def build_erfs_survey_collection():

    parser = SafeConfigParser()
    config_local_ini = os.path.join(CONFIG_DIR, 'config_local.ini')
    config_ini = os.path.join(CONFIG_DIR, 'config.ini')
    found = parser.read([config_local_ini, config_ini])
    data_directory = parser.get('data', 'input_directory')

    erfs_survey_collection = SurveyCollection()
    for year in range(2008, 2010):
        surveys = erfs_survey_collection.surveys
        yr = str(year)[2:]
        yr1 = str(year+1)[2:]

        eec_variables = ['noi','noicon','noindiv','noiper','noimer','ident','naia','naim','lien',
                       'acteu','stc','contra','titc','mrec','forter','rstg','retrai','lpr','cohab','sexe',
                       'agepr','rga','statut', 'txtppb', 'encadr', 'prosa', 'nbsala',  'chpub', 'dip11']
        eec_rsa_variables = [ "sp0" + str(i) for i in range(0,10)] + ["sp10", "sp11"] + ['sitant', 'adeben',
                            'datant', 'raistp', 'amois', 'adfdap' , 'ancentr', 'ancchom', 'dimtyp', 'rabsp', 'raistp',
                             'rdem', 'ancinatm']
        eec_aah_variables = ["rc1rev", "maahe"]
        eec_variables += eec_rsa_variables + eec_aah_variables

        erf_tables = {
            "erf_menage" : {
                "Rdata_table" : "menage" + yr,
                "year" : year,
                "variables" : None,
                },
            "eec_menage" : {
                "Rdata_table" : "mrf" + yr + "e" + yr + "t4",
                "year" : year,
                "variables" : None,
                },
            "foyer" : {
                "Rdata_table" : "foyer" + yr,
                "year" : year,
                "variables" : None,
                },
            "erf_indivi" : {
                "Rdata_table" : "indivi" + yr,
                "year" : year,
                "variables" : ['noi','noindiv','ident','declar1','quelfic','persfip','declar2','persfipd','wprm',
                     "zsali","zchoi","ztsai","zreti","zperi","zrsti","zalri","zrtoi","zragi","zrici","zrnci",
                     "zsalo","zchoo","ztsao","zreto","zpero","zrsto","zalro","zrtoo","zrago","zrico","zrnco",
                     ],
                },
            "eec_indivi" : {
                "Rdata_table" : "irf" + yr + "e" + yr + "t4",
                "year" : year,
                "variables" : eec_variables,
                },
            "eec_cmp_1" : {
                "Rdata_table" : "icomprf" + yr + "e" + yr1 + "t1",
                "year" : year,
                "variables" : eec_variables,
                },
            "eec_cmp_2" : {
                "Rdata_table" : "icomprf" + yr + "e" + yr1 + "t2",
                "year" : year,
                "variables" : eec_variables,
                },
            "eec_cmp_3" : {
                "Rdata_table" : "icomprf" + yr + "e" + yr1 + "t3",
                "year" : year,
                "variables" : eec_variables,
                },
        }

        # Build absolute path for Rdata_file
        for table in erf_tables.values():
            table["Rdata_file"] = os.path.join(os.path.dirname(data_directory),
                                                   'R',
                                                   'erf',
                                                   str(year),
                                                   table["Rdata_table"] + str(".Rdata"),
                                                   )
        survey_name = 'erfs_' + str(year)
        hdf5_filename = os.path.join(os.path.dirname(data_directory),
                                     'test',
                                     "{}{}".format(survey_name, ".h5")
                                     )
        survey = Survey(name = survey_name, hdf5_filename = hdf5_filename)
        surveys[survey_name] = survey
        for table_name, table_args in erf_tables.iteritems():
            survey.insert_table(name = table_name, **table_args)
            survey.fill_hdf_from_Rdata(table_name)


if __name__ == '__main__':

    build_erfs_survey_collection()

#
#     hdf5_filename = os.path.join(os.path.dirname(ERF_HDF5_DATA_DIR),'erf','erf_old.h5')
#     print hdf5_filename
#     store = HDFStore(hdf5_filename)
#     print store

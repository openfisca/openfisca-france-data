#! /usr/bin/env python
# -*- coding: utf-8 -*-


# OpenFisca -- A versatile microsimulation software
# By: OpenFisca Team <contact@openfisca.fr>
#
# Copyright (C) 2011, 2012, 2013, 2014 OpenFisca Team
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
#

TODO: test configuration and dump load of Surveys/SurveyCollections

import collections
import gc
import json
import os
import pkg_resources

from ConfigParser import SafeConfigParser
import logging
from pandas import HDFStore

from openfisca_france.utils import check_consistency
#    Uses rpy2.
#    On MS Windows, The environment variable R_HOME and R_USER should be set
import pandas.rpy.common as com
import rpy2.rpy_classic as rpy


rpy.set_default_mode(rpy.NO_CONVERSION)

openfisca_france_location = pkg_resources.get_distribution('openfisca-france-data').location
default_config_files_directory = os.path.join(openfisca_france_location)

log = logging.getLogger(__name__)


class Survey(object):
    hdf5_file_path = None
    label = None
    name = None
    tables = None
    """
    An object to describe survey data
    """
    def __init__(self, name = None, label = None, hdf5_file_path = None, **kwargs):

        assert name is not None, "A survey should have a name"
        self.name = name
        self.tables = dict()

        if label is not None:
            self.label = label
        else:
            self.label = self.name

        if hdf5_file_path is not None:
            self.hdf5_file_path = hdf5_file_path
        else:
            self.hdf5_file_path = "{}{}".format(self.name, ".h5")

        self.informations = kwargs

    @classmethod
    def create_from_json(cls, survey_json):
        self = cls(
            name = survey_json.get('name'),
            label = survey_json.get('label'),
            hdf5_file_path = survey_json.get('hdf5_file_path')
            )
        self.tables = survey_json.get('tables')
        return self

    def dump(self, file_path):
        with open(file_path, 'w') as _file:
            json.dump(self.to_json(), _file, ensure_ascii=False, indent=2)

    def fill_hdf_from_Rdata(self, table, verbose = False):

        assert table in self.tables, "Table {} is not a repertorid table".format(table)
        Rdata_table = self.tables[table]["Rdata_table"]
        Rdata_file = self.tables[table]["Rdata_file"]

        if not os.path.isfile(Rdata_file):
             raise Exception("file_path do  not exists")

        rpy.r.load(Rdata_file)
        stored_table = com.load_data(Rdata_table)
        store_path = Rdata_table
        store = HDFStore(self.hdf5_file_path)
        ## force_recreation = True
        ## if store_path in store:
        ##     if force_recreation is not True:
        ##         print store_path + "already exists, do not re-create and exit"
        ##         store.close()
        ##         return
        variables = self.tables[table]['variables']
        if variables is not None:
            log.info('variables asked by the user: {}'.format(variables))
            variables_stored = list(set(variables).intersection(set(stored_table.columns)))
            log.info('variables stored: {}'.format(variables_stored))
            store.append(store_path, stored_table[variables_stored], format = 'table', data_columns = stored_table.columns)
        else:
             store.append(store_path, stored_table, format = 'table', data_columns = stored_table.columns)

        store.close()
        gc.collect()

    def get_value(self, variable, table=None):
        """
        Get value

        Parameters
        ----------
        variable : string
                  name of the variable
        table : string, default None
                name of the table hosting the variable
        Returns
        -------
        df : DataFrame, default None
             A DataFrame containing the variable
        """
        if table not in self.tables:
            log.error("Table {} is not found in survey tables".format(table))
        df = self.get_values([variable], table)
        return df

    def get_values(self, variables=None, table=None):
        """
        Get values

        Parameters
        ----------
        variables : list of strings, default None
                  list of variables names, if None return the whole table
        table : string, default None
                name of the table hosting the variables
        Returns
        -------
        df : DataFrame, default None
             A DataFrame containing the variables
        """
        store = HDFStore(self.hdf5_file_path)
        df = store[table]
        if variables is None:
            return df
        else:
            diff = set(variables) - set(df.columns)
            if diff:
                raise Exception("The following variable(s) %s are missing" %diff)
            variables = list( set(variables).intersection(df.columns))
            df = df[variables]
            return df

    def insert_table(self, name = None, **kwargs):
        """
        Insert a table in the Survey
        """
        if name not in self.tables:
            self.tables[name] = dict()
        for key, val in kwargs.iteritems():
            self.tables[name][key] = val

    @classmethod
    def load(cls, file_path):
        with open(file_path, 'r') as _file:
            self_json = json.load(_file)
        log.info("Creating survey: {}".format(self_json.get('name')))
        self =  cls.create_from_json(self_json)
        return self

    def to_json(self):
        self_json = collections.OrderedDict((
            ))
        self_json['hdf5_file_path'] = self.label
        self_json['label'] = self.label
        self_json['name'] = self.name
        self_json['tables'] = collections.OrderedDict(sorted(self.tables.iteritems()))
        return self_json


class SurveyCollection(object):
    """
    A collection of Surveys
    """
    label = None
    name = None

    def __init__(self, name = None, label = None):
        super(SurveyCollection, self).__init__()
        if label is not None:
            self.label = label
        if name is not None:
            self.name = name
        self.surveys = dict()

    def dump(self, file_path = None):
        if file_path is None:
            file_path = self.config.get("collections", "default_collection")

        with open(file_path, 'w') as _file:
            json.dump(self.to_json(), _file, ensure_ascii=False, indent=2)

    def fill_hdf_from_Rdata(self):
        for survey in self.surveys:
            for table in self.tables:
                survey.fill_hdf_from_Rdata(table)

    @classmethod
    def load(cls, file_path):
        if file_path is None:
            file_path = self.config.get("collections", "default_collection")

        with open(file_path, 'r') as _file:
            self_json = json.load(_file)
        surveys = self_json.get('surveys')
        self = cls(name=self_json.get('name'), label=self_json.get('label'))
        for survey_name, survey_json in surveys.iteritems():
            print """
            {}
            {}
            """.format(survey_name, survey_json)
            log.info("Creating survey: {}".format(survey_name))
            survey = Survey(name=survey_name)
            self.surveys[survey_name] = survey.create_from_json(survey_json)
        return self

    def to_json(self):
        self_json = collections.OrderedDict((
            ))
        self_json['name'] = self.name
        self_json['surveys'] = collections.OrderedDict((
            ))
        for name, survey in self.surveys.iteritems():
            self_json['surveys'][name] = survey.to_json()
        return self_json


    def set_config_files_directory(config_files_directory = None)
        if config_files_directory is None:
            config_files_directory = default_config_files_directory

        parser = SafeConfigParser()
        self.config = parser
        config_local_ini = os.path.join(config_files_directory, 'config_local.ini')
        config_ini = os.path.join(config_files_directory, 'config.ini')
        found = parser.read([config_local_ini, config_ini])


def build_empty_erfs_survey_collection(years= None):
    if years is None:
        log.error("A list of years to process is needed")

    erfs_survey_collection = SurveyCollection(name = "erfs")
    erfs_survey_collection.set_config_files_directory()
    input_data_directory = erfs_survey_collection.config.get('data', 'input_directory')
    output_data_directory = erfs_survey_collection.config.get('data', 'output_directory')

    for year in years:
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
            "erf_menage": {  # Enquête revenu fiscaux, table ménage
                "Rdata_table" : "menage" + yr,
                "year" : year,
                "variables" : None,
                },
            "eec_menage": {  # Enquête emploi en continu, table ménage
                "Rdata_table" : "mrf" + yr + "e" + yr + "t4",
                "year" : year,
                "variables" : None,
                },
            "foyer": {      # Enquête revenu fiscaux, table foyer
                "Rdata_table" : "foyer" + yr,
                "year": year,
                "variables" : None,
                },
            "erf_indivi": {  # Enquête revenu fiscaux, table individu
                "Rdata_table" : "indivi" + yr,
                "year": year,
                "variables" : ['noi','noindiv','ident','declar1','quelfic','persfip','declar2','persfipd','wprm',
                     "zsali","zchoi","ztsai","zreti","zperi","zrsti","zalri","zrtoi","zragi","zrici","zrnci",
                     "zsalo","zchoo","ztsao","zreto","zpero","zrsto","zalro","zrtoo","zrago","zrico","zrnco",
                     ],
                },
            "eec_indivi": {  # Enquête emploi en continue, table individu
                "Rdata_table" : "irf" + yr + "e" + yr + "t4",
                "year" : year,
                "variables" : eec_variables,
                },
            "eec_cmp_1": {  # Enquête emploi en continue, table complémentaire 1
                "Rdata_table" : "icomprf" + yr + "e" + yr1 + "t1",
                "year" : year,
                "variables" : eec_variables,
                },
            "eec_cmp_2": {
                "Rdata_table" : "icomprf" + yr + "e" + yr1 + "t2",
                "year" : year,
                "variables" : eec_variables,
                },
            "eec_cmp_3": {
                "Rdata_table" : "icomprf" + yr + "e" + yr1 + "t3",
                "year" : year,
                "variables" : eec_variables,
                },
        }

        # Build absolute path for Rdata_file
        for table in erf_tables.values():
            table["Rdata_file"] = os.path.join(
                os.path.dirname(input_data_directory),
                'R',
                'erf',
                str(year),
                table["Rdata_table"] + str(".Rdata"),
                )
        survey_name = 'erfs_' + str(year)
        hdf5_file_path = os.path.join(
            os.path.dirname(output_data_directory),
            "{}{}".format(survey_name, ".h5")
            )
        survey = Survey(
            name = survey_name,
            hdf5_file_path = hdf5_file_path
            )
        surveys[survey_name] = survey
        for table, table_args in erf_tables.iteritems():
            survey.insert_table(name = table, **table_args)
    return erfs_survey_collection


if __name__ == '__main__':

    erfs_survey_collection = build_empty_erfs_survey_collection(years = [2006])
    erfs_survey_collection.fill_hdf_from_Rdata()

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

openfisca_france_data_location = pkg_resources.get_distribution('openfisca-france-data').location
default_config_files_directory = os.path.join(openfisca_france_data_location)

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
        self.tables = dict()  # TODO: rework to better organize this dict

        if label is not None:
            self.label = label

        if hdf5_file_path is not None:
            self.hdf5_file_path = hdf5_file_path

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

        assert table in self.tables, "Table {} is not a filed table".format(table)
        Rdata_table = self.tables[table]["Rdata_table"]
        Rdata_file = self.tables[table]["Rdata_file"]
        try:
            variables = self.tables[table]['variables']
        except:
            variables = None

        if not os.path.isfile(Rdata_file):
             raise Exception("file_path do  not exists")

        rpy.r.load(Rdata_file)
        stored_dataframe = com.load_data(Rdata_table)
        store_path = table

        log.info("Inserting {} in HDF file {} at point {}".format(
            Rdata_table,
            self.hdf5_file_path,
            table,
            )
        )

        if variables is not None:

            log.info('variables asked by the user: {}'.format(variables))
            variables_stored = list(set(variables).intersection(set(stored_dataframe.columns)))
            log.info('variables stored: {}'.format(variables_stored))

            stored_dataframe[variables_stored].to_hdf(self.hdf5_file_path, store_path, format='table', append=False)
        else:
             stored_dataframe.to_hdf(self.hdf5_file_path, store_path, format='table', append=False)

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

    def get_values(self, variables = None, table = None):
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
        try:
            df = store[table]
        except:
            df = store[self.tables[table]["Rdata_table"]]

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
        log.info("Getting survey information for {}".format(self_json.get('name')))
        self =  cls.create_from_json(self_json)
        return self

    def to_json(self):
        self_json = collections.OrderedDict((
            ))
        self_json['hdf5_file_path'] = self.hdf5_file_path
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

    def dump(self, file_path = None, collection = None, config_files_directory = None, append = False):
        if file_path is None:
            if collection is None:
                file_path = self.config.get("collections", "default_collection")
            else:
                file_path = self.config.get("collections", collection)

        with open(file_path, 'w') as _file:
            json.dump(self.to_json(), _file, ensure_ascii = False, indent = 2)

    def fill_hdf_from_Rdata(self, surveys_name = None):
        if surveys_name is None:
            surveys = self.surveys.values()
        for survey_name in surveys_name:
            survey = self.surveys[survey_name]
            for table in survey.tables:
                survey.fill_hdf_from_Rdata(table)

    @classmethod
    def load(cls, file_path = None, collection = None, config_files_directory = None):
        if file_path is None:
            self = cls()
            self.set_config_files_directory(config_files_directory = config_files_directory)
            if collection is None:
                file_path = self.config.get("collections", "default_collection")
            else:
                file_path = self.config.get("collections", collection)
            with open(file_path, 'r') as _file:
                self_json = json.load(_file)
                self.name = self_json.get('name')
                self.label = self_json.get('label')
        else:
            with open(file_path, 'r') as _file:
                self_json = json.load(_file)
                self = cls(name=self_json.get('name'), label=self_json.get('label'))

        surveys = self_json.get('surveys')
        for survey_name, survey_json in surveys.iteritems():
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

    def set_config_files_directory(self, config_files_directory = None):
        if config_files_directory is None:
            config_files_directory = default_config_files_directory

        parser = SafeConfigParser()

        config_local_ini = os.path.join(config_files_directory, 'config_local.ini')
        config_ini = os.path.join(config_files_directory, 'config.ini')
        found = parser.read([config_ini, config_local_ini,])
        self.config = parser

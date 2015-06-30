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


import gc
import os
import logging

from ConfigParser import SafeConfigParser
from pandas import HDFStore

log = logging.getLogger(__name__)

from . import default_config_files_directory


def temporary_store_decorator(config_files_directory = default_config_files_directory, file_name = None):
    parser = SafeConfigParser()
    config_local_ini = os.path.join(config_files_directory, 'config_local.ini')
    config_ini = os.path.join(config_files_directory, 'config.ini')
    _ = parser.read([config_ini, config_local_ini])
    tmp_directory = parser.get('data', 'tmp_directory')
    assert tmp_directory is not None, 'Temporary directory is not set'
    assert os.path.isabs(tmp_directory), 'Temporary directory path should be an absolut path'
    assert os.path.isdir(tmp_directory), 'Temporary directory does not exist'

    assert file_name is not None
    if not file_name.endswith('.h5'):
        file_name = "{}.h5".format(file_name)
    file_path = os.path.join(tmp_directory, file_name)

    def actual_decorator(func):
        def func_wrapper(*args, **kwargs):
            temporary_store = HDFStore(file_path)
            try:
                return func(*args, temporary_store = temporary_store, **kwargs)
            finally:
                gc.collect()
                temporary_store.close()

        return func_wrapper

    return actual_decorator


def get_store(config_files_directory = default_config_files_directory, file_name = None):
    parser = SafeConfigParser()
    config_local_ini = os.path.join(config_files_directory, 'config_local.ini')
    config_ini = os.path.join(config_files_directory, 'config.ini')
    _ = parser.read([config_ini, config_local_ini])
    tmp_directory = parser.get('data', 'tmp_directory')
    assert file_name is not None
    if not file_name.endswith('.h5'):
        file_name = "{}.h5".format(file_name)
    file_path = os.path.join(tmp_directory, file_name)
    return HDFStore(file_path)


def save_hdf_r_readable(data_frame, config_files_directory = default_config_files_directory, file_name = None,
                        file_path = None):
    if file_path is None:
        parser = SafeConfigParser()
        config_local_ini = os.path.join(config_files_directory, 'config_local.ini')
        config_ini = os.path.join(config_files_directory, 'config.ini')
        _ = parser.read([config_ini, config_local_ini])
        tmp_directory = parser.get('data', 'tmp_directory')
        if file_name is not None:
            if not file_name.endswith('.h5'):
                file_name = "{}.h5".format(file_name)
            file_path = os.path.join(tmp_directory, file_name)
        else:
            file_path = os.path.join(tmp_directory, 'temp.h5')

    store = HDFStore(file_path, "w", complib = str("zlib"), complevel = 5)
    store.put("dataframe", data_frame, data_columns = data_frame.columns)
    store.close()


class TemporaryStore(HDFStore):
    @classmethod
    def create(cls, config_files_directory = default_config_files_directory, file_name = None, file_path = None):
        if file_path is None:
            parser = SafeConfigParser()
            config_local_ini = os.path.join(config_files_directory, 'config_local.ini')
            config_ini = os.path.join(config_files_directory, 'config.ini')
            _ = parser.read([config_ini, config_local_ini])
            tmp_directory = parser.get('data', 'tmp_directory')
            if file_name is not None:
                if not file_name.endswith('.h5'):
                    file_name = "{}.h5".format(file_name)
                file_path = os.path.join(tmp_directory, file_name)
            else:
                file_path = os.path.join(tmp_directory, 'temp.h5')
            self = cls(file_path)
            return self

    def extract(self, name = None, variables = None):
        assert name is not None
        data_frame = self[name]
        if variables is None:
            return data_frame
        else:
            return data_frame[variables].copy()
        self.close()
        return data_frame

    def show(self):
        log.info("{}".format(self))
        self.close()

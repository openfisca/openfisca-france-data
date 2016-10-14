# -*- coding: utf-8 -*-


import gc
import os
import logging

from ConfigParser import SafeConfigParser
from pandas import HDFStore

log = logging.getLogger(__name__)

from openfisca_france_data import default_config_files_directory


def temporary_store_decorator(config_files_directory = default_config_files_directory, file_name = None):
    parser = SafeConfigParser()
    config_local_ini = os.path.join(config_files_directory, 'config_local.ini')
    config_ini = os.path.join(config_files_directory, 'config.ini')
    read_config_file_name = parser.read([config_ini, config_local_ini])
    tmp_directory = parser.get('data', 'tmp_directory')
    assert tmp_directory is not None, \
        'tmp_directory is not set: {!r} in {}'.format(tmp_directory, read_config_file_name)
    assert os.path.isabs(tmp_directory), \
        'tmp_directory should be an absolut path: {!r} in {}'.format(tmp_directory, read_config_file_name)
    assert os.path.isdir(tmp_directory), \
        'tmp_directory does not exist: {!r} in {}'.format(tmp_directory, read_config_file_name)

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

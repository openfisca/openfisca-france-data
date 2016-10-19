#! /usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
import time

from openfisca_france_data import default_config_files_directory as config_files_directory
from openfisca_france_data.input_data_builders.build_from_erfs_fpr import \
    step_01_preprocessing as preprocessing
from openfisca_france_data.input_data_builders.build_from_erfs_fpr import \
    step_02_imputation_loyer as imputation_loyer
from openfisca_france_data.input_data_builders.build_from_erfs_fpr import \
    step_03_variables_individuelles as variables_individuelles 
from openfisca_france_data.temporary import get_store
from openfisca_survey_manager.survey_collections import SurveyCollection
from openfisca_survey_manager.surveys import Survey

log = logging.getLogger(__name__)


def run_all(year = None, check = False):
    assert year is not None
    preprocessing.merge_tables(year = year)
    # imputation_loyer.imputation_loyer(year = year)
    variables_individuelles.create_variables_individuelles(year = year)

    temporary_store = get_store(file_name = 'erfs_fpr')
    data_frame = temporary_store['input_{}'.format(year)]

    # Saving the data_frame
    openfisca_survey_collection = SurveyCollection(name = "openfisca", config_files_directory = config_files_directory)
    output_data_directory = openfisca_survey_collection.config.get('data', 'output_directory')
    survey_name = "openfisca_erfs_fpr_data_{}".format(year)
    table = "input"
    hdf5_file_path = os.path.join(os.path.dirname(output_data_directory), "{}.h5".format(survey_name))
    survey = Survey(
        name = survey_name,
        hdf5_file_path = hdf5_file_path,
        )
    survey.insert_table(name = table, data_frame = data_frame)
    openfisca_survey_collection.surveys.append(survey)
    collections_directory = openfisca_survey_collection.config.get('collections', 'collections_directory')
    json_file_path = os.path.join(collections_directory, 'openfisca_erfs_fpr.json')
    openfisca_survey_collection.dump(json_file_path = json_file_path)


if __name__ == '__main__':
    import time
    start = time.time()
    logging.basicConfig(level = logging.INFO, filename = 'run_all.log', filemode = 'w')
    run_all(year = 2012, check = False)
    log.info("Script finished after {}".format(time.time() - start))
    print time.time() - start

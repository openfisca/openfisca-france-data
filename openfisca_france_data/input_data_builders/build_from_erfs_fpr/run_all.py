#! /usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
import time

from openfisca_france_data.input_data_builders.build_from_erfs_fpr import \
    step_01_preprocessing as preprocessing
from openfisca_france_data.input_data_builders.build_from_erfs_fpr import \
    step_02_imputation_loyer as imputation_loyer
from openfisca_france_data.temporary import get_store
from openfisca_survey_manager.survey_collections import SurveyCollection
from openfisca_survey_manager.surveys import Survey

log = logging.getLogger(__name__)


def run_all(year = None, check = False):
    assert year is not None
    preprocessing.merge_tables(year = year)
    imputation_loyer(year = year)
    # try:
    #     imputation_loyer.imputation_loyer(year = year)
    # except Exception, e:
    #     log.info('Do not impute loyer because of the following error: \n {}'.format(e))
    #     pass
    #    fip.create_fip(year = year)
    #    famille.famille(year = year)
    #    foyer.sif(year = year)
    #    foyer.foyer_all(year = year)
    #    rebuild.create_totals_first_pass(year = year)
    #    rebuild.create_totals_second_pass(year = year)
    #    rebuild.create_final(year = year)
    #    invalides.invalide(year = year)
    #    final.final(year = year, check = check)
    temporary_store = get_store(file_name = 'erfs_fpr')
    data_frame = temporary_store['input_{}'.format(year)]

    # Saving the data_frame
#    openfisca_survey_collection = SurveyCollection(name = "openfisca", config_files_directory = config_files_directory)
#    output_data_directory = openfisca_survey_collection.config.get('data', 'output_directory')
#    survey_name = "openfisca_data_{}".format(year)
#    table = "input"
#    hdf5_file_path = os.path.join(os.path.dirname(output_data_directory), "{}.h5".format(survey_name))
#    survey = Survey(
#        name = survey_name,
#        hdf5_file_path = hdf5_file_path,
#        )
#    survey.insert_table(name = table, data_frame = data_frame)
#    openfisca_survey_collection.surveys.append(survey)
#    collections_directory = openfisca_survey_collection.config.get('collections', 'collections_directory')
#    json_file_path = os.path.join(collections_directory, 'openfisca.json')
#    openfisca_survey_collection.dump(json_file_path = json_file_path)


if __name__ == '__main__':
    import time
    start = time.time()
    logging.basicConfig(level = logging.INFO, filename = 'run_all.log', filemode = 'w')
    run_all(year = 2012, check = False)
    log.info("Script finished after {}".format(time.time() - start))
    print time.time() - start

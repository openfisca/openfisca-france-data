# -*- coding: utf-8 -*-

import logging

from openfisca_france_data.erfs_fpr.input_data_builder import (
    step_01_preprocessing as preprocessing,
    # step_02_imputation_loyer as imputation_loyer,
    step_03_variables_individuelles as variables_individuelles,
    step_04_famille as famille,
    step_05_final as final,
    )
from openfisca_survey_manager.temporary import get_store
from openfisca_france_data.utils import store_input_data_frame


log = logging.getLogger(__name__)


def build(year = None):
    assert year is not None
    #
    preprocessing.build_merged_dataframes(year = year)

    # openfisca_survey_collection = SurveyCollection(name = 'openfisca')
    # stata_directory = openfisca_survey_collection.config.get('data', 'stata_directory')
    # stata_file = os.path.join(stata_directory, 'log_men_ERFS.dta')
    # imputation_loyer.merge_imputation_loyer(stata_file = stata_file, year = year)

    #
    variables_individuelles.build_variables_individuelles(year = year)
    famille.build_famille(year = year)
    final.create_input_data_frame(year = year)
    #
    temporary_store = get_store(file_name = 'erfs_fpr')
    data_frame = temporary_store['input_{}'.format(year)]
    # Save the data_frame in a collection
    store_input_data_frame(
        data_frame = data_frame,
        collection = "openfisca_erfs_fpr",
        survey = "openfisca_erfs_fpr_data_{}".format(year),
        )


if __name__ == '__main__':
    import sys
    import time
    start = time.time()
    logging.basicConfig(level = logging.INFO, stream = sys.stdout)
    year = 2012
    # build(year = year)
    # TODO: create_enfants_a_naitre(year = year)
    log.info("Script finished after {}".format(time.time() - start))
    print(time.time() - start)

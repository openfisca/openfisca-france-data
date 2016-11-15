# -*- coding: utf-8 -*-

import logging

from openfisca_france_data.erfs_fpr.input_data_builder import (
    step_01_preprocessing as preprocessing,
    # step_02_imputation_loyer as imputation_loyer,
    step_03_variables_individuelles as variables_individuelles,
    step_04_famille as famille,
    step_05_final as final,
    )
from openfisca_france_data.temporary import get_store
from openfisca_france_data.utils import store_input_data_frame


log = logging.getLogger(__name__)


def build(year = None, check = False):
    assert year is not None
    preprocessing.build_merged_dataframes(year = year)
    # imputation_loyer.imputation_loyer(year = year)
    variables_individuelles.create_variables_individuelles(year = year)
    famille.create_famille(year = year)
    final.create_input_data_frame(year = year)

    temporary_store = get_store(file_name = 'erfs_fpr')
    data_frame = temporary_store['input_{}'.format(year)]
    # Save the data_frame in a collection
    store_input_data_frame(
        data_frame = data_frame,
        collection = "openfisca",
        survey = "openfisca_erfs_fpr_data_{}".format(year),
        )

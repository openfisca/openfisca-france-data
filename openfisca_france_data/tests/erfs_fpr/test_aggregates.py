# -*- coding: utf-8 -*-

from __future__ import division


import logging
import numpy as np


from openfisca_france_data.tests import base as base_survey
from openfisca_france_data.erfs_fpr.get_survey_scenario import get_survey_scenario
from openfisca_france_data.aggregates import Aggregates


log = logging.getLogger(__name__)


def test_erfs_fpr_survey_simulation_aggregates(year = 2012, rebuild_input_data = False):
    np.seterr(all = 'raise')
    tax_benefit_system = base_survey.france_data_tax_benefit_system

    survey_scenario = get_survey_scenario(
        tax_benefit_system = tax_benefit_system,
        baseline_tax_benefit_system = tax_benefit_system,
        year = year,
        rebuild_input_data = rebuild_input_data,
        )
    return survey_scenario


def test_erfs_fpr_aggregates_reform():
    '''
    test aggregates value with data
    :param year: year of data and simulation to test agregates
    :param reform: optional argument, put an openfisca_france.refoms object, default None
    '''
    tax_benefit_system = base_survey.france_data_tax_benefit_system
    year = 2012
    survey_scenario = get_survey_scenario(
        reform_key = 'plf2015',
        baseline_tax_benefit_system = tax_benefit_system,
        year = year,
        rebuild_input_data = False,
        )
    aggregates = Aggregates(survey_scenario = survey_scenario)
    base_data_frame = aggregates.compute_aggregates()

    return aggregates, base_data_frame


if __name__ == '__main__':
    import logging
    log = logging.getLogger(__name__)
    import sys
    logging.basicConfig(level = logging.INFO, stream = sys.stdout)
    # aggregates_data_frame, difference_data_frame,
    survey_scenario = test_erfs_fpr_survey_simulation_aggregates(rebuild_input_data = False)

    # aggregates = Aggregates(survey_scenario = survey_scenario)
    # df = aggregates.compute_aggregates(use_baseline = False)
    # print df
    # difference_data_frame = aggregates.compute_difference()
    # return aggregates.base_data_frame, difference_data_frame, survey_scenario

    aggregates, base_data_frame = test_erfs_fpr_aggregates_reform()


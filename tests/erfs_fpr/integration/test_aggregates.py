# -*- coding: utf-8 -*-

import logging
import numpy as np

from openfisca_france_data import france_data_tax_benefit_system
from openfisca_france_data.erfs_fpr.get_survey_scenario import get_survey_scenario
from openfisca_france_data.aggregates import Aggregates


log = logging.getLogger(__name__)


def test_erfs_fpr_survey_simulation_aggregates(year = 2012, rebuild_input_data = False):
    np.seterr(all = 'raise')
    tax_benefit_system = france_data_tax_benefit_system

    survey_scenario = get_survey_scenario(
        tax_benefit_system = tax_benefit_system,
        baseline_tax_benefit_system = tax_benefit_system,
        year = year,
        rebuild_input_data = rebuild_input_data,
        )
    aggregates = Aggregates(survey_scenario = survey_scenario)

    return survey_scenario, aggregates


def test_erfs_fpr_aggregates_reform():
    '''
    test aggregates value with data
    :param year: year of data and simulation to test agregates
    :param reform: optional argument, put an openfisca_france.refoms object, default None
    '''
    tax_benefit_system = france_data_tax_benefit_system
    year = 2012
    survey_scenario = get_survey_scenario(
        reform = 'plf2015',
        baseline_tax_benefit_system = tax_benefit_system,
        year = year,
        rebuild_input_data = False,
        )
    aggregates = Aggregates(survey_scenario = survey_scenario)
    base_data_frame = aggregates.compute_aggregates()
    difference_data_frame = aggregates.compute_difference()

    return aggregates, base_data_frame, difference_data_frame


if __name__ == '__main__':
    import logging
    log = logging.getLogger(__name__)
    import sys
    logging.basicConfig(level = logging.DEBUG, stream = sys.stdout)
    survey_scenario, aggregates = test_erfs_fpr_survey_simulation_aggregates(
        year = 2014, rebuild_input_data = False)
    survey_scenario._set_used_as_input_variables_by_entity()
    print(survey_scenario.used_as_input_variables_by_entity)
    df = aggregates.compute_aggregates(use_baseline = True, actual = False)
    df.to_csv('aggregates.csv')
    # aggregates, base_data_frame, difference_data_frame = test_erfs_fpr_aggregates_reform()

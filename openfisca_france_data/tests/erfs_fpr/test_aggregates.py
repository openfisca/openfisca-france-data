# -*- coding: utf-8 -*-

from __future__ import division


import logging
import numpy as np


from openfisca_france_data.tests import base as base_survey
from openfisca_france_data.erfs_fpr.scenario import ErfsFprSurveyScenario
from openfisca_france_data.aggregates import Aggregates


log = logging.getLogger(__name__)


def test_erfs_fpr_survey_simulation_aggregates(year = 2012, rebuild_input_data = False):
    np.seterr(all='raise')
    tax_benefit_system = base_survey.france_data_tax_benefit_system
    survey_scenario = ErfsFprSurveyScenario.create(
        tax_benefit_system = tax_benefit_system,
        reference_tax_benefit_system = tax_benefit_system,
        year = year,
        )
    survey_scenario.init_from_survey_tables(rebuild_input_data = rebuild_input_data)
    return survey_scenario


def test_erfs_fpr_aggregates_reform():
    '''
    test aggregates value with data
    :param year: year of data and simulation to test agregates
    :param reform: optional argument, put an openfisca_france.refoms object, default None
    '''
    survey_scenario = ErfsFprSurveyScenario.create(data_year = 2012, year = 2015, reform_key = 'plf2015')
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

    aggregates = Aggregates(survey_scenario = survey_scenario)
    df = aggregates.compute_aggregates(reference = False)
    # difference_data_frame = aggregates.compute_difference()
    # return aggregates.base_data_frame, difference_data_frame, survey_scenario

    # df = test_erfs_aggregates_reform()


# -*- coding: utf-8 -*-


import logging
import numpy as np


from openfisca_france_data.aggregates import Aggregates
from openfisca_france_data.erfs.scenario import ErfsSurveyScenario
from openfisca_france_data.erfs_fpr.scenario import ErfsFprSurveyScenario
from openfisca_france_data.tests import base as base_survey


log = logging.getLogger(__name__)


def test_erfs_fpr_survey_simulation_aggregates(year = 2012):
    np.seterr(all='raise')
    tax_benefit_system = base_survey.get_cached_reform(
        reform_key = 'inversion_directe_salaires',
        tax_benefit_system = base_survey.france_data_tax_benefit_system,
        )
    survey_scenario = ErfsFprSurveyScenario.create(
        tax_benefit_system = tax_benefit_system,
        reference_tax_benefit_system = tax_benefit_system,
        year = year,
        )
    return survey_scenario


def test_erfs_survey_simulation(year = 2009):
    survey_scenario = ErfsSurveyScenario.create(year = year)
    aggregates = Aggregates(survey_scenario = survey_scenario)
    aggregates.compute_aggregates()
    return aggregates.base_data_frame


def test_erfs_aggregates_reform():
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
    #aggregates_data_frame, difference_data_frame,
    survey_scenario = test_erfs_fpr_survey_simulation_aggregates()


    aggregates = Aggregates(survey_scenario = survey_scenario)
    aggregates.compute_aggregates()
    print aggregates.base_data_frame
    # difference_data_frame = aggregates.compute_difference()
#    return aggregates.base_data_frame, difference_data_frame, survey_scenario

    # df = test_erfs_aggregates_reform()

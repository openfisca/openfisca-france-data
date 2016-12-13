# -*- coding: utf-8 -*-


import logging

from openfisca_france_data.aggregates import Aggregates
from openfisca_france_data.erfs.scenario import ErfsSurveyScenario
from openfisca_france_data.erfs_fpr.scenario import ErfsFprSurveyScenario


log = logging.getLogger(__name__)


def test_erfs_fpr_survey_simulation_aggregates(year = 2012):
    try:
        survey_scenario = ErfsFprSurveyScenario.create(year = year)
    except AssertionError as e:
        print(e)
        return
    aggregates = Aggregates(survey_scenario = survey_scenario)
    aggregates.compute_aggregates()
    return aggregates.base_data_frame


def test_erfs_survey_simulation(year = 2009):
    try:
        survey_scenario = ErfsSurveyScenario.create(year = year)
    except AssertionError as e:
        print(e)
        return
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
    df = test_erfs_fpr_survey_simulation_aggregates()
    # df = test_erfs_aggregates_reform()

# -*- coding: utf-8 -*-


import pytest

from openfisca_france_data.aggregates import Aggregates
from openfisca_france_data.erfs.scenario import ErfsSurveyScenario
from openfisca_france_data.erfs_fpr.scenario import ErfsFprSurveyScenario


@pytest.mark.skip(reason = 'assert False != (None is not None)')
def test_erfs_survey_simulation(year = 2009):
    survey_scenario = ErfsSurveyScenario.create(year = year)
    aggregates = Aggregates(survey_scenario = survey_scenario)
    aggregates.compute_aggregates()
    return aggregates.base_data_frame


@pytest.mark.skip(reason = "TypeError: create() got an unexpected keyword argument 'data_year'")
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

# -*- coding: utf-8 -*-


from openfisca_france_data.erfs.scenario import ErfsSurveyScenario
from openfisca_france_data.erfs_fpr.scenario import ErfsFprSurveyScenario


def test_pivot_table_1d_mean():
    survey_scenario = get_survey_scenario(kind = 'erfs_fpr')
    pivot_table = survey_scenario.compute_pivot_table(
        columns = ['decile_rfr'],
        values = ['irpp']
        )
    return pivot_table


def test_pivot_table_1d_sum():
    survey_scenario = get_survey_scenario(kind = 'erfs_fpr')
    pivot_table = survey_scenario.compute_pivot_table(
        aggfunc = 'sum',
        columns = ['decile_rfr'],
        values = ['irpp']
        )
    return pivot_table


def test_pivot_table_1d_count():
    survey_scenario = get_survey_scenario(kind = 'erfs_fpr')
    pivot_table = survey_scenario.compute_pivot_table(
        aggfunc = 'count',
        columns = ['decile_rfr'],
        values = ['irpp']
        )
    return pivot_table


def test_pivot_table_2d_2values():
    survey_scenario = get_survey_scenario(kind = 'erfs_fpr')
    pivot_table = survey_scenario.compute_pivot_table(
        columns = ['decile_rfr'],
        index = ['nbptr'],
        values = ['irpp', 'rfr']
        )
    return pivot_table


def get_survey_scenario(kind = 'erfs_fpr'):
    if kind == 'erfs_fpr':
        year = 2012
        SurveyScenario = ErfsFprSurveyScenario
    else:
        year = 2009
        SurveyScenario = ErfsSurveyScenario

    return SurveyScenario.create(year = year)


if __name__ == '__main__':
    import logging
    import time
    log = logging.getLogger(__name__)
    import sys
    logging.basicConfig(level = logging.INFO, stream = sys.stdout)
    start = time.time()
    print(test_pivot_table_1d_sum())
    print(test_pivot_table_1d_mean())
    print(test_pivot_table_2d())
    print(time.time() - start)

# -*- coding: utf-8 -*-


from openfisca_france_data.erfs.scenario import ErfsSurveyScenario


def test_pivot_table_1d_mean(year = 2009):
    survey_scenario = ErfsSurveyScenario.create(year = year)
    pivot_table = survey_scenario.compute_pivot_table(
        columns = ['decile_rfr'],
        values = ['irpp']
        )
    return pivot_table


def test_pivot_table_1d_sum(year = 2009):
    survey_scenario = ErfsSurveyScenario.create(year = year)
    pivot_table = survey_scenario.compute_pivot_table(
        aggfunc = 'sum',
        columns = ['decile_rfr'],
        values = ['irpp']
        )
    return pivot_table


def test_pivot_table_1d_count(year = 2009):
    survey_scenario = ErfsSurveyScenario.create(year = year)
    pivot_table = survey_scenario.compute_pivot_table(
        aggfunc = 'count',
        columns = ['decile_rfr'],
        values = ['irpp']
        )
    return pivot_table


def test_pivot_table_2d(year = 2009):
    survey_scenario = ErfsSurveyScenario.create(year = year)
    pivot_table = survey_scenario.compute_pivot_table(
        columns = ['decile_rfr'],
        index = ['nbptr'],
        values = ['irpp']
        )
    return pivot_table


if __name__ == '__main__':
    import logging
    import time
    log = logging.getLogger(__name__)
    import sys
    logging.basicConfig(level = logging.INFO, stream = sys.stdout)
    start = time.time()
    pivot_table = test_pivot_table_1d_sum(year = 2009)
    print(time.time() - start)

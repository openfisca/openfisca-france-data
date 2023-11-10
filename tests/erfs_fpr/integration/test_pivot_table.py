import pytest

from openfisca_france_data.erfs_fpr.get_survey_scenario import get_survey_scenario as erfs_fpr_get_survey_scenario
from openfisca_france_data.erfs.scenario import ErfsSurveyScenario
from openfisca_france_data import base_survey


def test_pivot_table_1d_mean():
    year = 2013
    survey_scenario = get_survey_scenario(kind = 'erfs_fpr', year = year)
    pivot_table = survey_scenario.compute_pivot_table(
        columns = ['decile_rfr'],
        values = ['impot_revenu_restant_a_payer'],
        period = year,
        )
    return pivot_table


def test_pivot_table_1d_sum():
    year = 2013
    survey_scenario = get_survey_scenario(kind = 'erfs_fpr', year = year)
    pivot_table = survey_scenario.compute_pivot_table(
        aggfunc = 'sum',
        columns = ['decile_rfr'],
        values = ['impot_revenu_restant_a_payer'],
        period = year,
        )
    return pivot_table


def test_pivot_table_1d_count():
    year = 2013
    survey_scenario = get_survey_scenario(kind = 'erfs_fpr', year = year)
    pivot_table = survey_scenario.compute_pivot_table(
        aggfunc = 'count',
        columns = ['decile_rfr'],
        values = ['impot_revenu_restant_a_payer'],
        period = year,
        )
    return pivot_table


def test_pivot_table_2d_2values():
    year = 2013
    survey_scenario = get_survey_scenario(kind = 'erfs_fpr', year = year)
    pivot_table = survey_scenario.compute_pivot_table(
        columns = ['decile_rfr'],
        index = ['nbptr'],
        values = ['impot_revenu_restant_a_payer', 'rfr'],
        period = year,
        )
    return pivot_table


def get_survey_scenario(kind = 'erfs_fpr', year = None):
    if kind == 'erfs_fpr':
        tax_benefit_system = base_survey.france_data_tax_benefit_system
        return erfs_fpr_get_survey_scenario(year = year, tax_benefit_system = tax_benefit_system)
    else:
        year = 2009
        SurveyScenario = ErfsSurveyScenario

    return SurveyScenario.create(period = year)

import pytest

from openfisca_france_data.erfs_fpr.get_survey_scenario import get_survey_scenario
from openfisca_france_data import base_survey


def test_inflation():
    period = year = 2013
    survey_scenario = get_survey_scenario(
        year = year,
        tax_benefit_system = base_survey.france_data_tax_benefit_system
        )
    target_by_variable = dict(
        salaire_imposable = 1.2e08,
        )
    survey_scenario.inflate(target_by_variable = target_by_variable, period = period)
    assert abs(survey_scenario.compute_aggregate('salaire_imposable', period = period) - 1.2e08) / 1.2e08 < 1e-6, \
        "{} != {}".format(survey_scenario.compute_aggregate('salaire_imposable', period = period), 1.2e08)

import os

import pytest

from openfisca_survey_manager.calibration import Calibration  # type: ignore
from openfisca_france_data import openfisca_france_data_location
from openfisca_france_data.model.calage import create_dic_calage
from openfisca_france_data.reforms.variables_calibration import create_calibration_tax_benefit_system
from openfisca_france_data.erfs_fpr.scenario import (  # type: ignore
    ErfsFprSurveyScenario,
    )
from openfisca_france_data import france_data_tax_benefit_system

@pytest.fixture
def location() -> str:
    return openfisca_france_data_location


def test_calage(survey_scenario, fake_input_data, location, year: int = 2015):
    # On ititialise le survey scenario
    survey_scenario2 = ErfsFprSurveyScenario.create(
    tax_benefit_system = create_calibration_tax_benefit_system(france_data_tax_benefit_system),
    period = year,
    )
    survey_scenario = survey_scenario2

    # On charge les données
    input_data = fake_input_data(year)

    # On fait la calibration
    parameters = dict(
        method = "logit",
        invlo = 3,
        up = 3,
        )

    base_year = 2013

    target_margins_by_variable = create_dic_calage(year, base_year, ["age"])

    calibration_kwargs = {'target_margins_by_variable': target_margins_by_variable, 'parameters': parameters}

    # On initialise le survey scenario
    survey_scenario.init_from_data(data = dict(input_data_frame = input_data), calibration_kwargs = calibration_kwargs)
    weight_base = sum(survey_scenario.calculate_variable("wprm", period = base_year))

    assert weight_base < sum(survey_scenario.calculate_variable("wprm", period = year))

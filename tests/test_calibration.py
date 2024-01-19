import os

import pytest

from openfisca_survey_manager.calibration import Calibration  # type: ignore
from openfisca_france_data import openfisca_france_data_location




@pytest.fixture
def location() -> str:
    return openfisca_france_data_location


def test_calibration(survey_scenario, fake_input_data, location, year: int = 2009):
    # On ititialise le survey scenario
    survey_scenario = survey_scenario(year)

    # On charge les données
    input_data = fake_input_data(year)

    # On initialise le survey scenario
    survey_scenario.init_from_data(data = dict(input_data_frame = input_data))

    # On fait la calibration
    parameters = dict(
        method = "logit",
        invlo = 3,
        up = 3,
        )

    pre_cal_weight = survey_scenario.calculate_variable("wprm", period = year)
    target_entity_count = pre_cal_weight.sum() * 1.123
    survey_scenario.calibrate(target_entity_count = target_entity_count, entity = "menage", parameters = parameters, period = year)

    assert pre_cal_weight * 1.123 == survey_scenario.calculate_variable("wprm", period = year)

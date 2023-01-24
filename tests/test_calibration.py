import pkg_resources
import os

import pytest

from openfisca_survey_manager.calibration import Calibration  # type: ignore


@pytest.fixture
def location() -> str:
    return pkg_resources.get_distribution("openfisca-france-data").location


def test_calibration(survey_scenario, fake_input_data, location, year: int = 2009):
    # On ititialise le survey scenario
    survey_scenario = survey_scenario(year)

    # On charge les données
    input_data = fake_input_data(year)

    # On initialise le survey scenario
    survey_scenario.init_from_data(data = dict(input_data_frame = input_data))

    # On fait la calibration
    calibration = Calibration(survey_scenario)
    calibration.parameters["method"] = "linear"
    calibration.total_population = calibration.initial_total_population * 1.123

    calibration.set_parameters("invlo", 3)
    calibration.set_parameters("up", 3)
    calibration.set_parameters("method", "logit")

    calibration.calibrate()
    pre_cal_weight = survey_scenario.calculate_variable("wprm", period = year)
    calibration.set_calibrated_weights()
    assert pre_cal_weight * 1.123 == survey_scenario.calculate_variable("wprm", period = year)


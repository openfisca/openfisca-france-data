# -*- coding: utf-8 -*-


import pkg_resources
import os

import pytest

from openfisca_survey_manager.calibration import Calibration
from openfisca_france_data.erfs.scenario import ErfsSurveyScenario


@pytest.fixture
def location():
    return pkg_resources.get_distribution('openfisca-france-data').location


@pytest.mark.skip(reason = 'assert None is not None')
def test_calibration():
    year = 2009
    survey_scenario = ErfsSurveyScenario().create(year = year)
    calibration = Calibration(survey_scenario)
    calibration.parameters['method'] = 'linear'
    calibration.total_population = calibration.initial_total_population * 1.123

    filename = os.path.join(
        location,
        "openfisca_france_data",
        "calibrations",
        "calib_2006.csv"
        )

    calibration.set_inputs_margins_from_file(filename, 2006)
    calibration.set_parameters('invlo', 3)
    calibration.set_parameters('up', 3)
    calibration.set_parameters('method', 'logit')
    calibration.calibrate()

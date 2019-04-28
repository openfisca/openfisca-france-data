# -*- coding: utf-8 -*-


import pkg_resources
import os

import pytest

from openfisca_core.taxbenefitsystems import TaxBenefitSystem  # type: ignore
from openfisca_france_data import france_data_tax_benefit_system  # type: ignore
from openfisca_france_data.erfs.scenario import ErfsSurveyScenario  # type: ignore
from openfisca_survey_manager.calibration import Calibration  # type: ignore


@pytest.fixture
def tax_benefit_system() -> TaxBenefitSystem:
    return france_data_tax_benefit_system


@pytest.fixture
def year() -> int:
    return 2009


@pytest.fixture
def survey_scenario(
        tax_benefit_system: TaxBenefitSystem,
        year: int,
        ) -> ErfsSurveyScenario:
    return ErfsSurveyScenario.create(
        tax_benefit_system = tax_benefit_system,
        year = year,
        )


@pytest.fixture
def location() -> str:
    return pkg_resources.get_distribution("openfisca-france-data").location


@pytest.mark.skip(reason = "assert data is not None")
def test_calibration(survey_scenario, year, location):
    calibration = Calibration(survey_scenario, period = year)
    calibration.parameters["method"] = "linear"
    calibration.total_population = calibration.initial_total_population * 1.123

    filename = os.path.join(
        location,
        "openfisca_france_data",
        "calibrations",
        "calib_2006.csv"
        )

    calibration.set_inputs_margins_from_file(filename, 2006)
    calibration.set_parameters("invlo", 3)
    calibration.set_parameters("up", 3)
    calibration.set_parameters("method", "logit")

    assert calibration.calibrate()

# -*- coding: utf-8 -*-


import pytest

from openfisca_core.taxbenefitsystems import TaxBenefitSystem  # type: ignore
from openfisca_france_data import france_data_tax_benefit_system  # type: ignore
from openfisca_france_data.aggregates import Aggregates  # type: ignore
from openfisca_france_data.erfs.scenario import ErfsSurveyScenario  # type: ignore
from openfisca_france_data.erfs_fpr.scenario import (  # type: ignore
    ErfsFprSurveyScenario,
    )


@pytest.fixture
def tax_benefit_system() -> TaxBenefitSystem:
    return france_data_tax_benefit_system


@pytest.fixture
def survey_scenario(
        tax_benefit_system: TaxBenefitSystem,
        year: int = 2009,
        ) -> ErfsSurveyScenario:
    return ErfsSurveyScenario.create(
        tax_benefit_system = tax_benefit_system,
        year = year,
        )


@pytest.mark.skip(reason = "assert survey_scenario.simulation is not None")
def test_erfs_survey_simulation(survey_scenario):
    aggregates = Aggregates(survey_scenario = survey_scenario)
    aggregates.compute_aggregates()
    return aggregates.base_data_frame


@pytest.mark.skip(
    reason = "TypeError: create() got an unexpected keyword argument 'data_year'",
    )
def test_erfs_fpr_aggregates_reform():
    survey_scenario = ErfsFprSurveyScenario.create(
        data_year = 2012,
        year = 2015,
        reform_key = 'plf2015',
        )

    aggregates = Aggregates(survey_scenario = survey_scenario)
    base_data_frame = aggregates.compute_aggregates()
    return aggregates, base_data_frame

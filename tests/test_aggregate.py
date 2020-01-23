# -*- coding: utf-8 -*-


import pytest

from openfisca_france_data.aggregates import Aggregates  # type: ignore
from openfisca_france_data.erfs_fpr.scenario import (  # type: ignore
    ErfsFprSurveyScenario,
    )


@pytest.mark.skip(reason = "ValueError: NumPy boolean array indexing assignment...")
def test_erfs_survey_simulation(survey_scenario, fake_input_data, year: int = 2009):
    # On ititialise le survey scenario
    survey_scenario = survey_scenario(year)

    # On charge les données
    input_data = fake_input_data(year)

    # On initialise le survey scenario
    survey_scenario.init_from_data(data = dict(input_data_frame = input_data))

    # On calcule les agrégats
    aggregates = Aggregates(survey_scenario = survey_scenario)
    aggregates.compute_aggregates(use_baseline = False)
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

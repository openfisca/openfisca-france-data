import pytest


from openfisca_france_data import france_data_tax_benefit_system  # type: ignore
from openfisca_france_data.aggregates import FranceAggregates as Aggregates  # type: ignore
from openfisca_france_data.erfs_fpr.scenario import (  # type: ignore
    ErfsFprSurveyScenario,
    )


@pytest.mark.skip(
    reason = "FileNotFoundError: [Errno 2] No such file or directory: '/opt/hostedtoolcache/Python/3.9.9/x64/lib/python3.9/site-packages/openfisca_france_data/assets/agregats_tests_taxipp_2_0.xlsx'",
    )
def test_erfs_survey_simulation(survey_scenario, fake_input_data, year: int = 2009):
    # On ititialise le survey scenario
    survey_scenario = ErfsFprSurveyScenario.create(year)

    # On charge les données
    input_data = fake_input_data(year)

    # On initialise le survey scenario
    survey_scenario.init_from_data(data = dict(input_data_frame = input_data))

    # On calcule les agrégats
    aggregates = Aggregates(survey_scenario = survey_scenario, target_source = 'taxipp')
    aggregates.compute_aggregates(use_baseline = False)
    return aggregates.base_data_frame


@pytest.mark.skip(
    reason = "FileNotFoundError: [Errno 2] No such file or directory: '/opt/hostedtoolcache/Python/3.9.9/x64/lib/python3.9/site-packages/openfisca_france_data/assets/agregats_tests_taxipp_2_0.xlsx'",
    )
def test_erfs_fpr_aggregates_reform(fake_input_data, year:int = 2013):
    survey_scenario = ErfsFprSurveyScenario.create(
        year = year,
        reform_key = 'plf2015',
        baseline_tax_benefit_system = france_data_tax_benefit_system,
        )
    # On charge les données
    input_data = fake_input_data(year)

    # On initialise le survey scenario
    survey_scenario.init_from_data(data = dict(input_data_frame = input_data))

    aggregates = Aggregates(survey_scenario = survey_scenario, target_source = 'taxipp')
    base_data_frame = aggregates.compute_aggregates()
    return aggregates, base_data_frame

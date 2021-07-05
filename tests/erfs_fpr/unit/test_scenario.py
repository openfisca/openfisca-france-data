import pytest

from openfisca_france_data.erfs_fpr.scenario import ErfsFprSurveyScenario


@pytest.fixture
def year() -> int:
    return 2019


def test_create_scenario(year):
    assert ErfsFprSurveyScenario(year)

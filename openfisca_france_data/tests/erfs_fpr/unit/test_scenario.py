# -*- coding: utf-8 -*-


import pytest

from openfisca_france_data.erfs_fpr.scenario import ErfsFprSurveyScenario


@pytest.fixture
def year() -> int:
    return 2019


@pytest.fixture
def word() -> str:
    return 'openfisca'


def test_create_scenario(year: int):
    assert ErfsFprSurveyScenario(year)


def test_create_scenario_with_word(word: str):
    with pytest.raises(TypeError):
        ErfsFprSurveyScenario(word)  # type: ignore


def test_create_scenario_without_year():
    with pytest.raises(TypeError):
        ErfsFprSurveyScenario()

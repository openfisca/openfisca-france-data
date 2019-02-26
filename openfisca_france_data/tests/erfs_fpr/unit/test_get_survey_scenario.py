# -*- coding: utf-8 -*-


import pytest

from openfisca_core.reforms import Reform  # type: ignore
from openfisca_core.taxbenefitsystems import TaxBenefitSystem  # type: ignore

from openfisca_france.reforms.plf2015 import plf2015  # type: ignore

from openfisca_france_data import france_data_tax_benefit_system
from openfisca_france_data.erfs_fpr.get_survey_scenario import (
    get_survey_scenario,
    get_tax_benefit_system,
    get_baseline_tax_benefit_system,
    )


@pytest.fixture
def tax_benefit_system() -> TaxBenefitSystem:
    return france_data_tax_benefit_system


@pytest.fixture
def reform() -> Reform:
    return plf2015


@pytest.mark.skip(reason = 'AssertionError: {} is not a valid path')
def test_get_survey_scenario():
    assert get_survey_scenario()


def test_get_tax_benefit_system(tax_benefit_system: TaxBenefitSystem):
    assert get_tax_benefit_system(tax_benefit_system, None, None), tax_benefit_system


def test_get_tax_benefit_system_with_tax_benefit_system(tax_benefit_system: TaxBenefitSystem):
    assert get_tax_benefit_system(tax_benefit_system, tax_benefit_system, None), tax_benefit_system


def test_get_tax_benefit_system_with_reform(
        tax_benefit_system: TaxBenefitSystem,
        reform: Reform
        ):
    assert get_tax_benefit_system(tax_benefit_system, None, reform), reform(tax_benefit_system)


def test_get_tax_benefit_system_without_arguments():
    with pytest.raises(TypeError):
        get_tax_benefit_system(None, None, None)


def test_get_baseline_tax_benefit_system(tax_benefit_system: TaxBenefitSystem):
    assert get_baseline_tax_benefit_system(tax_benefit_system, None), tax_benefit_system


def test_get_baseline_tax_benefit_system_with_baseline_tax_benefit_system(
        tax_benefit_system: TaxBenefitSystem
        ):
    assert get_baseline_tax_benefit_system(None, tax_benefit_system), tax_benefit_system


def test_get_baseline_tax_benefit_system_without_arguments():
    with pytest.raises(TypeError):
        get_baseline_tax_benefit_system(None, None)

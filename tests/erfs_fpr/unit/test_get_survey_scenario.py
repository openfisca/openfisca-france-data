import pytest

from openfisca_core.reforms import Reform  # type: ignore
from openfisca_france import FranceTaxBenefitSystem as TaxBenefitSystem  # type: ignore

from openfisca_france_data.reforms.old_openfisca_france_reforms.plf2015 import plf2015  # type: ignore

from openfisca_france_data import france_data_tax_benefit_system
from openfisca_france_data.erfs_fpr.get_survey_scenario import (
    get_survey_scenario,
    get_tax_benefit_system,
    get_baseline_tax_benefit_system,
    )


@pytest.fixture
def tax_benefit_system() -> TaxBenefitSystem:
    return TaxBenefitSystem()


@pytest.fixture
def default_tax_benefit_system() -> TaxBenefitSystem:
    return france_data_tax_benefit_system


@pytest.fixture
def reform() -> Reform:
    return plf2015


@pytest.mark.skip(reason = 'AssertionError: {} is not a valid path')
def test_get_survey_scenario():
    assert get_survey_scenario()


def test_get_tax_benefit_system(tax_benefit_system, reform):
    assert get_tax_benefit_system(tax_benefit_system, reform), tax_benefit_system


def test_get_tax_benefit_system_when_tax_benefit_system(tax_benefit_system):
    assert get_tax_benefit_system(tax_benefit_system, None), tax_benefit_system


def test_get_tax_benefit_system_when_reform(reform, default_tax_benefit_system):
    assert get_tax_benefit_system(None, reform), reform(default_tax_benefit_system)


def test_get_tax_benefit_system_when_none(default_tax_benefit_system):
    assert get_tax_benefit_system(None, None), default_tax_benefit_system


def test_get_baseline_tax_benefit_system(tax_benefit_system):
    assert get_baseline_tax_benefit_system(tax_benefit_system), tax_benefit_system


def test_get_baseline_tax_benefit_system_when_none(default_tax_benefit_system):
    assert get_baseline_tax_benefit_system(None), default_tax_benefit_system

# -*- coding: utf-8 -*-


from openfisca_core.tools import assert_near


from openfisca_france.tests.base import get_cached_composed_reform, get_cached_reform
from .. import france_data_tax_benefit_system, FranceDataTaxBenefitSystem


__all__ = [
    'assert_near',
    'france_data_tax_benefit_system',
    'FranceDataTaxBenefitSystem',
    'get_cached_composed_reform',
    'get_cached_reform',
    ]

# -*- coding: utf-8 -*-

import os


from openfisca_core.reforms import Reform, compose_reforms
from openfisca_core.tools import assert_near


from openfisca_france.tests.base import get_cached_composed_reform, get_cached_reform

__all__ = [
    'assert_near',
    'france_data_tax_benefit_system',
    'FranceDataTaxBenefitSystem',
    'get_cached_composed_reform',
    'get_cached_reform',
    'skip_on_travis',
    ]


def skip_on_travis(test_function):
    use_travis = os.environ.get('USE_TRAVIS', None) == 'true'
    def pass_function():
        pass
    if use_travis:
        return pass_function
    else:
        return test_function

# Initialize a tax_benefit_system

from .. import france_data_tax_benefit_system



# -*- coding: utf-8 -*-


from __future__ import division


from openfisca_france_data.tests import base as base_survey


def test_reform_combination():
    reference_tax_benefit_system = base_survey.get_cached_reform(
        reform_key = 'inversion_directe_salaires',
        tax_benefit_system = base_survey.france_data_tax_benefit_system,
        )
    tax_benefit_system = base_survey.get_cached_reform(
        reform_key = 'ayrault_muet',
        tax_benefit_system = reference_tax_benefit_system,
        )


if __name__ == '__main__':
    import logging
    log = logging.getLogger(__name__)
    import sys
    logging.basicConfig(level = logging.INFO, stream = sys.stdout)
    test_reform_combination()

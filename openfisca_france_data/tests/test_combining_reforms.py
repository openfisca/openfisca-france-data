# -*- coding: utf-8 -*-


from openfisca_france_data import france_data_tax_benefit_system
from openfisca_france_data.reforms.inversion_directe_salaires import inversion_directe_salaires
from openfisca_france.reforms.plf2016_ayrault_muet import ayrault_muet


def test_reform_combination():
    baseline_tax_benefit_system = inversion_directe_salaires(france_data_tax_benefit_system)
    reformed_tax_benefit_system = ayrault_muet(baseline_tax_benefit_system)


if __name__ == '__main__':
    import logging
    log = logging.getLogger(__name__)
    import sys
    logging.basicConfig(level = logging.INFO, stream = sys.stdout)
    test_reform_combination()

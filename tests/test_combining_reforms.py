# -*- coding: utf-8 -*-


from toolz.functoolz import pipe  # type: ignore

from openfisca_france.reforms.plfr2014 import plfr2014  # type: ignore
from openfisca_france.reforms.plf2015 import plf2015  # type: ignore
from openfisca_france.reforms.plf2016 import plf2016  # type: ignore
from openfisca_france.reforms.plf2016_ayrault_muet import ayrault_muet  # type: ignore
from openfisca_france_data import france_data_tax_benefit_system  # type: ignore


def test_reform_combination():
    assert pipe(
        france_data_tax_benefit_system,
        plfr2014,
        plf2015,
        plf2016,
        ayrault_muet,
        )

# -*- coding: utf-8 -*-


# OpenFisca -- A versatile microsimulation software
# By: OpenFisca Team <contact@openfisca.fr>
#
# Copyright (C) 2011, 2012, 2013, 2014, 2015 OpenFisca Team
# https://github.com/openfisca
#
# This file is part of OpenFisca.
#
# OpenFisca is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# OpenFisca is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from openfisca_core.reforms import Reform, compose_reforms
from openfisca_core.tools import assert_near

#from openfisca_france.reforms import (
#    allocations_familiales_imposables,
#    inversion_directe_salaires,
#    cesthra_invalidee,
#    plf2015,
#    plf2016,
#    plf2016_ayrault_muet,
#    plfr2014,
#    trannoy_wasmer,
#    )

from openfisca_france.tests.base import get_cached_composed_reform, get_cached_reform

__all__ = [
    'assert_near',
    'france_data_tax_benefit_system',
    'FranceDataTaxBenefitSystem',
    'get_cached_composed_reform',
    'get_cached_reform',
    ]

# Initialize a tax_benefit_system

from .. import france_data_tax_benefit_system


# Reforms cache, used by long scripts like test_yaml.py

## The reforms commented haven't been adapted to the new core API yet.
#reform_list = {
#    'allocations_familiales_imposables': allocations_familiales_imposables.allocations_familiales_imposables,
#    'cesthra_invalidee': cesthra_invalidee.cesthra_invalidee,
#    'plf2016': plf2016.reform,
#    # 'ayrault_muet': plf2016_ayrault_muet.build_reform,
#    'plf2016_counterfactual': plf2016.counterfactual_reform,
#    # 'plf2016_counterfactual_2014': plf2016.build_counterfactual_2014_reform,
#    'plf2015': plf2015.plf2015,
#    # 'plfr2014': plfr2014.build_reform,
#    'trannoy_wasmer': trannoy_wasmer.trannoy_wasmer,
#    }
#
## Only use the following reform if scipy can be imported
#try:
#    import scipy
#except ImportError:
#    scipy = None
#
#if scipy is not None:
#    from openfisca_france.reforms import de_net_a_brut
#    reform_list['de_net_a_brut'] = de_net_a_brut.de_net_a_brut
#
#reform_by_full_key = {}
#
#
#
#def get_cached_composed_reform(reform_keys, tax_benefit_system):
#    full_key = '.'.join(
#        [tax_benefit_system.full_key] + reform_keys
#        if isinstance(tax_benefit_system, Reform)
#        else reform_keys
#        )
#    composed_reform = reform_by_full_key.get(full_key)
#
#    if composed_reform is None:
#        reforms = []
#        for reform_key in reform_keys:
#            assert reform_key in reform_list, \
#                'Error loading cached reform "{}" in build_reform_functions'.format(reform_key)
#            reform = reform_list[reform_key]
#            reforms.append(reform)
#        composed_reform = compose_reforms(
#            reforms = reforms,
#            tax_benefit_system = tax_benefit_system,
#            )
#        assert full_key == composed_reform.full_key
#        reform_by_full_key[full_key] = composed_reform
#    return composed_reform
#
#
#def get_cached_reform(reform_key, tax_benefit_system):
#    return get_cached_composed_reform([reform_key], tax_benefit_system)

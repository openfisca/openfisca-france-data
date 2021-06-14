from functools import reduce

from openfisca_core.reforms import Reform

from openfisca_france.entities import Famille
from openfisca_france_data import france_data_tax_benefit_system

from openfisca_france.reforms import (
    allocations_familiales_imposables,
    cesthra_invalidee,
    # inversion_directe_salaires, # We use a custom inversion_directe_salaires, not merged in the openfisca-france yet
    plf2016,
    plf2016_ayrault_muet,
    plf2015,
    plfr2014,
    trannoy_wasmer,
    )

from openfisca_france_data.reforms import (
    inversion_directe_salaires
    )

# The reforms commented haven't been adapted to the new core API yet.
reform_list = {
    'allocations_familiales_imposables': allocations_familiales_imposables.allocations_familiales_imposables,
    'cesthra_invalidee': cesthra_invalidee.cesthra_invalidee,
    'inversion_directe_salaires': inversion_directe_salaires.inversion_directe_salaires,
    'plf2016': plf2016.plf2016,
    'ayrault_muet': plf2016_ayrault_muet.ayrault_muet,
    'plf2016_counterfactual': plf2016.plf2016_counterfactual,
    'plf2016_counterfactual_2014': plf2016.plf2016_counterfactual_2014,
    'plf2015': plf2015.plf2015,
    'plfr2014': plfr2014.plfr2014,
    'trannoy_wasmer': trannoy_wasmer.trannoy_wasmer,
    }

# Only use the following reform if scipy can be imported
try:
    import scipy
except ImportError:
    scipy = None

if scipy is not None:
    from openfisca_france.reforms import de_net_a_brut
    reform_list['de_net_a_brut'] = de_net_a_brut.de_net_a_brut

reform_by_full_key = {}


def compose_reforms(reforms, tax_benefit_system):
    def compose_reforms_reducer(memo, reform):
        reformed_tbs = reform(memo)
        return reformed_tbs
    final_tbs = reduce(compose_reforms_reducer, reforms, tax_benefit_system)
    return final_tbs


def get_cached_composed_reform(reform_keys, tax_benefit_system):
    full_key = '.'.join(
        [tax_benefit_system.full_key] + reform_keys
        if isinstance(tax_benefit_system, Reform)
        else reform_keys
        )
    composed_reform = reform_by_full_key.get(full_key)

    if composed_reform is None:
        reforms = []
        for reform_key in reform_keys:
            assert reform_key in reform_list, \
                'Error loading cached reform "{}" in build_reform_functions'.format(reform_key)
            reform = reform_list[reform_key]
            reforms.append(reform)
        composed_reform = compose_reforms(
            reforms = reforms,
            tax_benefit_system = tax_benefit_system,
            )
        assert full_key == composed_reform.full_key, (full_key, composed_reform.full_key)
        reform_by_full_key[full_key] = composed_reform
    return composed_reform


def get_cached_reform(reform_key, tax_benefit_system):
    return get_cached_composed_reform([reform_key], tax_benefit_system)


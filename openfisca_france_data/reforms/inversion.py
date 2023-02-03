import numpy as np

from openfisca_france.model.base import *  # noqa analysis:ignore
from openfisca_core.reforms import Reform
from openfisca_core.taxscales import MarginalRateTaxScale, combine_tax_scales
from openfisca_france_data.felin.input_data_builder.create_variables_individuelles import create_taux_csg_remplacement
from openfisca_france import FranceTaxBenefitSystem
from openfisca_france.scenarios import init_single_entity

import logging

log = logging.getLogger(__name__)

def inversion_chomage():

    tax_benefit_system = FranceTaxBenefitSystem()
    scenario = tax_benefit_system.new_scenario()
    init_single_entity(
        scenario, 
        period='2021',  # wide: we simulate for the year
        parent1=dict(
            chomage_imposable={'2021-01': 1000},
            rfr={'2021': 11407}, # Seuil 11408 / npbtr = 1
            nbptr={'2021': 1}, 
            allocation_retour_emploi_journaliere='prive_non_cadre'},
            allegement_fillon_mode_recouvrement='progressif'
            )
        )
    simulation = scenario.new_simulation()
    create_taux_csg_remplacement(scenario.individus, scenario.period, scenario.tax_benefit_system)
    assert simulation.calculate('chomage_brut', '2021-01') == 1000
    assert simulation.calculate('csg_deductible_chomage', '2021-01') == 0
    assert simulation.calculate('csg_imposable_chomage', '2021-01') == 0
    assert simulation.calculate('crds_chomage', '2021-01') == 1

inversion_chomage()
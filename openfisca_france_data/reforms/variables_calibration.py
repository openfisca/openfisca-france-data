import numpy as np
from numpy import minimum as min_

from openfisca_france.model.base import *  # noqa analysis:ignore
from openfisca_core.reforms import Reform
from openfisca_france_data import france_data_tax_benefit_system

import logging

log = logging.getLogger(__name__)

class variables_pour_calibration(Reform):
    name = 'variables_pour_calibration'

    def apply(self):

        class age_calage(Variable):
            value_type = str
            entity = Individu
            label = "Age censuré pour calage"
            definition_period = YEAR
            unit = 'years'
            is_period_size_independent = True
            set_input = set_input_dispatch_by_period

            def formula(individu, period):
                age = individu('age', period.first_month)
                return min_(age, 100)


        class weight_individus(Variable):
            is_period_size_independent = True
            value_type = float
            entity = Individu
            label = "Poids de l'individu"
            definition_period = YEAR

            def formula(individu, period):
                if france_data_tax_benefit_system.variables["weight_familles"].is_input_variable():
                    return(individu.famille('weight_familles', period))
                elif france_data_tax_benefit_system.variables["weight_foyers"].is_input_variable():
                    return(individu.foyer_fiscal('weight_foyers', period))
                elif france_data_tax_benefit_system.variables["weight_menages"].is_input_variable():
                    return(individu.menage('weight_menages', period))
                return individu.menage('wprm', period)

        self.add_variable(age_calage)
scenario_for_calibration = variables_pour_calibration(france_data_tax_benefit_system)

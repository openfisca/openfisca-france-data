import numpy as np
from numpy import minimum as min_

from openfisca_france.model.base import *  # noqa analysis:ignore
from openfisca_core.reforms import Reform

import logging

log = logging.getLogger(__name__)
def create_calibration_tax_benefit_system(survey_scenario = None):
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

            self.add_variable(age_calage)
    scenario_for_calibration = variables_pour_calibration(survey_scenario)
    return scenario_for_calibration

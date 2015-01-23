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

import pkg_resources
import os


import openfisca_france
from openfisca_france_data.reforms import adapt_to_survey
from openfisca_france_data.calibration import Calibration
from openfisca_france_data.input_data_builders import get_input_data_frame
from openfisca_france_data.surveys import SurveyScenario


openfisca_france_data_location = pkg_resources.get_distribution('openfisca-france-data').location


def test_calibration():
    year = 2006
    input_data_frame = get_input_data_frame(year)
    TaxBenefitSystem = openfisca_france.init_country()
    tax_benefit_system = TaxBenefitSystem()
    survey_tax_benefit_system = adapt_to_survey.build_reform(tax_benefit_system)
    survey_scenario = SurveyScenario().init_from_data_frame(
        input_data_frame = input_data_frame,
        tax_benefit_system = survey_tax_benefit_system,
        year = year,
        )
    survey_scenario.initialize_weights()
    calibration = Calibration()
    calibration.set_survey_scenario(survey_scenario)
    calibration.parameters['method'] = 'linear'
    print calibration.initial_total_population
    calibration.total_population = calibration.initial_total_population * 1.123
    print calibration.total_population

    filename = os.path.join(
        openfisca_france_data_location,
        "openfisca_france_data",
        "calibrations",
        "calib_2006.csv"
        )
    calibration.set_inputs_margins_from_file(filename, 2006)
    calibration.set_parameters('invlo', 3)
    calibration.set_parameters('up', 3)
    calibration.set_parameters('method', 'logit')
    calibration.calibrate()

if __name__ == '__main__':
    import logging
    log = logging.getLogger(__name__)
    import sys
    logging.basicConfig(level = logging.INFO, stream = sys.stdout)
    test_calibration()

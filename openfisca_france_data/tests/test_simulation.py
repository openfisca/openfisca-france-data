# -*- coding: utf-8 -*-


# OpenFisca -- A versatile microsimulation software
# By: OpenFisca Team <contact@openfisca.fr>
#
# Copyright (C) 2011, 2012, 2013, 2014 OpenFisca Team
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


import os


import openfisca_france
from openfisca_france.surveys import new_simulation_from_survey_data_frame
from openfisca_france_data.surveys import SurveyCollection

current_dir = os.path.dirname(os.path.realpath(__file__))


def test_survey_simulation():
    datesim = 2006
    TaxBenefitSystem = openfisca_france.init_country()
    tax_benefit_system = TaxBenefitSystem()

    openfisca_survey_collection = SurveyCollection.load(collection = "openfisca")
    openfisca_survey = openfisca_survey_collection.surveys["openfisca_data_2006"]
    openfisca_survey_dataframe = openfisca_survey.get_values(table = "input")
    simulation = new_simulation_from_survey_data_frame(
        survey = openfisca_survey_dataframe,
        tax_benefit_system = tax_benefit_system,
        year = datesim,
        )
    simulation.calculate('revdisp')

if __name__ == '__main__':
    test_survey_simulation()

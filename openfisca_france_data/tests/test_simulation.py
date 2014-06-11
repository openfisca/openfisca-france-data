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


from openfisca_core.formulas import NaNCreationError
import openfisca_france
from openfisca_france.surveys import SurveyScenario
from openfisca_france_data.surveys import SurveyCollection
from openfisca_france_data.build_openfisca_survey_data.utils import id_formatter


current_dir = os.path.dirname(os.path.realpath(__file__))


def get_input_data_frame(year):
    openfisca_survey_collection = SurveyCollection.load(collection = "openfisca")
    openfisca_survey = openfisca_survey_collection.surveys["openfisca_data_{}".format(year)]
    input_data_frame = openfisca_survey.get_values(table = "input")
    input_data_frame.reset_index(inplace = True)
    return input_data_frame

# TODO, move to SurveyScenario
def filter_input_data_frame(data_frame, filter_entity = None, filter_index = None, simulation = None):
    symbol = filter_entity.symbol
    other_symbols = [entity.symbol for entity in simulation.entity_by_key_singular.values()]
    other_symbols = other_symbols.remove('ind')
    person_index = dict()
    if symbol is 'ind':
        selection = data_frame.index.isin(filter_index)
        person_index['ind'] = data_frame.index[selection].copy()
    else:
        selection = data_frame['id' + symbol].isin(filter_index)
        other_symbols.remove(symbol)
        person_index[symbol] = data_frame.index[selection].copy()

    final_selection_index = person_index[symbol]  # initialisation
    for other_symbol in other_symbols:
        other_symbol_index = data_frame['id' + other_symbol][person_index[symbol]].unique()
        person_index[other_symbol] = data_frame.index[data_frame['id' + other_symbol].isin(other_symbol_index)].copy()
        final_selection_index += person_index[other_symbol]

    data_frame = data_frame.iloc[final_selection_index].copy().reset_index()
    for entity_id in ['id' + entity.symbol for entity in simulation.entity_by_key_singular.values()]:
            data_frame = id_formatter(data_frame, entity_id)
    return data_frame


def test_survey_simulation():
    year = 2006
    input_data_frame = get_input_data_frame(year)
    TaxBenefitSystem = openfisca_france.init_country()
    tax_benefit_system_class = TaxBenefitSystem
    survey_scenario = SurveyScenario().init_from_data_frame(
        input_data_frame = input_data_frame,
        tax_benefit_system_class = tax_benefit_system_class,
        year = year,
        )
    simulation = survey_scenario.new_simulation()
    try:
        from pandas import DataFrame
        revdisp = DataFrame({"revdisp": simulation.calculate('revdisp')})
    except NaNCreationError as error:
        index = error.index
        entity = error.entity
        column_name = error.column_name
        input_data_frame_debug = filter_input_data_frame(
            simulation.input_data_frame,
            entity,
            index[:10],
            )
        survey_scenario_debug = SurveyScenario()
        simulation_debug = survey_scenario_debug.new_simulation(
            debug = True,
            input_data_frame = input_data_frame_debug,
            tax_benefit_system_class = tax_benefit_system_class,
            year = year,
            )
        simulation_debug.calculate(column_name)

    print revdisp.info()
    print 'finished'


def test_weights_building():
    year = 2006
    input_data_frame = get_input_data_frame(year)
    TaxBenefitSystem = openfisca_france.init_country()
    tax_benefit_system_class = TaxBenefitSystem
    survey_scenario = SurveyScenario().init_from_data_frame(
        input_data_frame = input_data_frame,
        tax_benefit_system_class = tax_benefit_system_class,
        year = year,
        )
    simulation = survey_scenario.new_simulation()


if __name__ == '__main__':
    import logging
    log = logging.getLogger(__name__)
    import sys
    logging.basicConfig(level = logging.INFO, stream = sys.stdout)
#    test_survey_simulation()
    test_weights_building()

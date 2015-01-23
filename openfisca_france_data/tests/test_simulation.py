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


from openfisca_core.formulas import NaNCreationError
import openfisca_france


from openfisca_france_data.input_data_builders import get_input_data_frame
from openfisca_france_data.input_data_builders.fake_openfisca_data_builder import get_fake_input_data_frame
from openfisca_france_data.surveys import SurveyScenario


def test_fake_survey_simulation():
    year = 2006
    input_data_frame = get_fake_input_data_frame(year)
    survey_scenario = SurveyScenario().init_from_data_frame(
        input_data_frame = input_data_frame,
        year = year,
        )
    simulation = survey_scenario.new_simulation()
    simulation.calculate('revdisp')


def test_survey_simulation():
    year = 2006
    input_data_frame = get_input_data_frame(year)
    survey_scenario = SurveyScenario().init_from_data_frame(
        input_data_frame = input_data_frame,
        year = year,
        )
    simulation = survey_scenario.new_simulation()
    try:
        from pandas import DataFrame
        simulation.calculate('revdisp')
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
            tax_benefit_system = tax_benefit_system,
            year = year,
            )
        simulation_debug.calculate(column_name)

    data_frame_by_entity_key_plural = dict(
        individus = DataFrame(
            dict([(name, simulation.calculate(name)) for name in [
                'idmen',
                'quimen',
                'idfoy',
                'quifoy',
                'idfam',
                'quifam',
                'age',
                'champm_ind',
                'sal',
                'salnet',
                'txtppb',
                # salsuperbrut # TODO bug in 2006
                ]])
            ),
        menages = DataFrame(
            dict([(name, simulation.calculate(name)) for name in [
                'revdisp'
                ]])
            ),
        )

    return data_frame_by_entity_key_plural


def test_weights_building():
    year = 2006
    input_data_frame = get_input_data_frame(year)
    survey_scenario = SurveyScenario().init_from_data_frame(
        input_data_frame = input_data_frame,
        year = year,
        )
    survey_scenario.new_simulation()


if __name__ == '__main__':
    import logging
    log = logging.getLogger(__name__)
    import sys
    logging.basicConfig(level = logging.INFO, stream = sys.stdout)
    test_fake_survey_simulation()

    df_by_entity = test_survey_simulation()
    df_i = df_by_entity['individus']
    df_m = df_by_entity['menages']
    print df_i
    print df_m
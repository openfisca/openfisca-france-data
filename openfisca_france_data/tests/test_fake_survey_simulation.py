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


import pandas


from openfisca_france_data.calibration import Calibration
from openfisca_france_data.input_data_builders.fake_openfisca_data_builder import get_fake_input_data_frame
from openfisca_france_data.surveys import SurveyScenario


def test_fake_survey_simulation():
    year = 2006
    input_data_frame = get_fake_input_data_frame(year)
    assert (input_data_frame.sal.loc[0:1] == 20000).all()
    survey_scenario = SurveyScenario().init_from_data_frame(
        input_data_frame = input_data_frame,
        used_as_input_variables = ['sal', 'cho', 'rst'],
        year = year,
        )
    assert (survey_scenario.input_data_frame.sal.loc[0:1] == 20000).all()
    simulation = survey_scenario.new_simulation()

    sal = simulation.calculate('sal')
    print sal[0:1] == 20000

    data_frame_by_entity_key_plural = dict(
        individus = pandas.DataFrame(
            dict([(name, simulation.calculate(name)) for name in [
                'idmen',
                'quimen',
                'idfoy',
                'quifoy',
                'idfam',
                'quifam',
                'age',
                'champm_individus',
                'sal',
                'salaire_net',
                'txtppb',
                # salsuperbrut # TODO bug in 2006
                ]])
            ),
        foyers_fiscaux = pandas.DataFrame(
            dict([(name, simulation.calculate(name)) for name in [
                'impo'
                ]])
            ),
        menages = pandas.DataFrame(
            dict([(name, simulation.calculate(name)) for name in [
                'revdisp'
                ]])
            ),
        )

    return data_frame_by_entity_key_plural


def test_fake_calibration():
    year = 2006
    input_data_frame = get_fake_input_data_frame(year)
    survey_scenario = SurveyScenario().init_from_data_frame(
        input_data_frame = input_data_frame,
        used_as_input_variables = ['sal', 'cho', 'rst'],
        year = year,
        )
    survey_scenario.new_simulation()
    survey_scenario.initialize_weights()
    print survey_scenario.weight_column_name_by_entity_key_plural
    print survey_scenario.simulation.calculate("wprm")

    calibration = Calibration()
    calibration.set_survey_scenario(survey_scenario)
    calibration.parameters['method'] = 'linear'
    print calibration.initial_total_population
    calibration.total_population = calibration.initial_total_population * 1.123
    print calibration.total_population

    # calibration.set_inputs_margins_from_file(filename, 2006)
    calibration.set_parameters('invlo', 3)
    calibration.set_parameters('up', 3)
    calibration.set_parameters('method', 'logit')
    calibration.calibrate()
    calibration.set_calibrated_weights()
    return calibration

if __name__ == '__main__':
    import logging
    log = logging.getLogger(__name__)
    import sys
    logging.basicConfig(level = logging.INFO, stream = sys.stdout)

#    df_by_entity = test_fake_survey_simulation()
#    df_i = df_by_entity['individus']
#    df_f = df_by_entity['foyers_fiscaux']
#    df_m = df_by_entity['menages']
#    print df_i
#    print df_m
    calibration = test_fake_calibration()
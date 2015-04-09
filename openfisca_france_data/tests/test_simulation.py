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


from openfisca_france_data.input_data_builders import get_input_data_frame
from openfisca_france_data.surveys import SurveyScenario


def test_survey_simulation():
    year = 2009
    input_data_frame = get_input_data_frame(year)
    survey_scenario = SurveyScenario().init_from_data_frame(
        input_data_frame = input_data_frame,
        used_as_input_variables = ['sal', 'cho', 'rst', 'age_en_mois', 'smic55'],
        year = year,
        )
    simulation = survey_scenario.new_simulation()

    data_frame_by_entity_key_plural = dict(
        individus = pandas.DataFrame(
            dict([(name, simulation.calculate_add(name)) for name in [
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
                # 'smic55',
                'txtppb',
                # salsuperbrut # TODO bug in 2006
                ]])
            ),
        familles = pandas.DataFrame(
            dict([(name, simulation.calculate_add(name)) for name in [
                'af_nbenf',
                'af',
                'weight_familles',
                ]])
            ),

        menages = pandas.DataFrame(
            dict([(name, simulation.calculate(name)) for name in [
                'revdisp',
                ]])
            ),
        )

    assert (data_frame_by_entity_key_plural['familles'].weight_familles
        * data_frame_by_entity_key_plural['familles'].af).sum() / 1e9 > 10

    return data_frame_by_entity_key_plural, simulation


def test_weights_building():
    year = 2009
    input_data_frame = get_input_data_frame(year)
    survey_scenario = SurveyScenario().init_from_data_frame(
        input_data_frame = input_data_frame,
        used_as_input_variables = ['sal', 'cho', 'rst', 'age_en_mois'],
        year = year,
        )
    survey_scenario.new_simulation()
    return survey_scenario.simulation

if __name__ == '__main__':
    import logging
    import time
    log = logging.getLogger(__name__)
    import sys
    logging.basicConfig(level = logging.INFO, stream = sys.stdout)

    start = time.time()
    data_frame_by_entity_key_plural, simulation = test_survey_simulation()
    data_frame_individus = data_frame_by_entity_key_plural['individus']
    data_frame_menages = data_frame_by_entity_key_plural['menages']
    data_frame_familles = data_frame_by_entity_key_plural['familles']

    ra_rsa = simulation.calculate('ra_rsa', "2009-01")
    salaire_net = simulation.calculate('salaire_net', "2009-01")

#    simulation = test_weights_building()
#    from openfisca_core.periods import period
#
#    print simulation.calculate('age_en_mois', period = period("2009"))
#    print simulation.calculate('age_en_mois', period = period("2009-01"))
#    print simulation.calculate('age_en_mois', period = period("2009-02"))
#    print simulation.calculate('age_en_mois', period = period("2009-03"))
#
#    age_en_mois = simulation.get_or_new_holder('age_en_mois')
#
#    age_en_mois.set_input("2009-01", 25)



    print time.time() - start

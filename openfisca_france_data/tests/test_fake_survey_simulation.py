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


from __future__ import division


import os


import numpy
import pandas


from openfisca_core.tools import assert_near
from openfisca_france_data.calibration import Calibration
from openfisca_france_data.input_data_builders import get_input_data_frame
from openfisca_france_data.surveys import SurveyScenario


current_dir = os.path.dirname(os.path.realpath(__file__))
hdf5_file_realpath = os.path.join(current_dir, 'data_files', 'fake_openfisca_input_data.h5')


def build_by_extraction(year = None):
    assert year is not None
    df = get_input_data_frame(year)
    output = df.ix[0:1]
    for symbol in ['fam', 'foy', 'men']:
        output['id{}_original'.format(symbol)] = output['id{}'.format(symbol)]
    output.loc[0, 'sali'] = 20000
    output.loc[1, 'sali'] = 10000
    output['wprm'] = 100
    store = pandas.HDFStore(hdf5_file_realpath)
    store.put(str(year), output)
    store.close()


def get_fake_input_data_frame(year = None):
    assert year is not None
    store = pandas.HDFStore(hdf5_file_realpath)
    input_data_frame = store.select(str(year))
    input_data_frame.rename(
        columns = dict(sali = 'sal', choi = 'cho', rsti = 'rst'),
        inplace = True,
        )
    input_data_frame.sal[0] = 20000
    input_data_frame.sal[1] = 10000

    input_data_frame.reset_index(inplace = True)
    return input_data_frame


def test_fake_survey_simulation():
    year = 2006
    input_data_frame = get_fake_input_data_frame(year)

    assert input_data_frame.sal.loc[0] == 20000
    assert input_data_frame.sal.loc[1] == 10000

    survey_scenario = SurveyScenario().init_from_data_frame(
        input_data_frame = input_data_frame,
        used_as_input_variables = ['sal', 'cho', 'rst', 'age_en_mois', 'age'],
        year = year,
        )
    assert (survey_scenario.input_data_frame.sal.loc[0] == 20000).all()
    assert (survey_scenario.input_data_frame.sal.loc[1] == 10000).all()

    simulation = survey_scenario.new_simulation()

    sal = simulation.calculate('sal')
    assert (sal[0:1] == 20000).all()
    age = simulation.calculate('age')
    assert age[0] == 77
    assert age[1] == 37
    age_en_mois = simulation.calculate('age_en_mois')
    assert age_en_mois[0] == 924
    assert age_en_mois[1] == 444

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


def create_fake_calibration():
    year = 2006
    input_data_frame = get_fake_input_data_frame(year)
    survey_scenario = SurveyScenario().init_from_data_frame(
        input_data_frame = input_data_frame,
        used_as_input_variables = ['sal', 'cho', 'rst', 'age'],
        year = year,
        )
    survey_scenario.new_simulation()
    calibration = Calibration(survey_scenario = survey_scenario)
    calibration.set_survey_scenario(survey_scenario)
    calibration.set_parameters('invlo', 3)
    calibration.set_parameters('up', 3)
    calibration.set_parameters('method', 'logit')
    return calibration


def test_fake_calibration_float():
    calibration = create_fake_calibration()
    survey_scenario = calibration.survey_scenario
    calibration.total_population = calibration.initial_total_population * 1.123

    revdisp_target = 7e6
    calibration.set_target_margin('revdisp', revdisp_target)

    calibration.calibrate()
    calibration.set_calibrated_weights()
    simulation = survey_scenario.simulation
    assert_near(
        simulation.calculate("wprm").sum(),
        calibration.total_population,
        absolute_error_margin = None,
        relative_error_margin = .00001
        )
    assert_near(
        (simulation.calculate('revdisp') * simulation.calculate("wprm")).sum(),
        revdisp_target,
        absolute_error_margin = None,
        relative_error_margin = .00001
        )

    return calibration


def test_fake_calibration_age():
    calibration = create_fake_calibration()
    survey_scenario = calibration.survey_scenario
    calibration.total_population = calibration.initial_total_population * 1.123
    calibration.set_target_margin('age', [95, 130])

    calibration.calibrate()
    calibration.set_calibrated_weights()
    simulation = survey_scenario.simulation
    assert_near(
        simulation.calculate("wprm").sum(),
        calibration.total_population,
        absolute_error_margin = None,
        relative_error_margin = .00001
        )
    age = survey_scenario.simulation.calculate('age'),
    wprm = survey_scenario.simulation.calculate('wprm')

    for category, target in calibration.margins_by_name['age']['target'].iteritems():
        assert_near(
            ((age == category) * wprm).sum() / wprm.sum(),
            target / numpy.sum(calibration.margins_by_name['age']['target'].values()),
            absolute_error_margin = None,
            relative_error_margin = .00001
            )
    return calibration


if __name__ == '__main__':
    import logging
    log = logging.getLogger(__name__)
    import sys
    logging.basicConfig(level = logging.INFO, stream = sys.stdout)

#    year = 2006
#    build_by_extraction(year = year)
#    df = get_fake_input_data_frame(year = year)

    df_by_entity = test_fake_survey_simulation()
    df_i = df_by_entity['individus']
    df_f = df_by_entity['foyers_fiscaux']
    df_m = df_by_entity['menages']
    print df_i
    print df_m
#    calibration = test_fake_calibration_age()
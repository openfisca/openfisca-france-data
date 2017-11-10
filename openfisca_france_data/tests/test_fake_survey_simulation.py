# -*- coding: utf-8 -*-


from __future__ import division

import numpy
import os
import pandas

from openfisca_core.tools import assert_near
import openfisca_france.tests.base as france_base
from openfisca_france_data.tests import base
from openfisca_france_data.erfs.scenario import ErfsSurveyScenario
from openfisca_survey_manager.calibration import Calibration
from openfisca_survey_manager.survey_collections import SurveyCollection


current_dir = os.path.dirname(os.path.realpath(__file__))
hdf5_file_realpath = os.path.join(current_dir, 'data_files', 'fake_openfisca_input_data.h5')
csv_file_realpath = os.path.join(current_dir, 'data_files', 'fake_openfisca_input_data.csv')


def get_input_data_frame(year):
    openfisca_survey_collection = SurveyCollection.load(collection = "openfisca")
    openfisca_survey = openfisca_survey_collection.get_survey("openfisca_data_{}".format(year))
    input_data_frame = openfisca_survey.get_values(table = "input").reset_index(drop = True)
    input_data_frame.rename(
        columns = dict(
            alr = 'pensions_alimentaires_percues',
            choi = 'chomage_imposable',
            cho_ld = 'chomeur_longue_duree',
            fra = 'frais_reels',
            rsti = 'retraite_imposable',
            sali = 'salaire_imposable',
            ),
        inplace = True,
        )
    return input_data_frame


def build_by_extraction(year = None):
    assert year is not None
    df = get_input_data_frame(year)
    output = df.ix[0:1]
    for symbol in ['fam', 'foy', 'men']:
        output['id{}_original'.format(symbol)] = output['id{}'.format(symbol)]
    output.loc[0, 'sali'] = 20000
    output.loc[1, 'sali'] = 10000
    output['wprm'] = 100
    output.to_csv(csv_file_realpath)
    output.to_hdf(hdf5_file_realpath)


def build_csv_from_hdf(year):
    output = pandas.read_hdf(hdf5_file_realpath, key = str(year))
    output.to_csv(csv_file_realpath)


def get_fake_input_data_frame(year = None):
    assert year is not None
    try:
        input_data_frame = pandas.read_hdf(hdf5_file_realpath, key = str(year))
    except:
        input_data_frame = pandas.read_csv(csv_file_realpath)
    input_data_frame.rename(
        columns = dict(sali = 'salaire_imposable', choi = 'chomage_imposable', rsti = 'retraite_imposable'),
        inplace = True,
        )
    input_data_frame.loc[0, 'salaire_imposable'] = 20000
    input_data_frame.loc[1, 'salaire_imposable'] = 10000
    for idx in [2, 6]:
        input_data_frame.loc[idx] = input_data_frame.loc[1].copy()
        input_data_frame.loc[idx, 'salaire_imposable'] = 0
        input_data_frame.loc[idx, 'quifam'] = idx
        input_data_frame.loc[idx, 'quifoy'] = idx
        input_data_frame.loc[idx, 'quimen'] = idx
        if idx < 4:
            input_data_frame.loc[idx, 'age'] = 10
        else:
            input_data_frame.loc[idx, 'age'] = 24
            input_data_frame.loc[idx, 'age'] = 24

    input_data_frame.reset_index(inplace = True)
    return input_data_frame


def test_fake_survey_simulation():
    year = 2006
    input_data_frame = get_fake_input_data_frame(year)
    assert input_data_frame.salaire_imposable.loc[0] == 20000
    assert input_data_frame.salaire_imposable.loc[1] == 10000

    survey_scenario = ErfsSurveyScenario().init_from_data_frame(
        input_data_frame = input_data_frame,
        year = year,
        )
    assert (survey_scenario.input_data_frame.salaire_imposable.loc[0] == 20000).all()
    assert (survey_scenario.input_data_frame.salaire_imposable.loc[1] == 10000).all()

    simulation = survey_scenario.new_simulation()

    salaire_imposable = simulation.calculate('salaire_imposable')
    assert (salaire_imposable[0:1] == 20000).all()
    assert (salaire_imposable[1:2] == 10000).all()
    age = simulation.calculate('age')
    assert age[0] == 77
    assert age[1] == 37
    age_en_mois = simulation.calculate('age_en_mois')
    assert age_en_mois[0] == 924
    assert age_en_mois[1] == 444
    sal_2003 = simulation.calculate_add('salaire_imposable', period = "2003")
    sal_2004 = simulation.calculate_add('salaire_imposable', period = "2004")
    sal_2005 = simulation.calculate_add('salaire_imposable', period = "2005")
    sal_2006 = simulation.calculate_add('salaire_imposable', period = "2006")

    assert (sal_2003 == 0).all()
    assert (sal_2004 == sal_2006).all()
    assert (sal_2005 == sal_2006).all()
    import itertools

    for year, month in itertools.product(range(2003, 2004), range(1, 13)):
        assert (simulation.calculate_add('salaire_imposable', period = "{}-{}".format(year, month)) == 0).all()

    for year, month in itertools.product(range(2004, 2007), range(1, 13)):
        # print "{}-{}".format(year, month)
        # print simulation.calculate_add_divide('salaire_imposable', period = "{}-{}".format(year, month))
        # print sal_2006 / 12
        assert (simulation.calculate('salaire_imposable', period = "{}-{}".format(year, month)) == sal_2006 / 12).all()

    create_data_frame_by_entity = survey_scenario.create_data_frame_by_entity(
        variables = [
            'age',
            'activite',
            'rsa_base_ressources_i',
            'menage_ordinaire_individus',
            'salaire_imposable',
            'salaire_net',
            'autonomie_financiere',
            'txtppb',
            'af_nbenf',
            'af',
            'af_majoration_enfant',
            'af_age_aine',
            'rsa_base_ressources',
            'rsa',
            'aspa',
            'aide_logement_montant_brut',
            'weight_familles',
            'revdisp',
            'impo',
            ]
        )
    return data_frame_by_entity_key_plural, simulation


def create_fake_calibration():
    year = 2006
    input_data_frame = get_fake_input_data_frame(year)
    survey_scenario = ErfsSurveyScenario().init_from_data_frame(
        input_data_frame = input_data_frame,
        year = year,
        )
    survey_scenario.new_simulation()
    calibration = Calibration(survey_scenario = survey_scenario)
    calibration.set_parameters('invlo', 3)
    calibration.set_parameters('up', 3)
    calibration.set_parameters('method', 'logit')
    return calibration


def test_fake_calibration_float():
    calibration = create_fake_calibration()
    calibration.total_population = calibration.initial_total_population * 1.123

    revdisp_target = 7e6
    calibration.set_target_margin('revdisp', revdisp_target)

    calibration.calibrate()
    calibration.set_calibrated_weights()
    simulation = calibration.survey_scenario.simulation
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
    weight_individus = survey_scenario.simulation.calculate('weight_individus')

    for category, target in calibration.margins_by_variable['age']['target'].iteritems():
        assert_near(
            ((age == category) * weight_individus).sum() / weight_individus.sum(),
            target / numpy.sum(calibration.margins_by_variable['age']['target'].values()),
            absolute_error_margin = None,
            relative_error_margin = .00001
            )
    return calibration


def test_reform():
    year = 2006
    input_data_frame = get_fake_input_data_frame(year)
    # On ne garde que les deux parents
    input_data_frame.loc[0, 'salaire_imposable'] = 20000
    input_data_frame.loc[1, 'salaire_imposable'] = 18000
    input_data_frame = input_data_frame.loc[0:1].copy()

    reform = france_base.get_cached_reform(
        reform_key = 'plf2015',
        tax_benefit_system = base.france_data_tax_benefit_system,
        )

    survey_scenario = ErfsSurveyScenario().init_from_data_frame(
        input_data_frame = input_data_frame,
        tax_benefit_system = reform,
        baseline_tax_benefit_system = base.france_data_tax_benefit_system,
        year = 2013,
        )
    baseline_simulation = survey_scenario.new_simulation(use_baseline = True)
    reform_simulation = survey_scenario.new_simulation()

    assert 'weight_individus' in reform_simulation.tax_benefit_system.column_by_name
    assert 'weight_individus' in baseline_simulation.tax_benefit_system.column_by_name

    error_margin = 1
    assert_near(baseline_simulation.calculate('irpp'), [-10124, -869], error_margin)
    assert_near(reform_simulation.calculate('irpp'), [-10118, -911.4 + (1135 - 911.4)], error_margin)
    # -911.4 + (1135 - 911.4) = -686.8

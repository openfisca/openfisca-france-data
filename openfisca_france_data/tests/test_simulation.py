# -*- coding: utf-8 -*-


from openfisca_france_data.erfs.scenario import ErfsSurveyScenario
from openfisca_france_data.erfs_fpr.scenario import ErfsFprSurveyScenario

import logging


log = logging.getLogger(__name__)


variables = [
    'aspa',
    'aide_logement_montant_brut',
    'idmen',
    'quimen',
    'idfoy',
    'quifoy',
    'idfam',
    'quifam',
    'age',
    'activite',
    'champm_individus',
    'pensions_alimentaires_percues',
    'salaire_imposable',
    'salaire_net',
    'autonomie_financiere',
    'af_nbenf',
    'af',
    'rsa_base_ressources',
    'rsa',
    'weight_familles',
    'revdisp',
    ]


def loose_check(data_frame_by_entity_key_plural):
    positive_variables = [
        'aspa',
        'aide_logement_montant_brut',
        'idmen',
        'quimen',
        'idfoy',
        'quifoy',
        'idfam',
        'quifam',
        'activite',
        'champm_individus',
        'pensions_alimentaires_percues',
        'salaire_imposable',
        'salaire_net',
        'autonomie_financiere',
        'af_nbenf',
        'af',
        'rsa_base_ressources',
        'rsa',
        'weight_familles',
        'revdisp',
        ]
    strictly_positive_sum_variables = positive_variables
    strictly_positive_sum_variables.remove('aide_logement_montant_brut')

    for entity, data_frame in data_frame_by_entity_key_plural.iteritems():
        for variable in data_frame.columns:
            if variable in positive_variables:
                assert (data_frame[variable] >= 0).all(), "Variable {} of entity {} is not always positive".format(
                    variable, entity)
            if variable in strictly_positive_sum_variables:
                assert (data_frame[variable]).sum(), "Variable {} sum of entity {} is not strictly positive".format(
                    variable, entity)


def test_erfs_fpr_survey_simulation(year = 2012):
    try:
        survey_scenario = ErfsFprSurveyScenario.create(year = year)
    except AssertionError as e:
        print(e)
        return
    data_frame_by_entity_key_plural = survey_scenario.create_data_frame_by_entity_key_plural(
        variables = variables,
        )
    loose_check(data_frame_by_entity_key_plural)
    return data_frame_by_entity_key_plural


def test_erfs_fpr_survey_simulation_with_rebuild(year = 2012):
    try:
        survey_scenario = ErfsFprSurveyScenario.create(year = year, rebuild_input_data = True)
    except AssertionError as e:
        print(e)
        return
    data_frame_by_entity_key_plural = survey_scenario.create_data_frame_by_entity_key_plural(
        variables = variables,
        )
    loose_check(data_frame_by_entity_key_plural)
    return data_frame_by_entity_key_plural


def test_erfs_survey_simulation(year = 2009):
    try:
        survey_scenario = ErfsSurveyScenario.create(year = year)
    except AssertionError as e:
        print(e)
        return

    data_frame_by_entity_key_plural = survey_scenario.create_data_frame_by_entity_key_plural(
        variables = variables,
        )
    loose_check(data_frame_by_entity_key_plural)
    assert (
        data_frame_by_entity_key_plural['familles'].weight_familles * data_frame_by_entity_key_plural['familles'].af
        ).sum() / 1e9 > 10

    return data_frame_by_entity_key_plural


def test_weights_building():
    year = 2012
    survey_scenario = ErfsFprSurveyScenario.create(year = year)
    survey_scenario.new_simulation()
    return survey_scenario.simulation

if __name__ == '__main__':
    import time
    log = logging.getLogger(__name__)
    import sys
    logging.basicConfig(level = logging.INFO, stream = sys.stdout)
    start = time.time()
    data_frame_by_entity_key_plural = test_erfs_fpr_survey_simulation(year = 2012)
    data_frame_individus = data_frame_by_entity_key_plural['individus']
    data_frame_menages = data_frame_by_entity_key_plural['menages']
    data_frame_familles = data_frame_by_entity_key_plural['familles']
    print(time.time() - start)

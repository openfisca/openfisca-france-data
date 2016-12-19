# -*- coding: utf-8 -*-


from openfisca_france_data.erfs.scenario import ErfsSurveyScenario
from openfisca_france_data.erfs_fpr.scenario import ErfsFprSurveyScenario

import logging


log = logging.getLogger(__name__)


variables = [
    'activite',
    'af_nbenf',
    'af',
    'age',
    'aide_logement_montant_brut',
    'aspa',
    'autonomie_financiere',
    'champm_individus',
    'idfam',
    'idfoy',
    'idmen',
    'minimum_vieillesse',
    'nbptr',
    'pensions_alimentaires_percues',
    'quifam',
    'quifoy',
    'quimen',
    'revdisp',
    'rsa_base_ressources',
    'rsa',
    'salaire_imposable',
    'salaire_net',
    'weight_familles',
    ]


def loose_check(create_data_frame_by_entity):
    positive_variables = [
        'activite',
        'af_nbenf',
        'af',
        'aide_logement_montant_brut',
        'aspa',
        'autonomie_financiere',
        'champm_individus',
        'idfam',
        'idfoy',
        'idmen',
        'minimum_vieillesse',
        'nbptr',
        'pensions_alimentaires_percues',
        'quifam',
        'quifoy',
        'quimen',
        # 'revdisp',  can be negative if rag, ric or rnc are negative
        'rsa_base_ressources',
        'rsa',
        'salaire_imposable',
        'salaire_net',
        'weight_familles',
        ]
    strictly_positive_sum_variables = positive_variables
    strictly_positive_sum_variables.remove('aide_logement_montant_brut')

    for entity, data_frame in create_data_frame_by_entity.iteritems():
        for variable in data_frame.columns:
            if variable in positive_variables:
                assert (data_frame[variable] >= 0).all(), \
                    "Variable {} of entity {} is not always positive. {} values are negative. \n {}".format(
                        variable,
                        entity,
                        (data_frame[variable] < 0).sum(),
                        data_frame.loc[data_frame[variable] < 0, variable].value_counts(dropna = False)
                        )
            if variable in strictly_positive_sum_variables:
                assert (data_frame[variable]).sum(), "Variable {} sum of entity {} is not strictly positive".format(
                    variable, entity)


def test_erfs_fpr_survey_simulation(year = 2012):
    try:
        survey_scenario = ErfsFprSurveyScenario.create(year = year)
    except AssertionError as e:
        print(e)
        return
    create_data_frame_by_entity = survey_scenario.create_data_frame_by_entity(
        variables = variables,
        )
    loose_check(create_data_frame_by_entity)
    return survey_scenario, create_data_frame_by_entity


def test_erfs_fpr_survey_simulation_with_rebuild(year = 2012):
    try:
        survey_scenario = ErfsFprSurveyScenario.create(year = year, rebuild_input_data = True)
    except AssertionError as e:
        print(e)
        return
    create_data_frame_by_entity = survey_scenario.create_data_frame_by_entity(
        variables = variables,
        )
    loose_check(create_data_frame_by_entity)
    return survey_scenario, create_data_frame_by_entity


def test_erfs_survey_simulation(year = 2009):
    try:
        survey_scenario = ErfsSurveyScenario.create(year = year)
    except AssertionError as e:
        print(e)
        return

    create_data_frame_by_entity = survey_scenario.create_data_frame_by_entity(
        variables = variables,
        )
    loose_check(create_data_frame_by_entity)
    assert (
        create_data_frame_by_entity['familles'].weight_familles * create_data_frame_by_entity['familles'].af
        ).sum() / 1e9 > 10

    return create_data_frame_by_entity


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
    survey_scenario, create_data_frame_by_entity = test_erfs_fpr_survey_simulation(year = 2012)
    data_frame_familles = create_data_frame_by_entity['famille']
    data_frame_foyers_fiscaux = create_data_frame_by_entity['foyer_fiscal']
    data_frame_individus = create_data_frame_by_entity['individu']
    data_frame_menages = create_data_frame_by_entity['menage']
    print(time.time() - start)

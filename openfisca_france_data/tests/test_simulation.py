# -*- coding: utf-8 -*-


from openfisca_france_data.surveys import ErfsSurveyScenario, ErfsFprSurveyScenario


def test_erfs_fpr_survey_simulation(year = 2012):
    survey_scenario = ErfsFprSurveyScenario.create(year = year)
    data_frame_by_entity_key_plural = survey_scenario.create_data_frame_by_entity_key_plural(
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
        )

    return data_frame_by_entity_key_plural


def test_survey_simulation():
    year = 2009
    survey_scenario = ErfsSurveyScenario.create(year = year)
    data_frame_by_entity_key_plural = survey_scenario.create_data_frame_by_entity_key_plural(
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
        )
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
    import logging
    import time
    log = logging.getLogger(__name__)
    import sys
    logging.basicConfig(level = logging.INFO, stream = sys.stdout)

    start = time.time()

    data_frame_by_entity_key_plural, simulation = test_erfs_fpr_survey_simulation(year = 2012)
    data_frame_individus = data_frame_by_entity_key_plural['individus']
    data_frame_menages = data_frame_by_entity_key_plural['menages']
    data_frame_familles = data_frame_by_entity_key_plural['familles']

    print(time.time() - start)

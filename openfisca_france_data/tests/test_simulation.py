# -*- coding: utf-8 -*-


from openfisca_france_data.input_data_builders import get_input_data_frame, get_erfs_fpr_input_data_frame
from openfisca_france_data.surveys import SurveyScenario


def test_erfs_fpr_survey_simulation(year = 2012):
    input_data_frame = get_erfs_fpr_input_data_frame(year)
    survey_scenario = SurveyScenario().init_from_data_frame(
        input_data_frame = input_data_frame,
        year = year,
        )
    simulation = survey_scenario.new_simulation(trace = True)
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
            'rsa_base_ressources_i',
            'champm_individus',
            'pensions_alimentaires_percues',
            'salaire_imposable',
            'salaire_net',
            'autonomie_financiere',
            'txtppb',
            'af_nbenf',
            'af',
            'rsa_base_ressources',
            'rsa',
            'rstnet',
            'weight_familles',
            'revdisp',
            ]
        )

    assert (
        data_frame_by_entity_key_plural['familles'].weight_familles * data_frame_by_entity_key_plural['familles'].af
        ).sum() / 1e9 > 10

    return data_frame_by_entity_key_plural, simulation


def test_survey_simulation():
    year = 2009
    input_data_frame = get_input_data_frame(year)
    survey_scenario = SurveyScenario().init_from_data_frame(
        input_data_frame = input_data_frame,
        year = year,
        )
    simulation = survey_scenario.new_simulation(trace = True)
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
            'rsa_base_ressources_i',
            'champm_individus',
            'pensions_alimentaires_percues',
            'salaire_imposable',
            'salaire_net',
            'autonomie_financiere',
            'txtppb',
            'af_nbenf',
            'af',
            'rsa_base_ressources',
            'rsa',
            'rstnet',
            'weight_familles',
            'revdisp',
            ]
        )

    assert (
        data_frame_by_entity_key_plural['familles'].weight_familles * data_frame_by_entity_key_plural['familles'].af
        ).sum() / 1e9 > 10

    return data_frame_by_entity_key_plural, simulation


def test_weights_building():
    year = 2009
    input_data_frame = get_input_data_frame(year)
    survey_scenario = SurveyScenario().init_from_data_frame(
        input_data_frame = input_data_frame,
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
    # year = 2009
    # input_data_frame = get_input_data_frame(year)
    data_frame_by_entity_key_plural, simulation = test_erfs_fpr_survey_simulation(year = 2012)
    data_frame_individus = data_frame_by_entity_key_plural['individus']
    data_frame_menages = data_frame_by_entity_key_plural['menages']
    data_frame_familles = data_frame_by_entity_key_plural['familles']
    # ra_rsa = simulation.calculate('ra_rsa', "2009-01")
    # salaire_net = simulation.calculate('salaire_net', "2009-01")
    print time.time() - start

# -*- coding: utf-8 -*-


from openfisca_france_data.erfs.scenario import ErfsSurveyScenario
from openfisca_france_data.erfs_fpr.scenario import ErfsFprSurveyScenario
from openfisca_france_data.tests import base as base_survey


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
    'menage_ordinaire_individus',
    'minimum_vieillesse',
    'nbptr',
    'pensions_alimentaires_percues',
    'revenu_disponible',
    'rsa_base_ressources',
    'rsa',
    'salaire_imposable',
    'salaire_net',
    'weight_familles',
    ]


def loose_check(data_frame_by_entity):
    positive_variables = [
        'activite',
        'af_nbenf',
        'af',
        'aide_logement_montant_brut',
        'aspa',
        'autonomie_financiere',
        'chomage_brut',
        'chomage_imposable',
        'chomage_nette',
        'menage_ordinaire_individus',
        'minimum_vieillesse',
        'nbptr',
        'pensions_alimentaires_percues',
        # 'revenu_disponible',  can be negative if rag, ric or rnc are negative
        'retraite_brute',
        'retraite_imposable',
        'retraite_nette',
        'rsa_base_ressources',
        'rsa',
        'salaire_imposable',
        'salaire_net',
        'weight_familles',
        ]
    strictly_positive_sum_variables = positive_variables
    strictly_positive_sum_variables.remove('aide_logement_montant_brut')

    for entity, data_frame in data_frame_by_entity.iteritems():
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


def test_erfs_fpr_survey_simulation(year = 2012, rebuild = False):
    tax_benefit_system = base_survey.get_cached_reform(
        reform_key = 'inversion_directe_salaires',
        tax_benefit_system = base_survey.france_data_tax_benefit_system,
        )
    survey_scenario = ErfsFprSurveyScenario.create(
        tax_benefit_system = tax_benefit_system,
        reference_tax_benefit_system = tax_benefit_system,
        year = year,
        # rebuild_input_data = True,
        )
    data_frame_by_entity = None
    #    data_frame_by_entity = survey_scenario.create_data_frame_by_entity(
#        variables = variables,
#        )
#    loose_check(data_frame_by_entity)
    return survey_scenario, data_frame_by_entity


def test_erfs_survey_simulation(year = 2009):
    tax_benefit_system = base_survey.get_cached_reform(
        reform_key = 'inversion_directe_salaires',
        tax_benefit_system = base_survey.france_data_tax_benefit_system,
        )
    survey_scenario = ErfsSurveyScenario.create(
        tax_benefit_system = tax_benefit_system,
        reference_tax_benefit_system = tax_benefit_system,
        year = year,
        )

    data_frame_by_entity = survey_scenario.create_data_frame_by_entity(
        variables = variables,
        )
    loose_check(frame_by_entity)
    assert (
        data_frame_by_entity['familles'].weight_familles * data_frame_by_entity['familles'].af
        ).sum() / 1e9 > 10

    return survey_scenario, frame_by_entity


def test_weights_building():
    year = 2012
    survey_scenario = ErfsFprSurveyScenario.create(year = year)
    survey_scenario.new_simulation()
    return survey_scenario.simulation


def show_variable(variable, index = None):
    simulation = survey_scenario.simulation
    holder = simulation.get_holder(variable)
    print 'formula: ', holder.__dict__['formula']
    print 'scalar: ', holder.column.scalar
    if holder.column.scalar:
        print holder.array[0]
        return
    for period, array in sorted(holder._array_by_period.iteritems()):
        if index is not None:
            print str(period), array[index]
        else:
            print str(period), array.mean(), array.min(), array.max()

if __name__ == '__main__':
    import time
    log = logging.getLogger(__name__)
    import sys
    logging.basicConfig(level = logging.INFO, stream = sys.stdout)
    start = time.time()
    survey_scenario, data_frame_by_entity = test_erfs_fpr_survey_simulation(year = 2012)
    print survey_scenario.simulation.calculate('salaire_imposable_pour_inversion')

    # print survey_scenario.simulation.calculate('salaire_de_base')

    data_frame_by_entity = survey_scenario.create_data_frame_by_entity(
        variables = [
            'categorie_salarie',
            'salaire_imposable_pour_inversion',
            'contrat_de_travail',
            'heures_remunerees_volume',
            'salaire_de_base',
            'salaire_imposable',
            'plafond_securite_sociale',
            ],
        )

#    data_frame_familles = data_frame_by_entity['famille']
#    data_frame_foyers_fiscaux = data_frame_by_entity['foyer_fiscal']
    data_frame_individus = data_frame_by_entity['individu']
    data_frame_individus.query('salaire_imposable_pour_inversion > 0').categorie_salarie.isin(range(7)).all()
    data_frame_individus.query('salaire_imposable_pour_inversion > 0').contrat_de_travail.isin(range(2)).all()
    simulation = survey_scenario.simulation

    (data_frame_individus.query(
        '(heures_remunerees_volume == 0) & (salaire_imposable_pour_inversion > 0)'
        ).contrat_de_travail == 0).all()

    #    data_frame_menages = data_frame_by_entity['menage']
    print(time.time() - start)

    mask = data_frame_individus.query(
        '(categorie_salarie in [0, 1]) & (salaire_imposable_pour_inversion > 0)')
    x = mask[[
        'salaire_imposable',
        'salaire_imposable_pour_inversion',
        'salaire_de_base',
        'categorie_salarie',
        'contrat_de_travail',
        'heures_remunerees_volume',
        'plafond_securite_sociale'
        ]].copy()

    x['plafond_recalcule'] = (x.heures_remunerees_volume / (35 * 52)) * 36372
    (
        (mask.salaire_imposable_pour_inversion - mask.salaire_imposable).abs() > .1
        ).sum()

    show_variable('salaire_imposable_pour_inversion', index = 7)
    show_variable('salaire_de_base', index = 7)

    bim
    simulation.calculate('plafond_securite_sociale')
    simulation.calculate('assiette_cotisations_sociales')
    simulation.calculate('assiette_cotisations_sociales_prive')

    simulation.calculate('agff_salarie')
    simulation.calculate('salaire_imposable')
    show_variable('agff_salarie', index = 7)

    show_variable('salaire_imposable', index = 7)
    for variable in [
       'age',
       'age_en_mois',
       'af_nbenf',
       ]:
       show_variable(variable)

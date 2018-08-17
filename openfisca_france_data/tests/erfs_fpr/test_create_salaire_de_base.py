#! /usr/bin/env python2
# -*- coding: utf-8 -*-


from openfisca_core import periods
from openfisca_france import FranceTaxBenefitSystem
from openfisca_france_data.erfs_fpr.input_data_builder.step_03_variables_individuelles import (
    create_ages,
    create_date_naissance,
    create_activite,
    create_revenus,
    create_contrat_de_travail,
    create_categorie_salarie,
    create_salaire_de_base,
    create_effectif_entreprise,
    create_traitement_indiciaire_brut,
    )
from openfisca_survey_manager.temporary import get_store

from openfisca_france_data.erfs_fpr.get_survey_scenario import get_survey_scenario


def test_create_salaire_de_base(year):
    """
    Test create_salaire_de_base avec données de l'enquête erfs_fpr
    """
    temporary_store = get_store(file_name = 'erfs_fpr')
    individu = temporary_store['individu_for_inversion_{}'.format(year)]

    id_variables = ['idfoy', 'idmen', 'idfam']
    for id_variable in id_variables:
        individu[id_variable] = range(0, len(individu))

    position_variables = ['quifoy', 'quimen', 'quifam']
    for position_variable in position_variables:
        individu[position_variable] = 0

    individu['zone_apl'] = 2
    data = dict(
        input_data_frame_by_entity = dict(
            individu = individu,
            )
        )
    survey_scenario = get_survey_scenario(
        year = year,
        data = data,
        )

    variables = ['salaire_de_base', 'salaire_imposable']
    survey_scenario.create_data_frame_by_entity(variables = variables, period = periods.period(year))

    return survey_scenario


def create_individu_for_inversion(year):
    assert year is not None

    # Using data produced by preprocessing.build_merged_dataframes
    temporary_store = get_store(file_name = 'erfs_fpr')
    individus = temporary_store['individus_{}_post_01'.format(year)]

    old_by_new_variables = {
        'chomage_i': 'chomage_net',
        'pens_alim_recue_i': 'pensions_alimentaires_percues',
        'rag_i': 'rag_net',
        'retraites_i': 'retraite_nette',
        'ric_i': 'ric_net',
        'rnc_i': 'rnc_net',
        'salaires_i': 'salaire_net',
        }

    for variable in old_by_new_variables:
        assert variable in individus.columns.tolist(), "La variable {} n'est pas présente".format(variable)

    individus.rename(
        columns = old_by_new_variables,
        inplace = True,
        )

    created_variables = []
    create_ages(individus, year)
    created_variables.append('age')
    created_variables.append('age_en_mois')

    create_date_naissance(individus, age_variable = None, annee_naissance_variable = 'naia', mois_naissance = 'naim',
        year = year)
    created_variables.append('date_naissance')

    revenu_type = 'net'
    period = periods.period(year)
    create_revenus(individus, revenu_type = revenu_type)
    # created_variables.append('taux_csg_remplacement')

    create_contrat_de_travail(individus, period = period, salaire_type = revenu_type)
    created_variables.append('contrat_de_travail')
    created_variables.append('heures_remunerees_volume')

    create_categorie_salarie(individus, period = period)
    created_variables.append('categorie_salarie')

    tax_benefit_system = FranceTaxBenefitSystem()
    create_salaire_de_base(individus, period = period, revenu_type = revenu_type, tax_benefit_system = tax_benefit_system)
    created_variables.append('salaire_de_base')

    create_effectif_entreprise(individus)
    created_variables.append('effectif_entreprise')

    create_traitement_indiciaire_brut(individus, period = period, revenu_type = revenu_type,
        tax_benefit_system = tax_benefit_system)
    created_variables.append('traitement_indiciaire_brut')

    temporary_store['individu_for_inversion_{}'.format(year)] = individus[created_variables]



if __name__ == '__main__':
    year = 2012
    create_individu_for_inversion(year)
    survey_scenario = test_create_salaire_de_base(year)

#! /usr/bin/env python2
import logging


from openfisca_core import periods
from openfisca_france import FranceTaxBenefitSystem
from openfisca_france.model.base import TypesCategorieSalarie
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


log = logging.getLogger(__name__)


variables_de_base = [
    'categorie_salarie',
    'contrat_de_travail',
    'heures_remunerees_volume',
    'hsup',
    'nombre_jours_calendaires',
    'salaire_imposable',
    'salaire_net',
    ]

cotisations_nulles_hors_prive = [
    # non contributives
    'agff_salarie',
    'agirc_salarie',
    'agirc_gmp_salarie',
    'apec_salarie',
    'arrco_salarie',
    'chomage_salarie',
    'cotisation_exceptionnelle_temporaire_salarie',
    'vieillesse_deplafonnee_salarie',
    'vieillesse_plafonnee_salarie',
    # contributives
    'mmid_salarie',
    ]

variables_nulles_hors_prive = [
    'complementaire_sante_salarie',
    'indemnite_fin_contrat',
    'salaire_de_base',
    ] + cotisations_nulles_hors_prive

cotisations_nulles_hors_fonction_publique = [
    # non contributives
    'ircantec_salarie',
    'pension_civile_salarie',
    'rafp_salarie',
    # contributives
    'contribution_exceptionnelle_solidarite',
    ]

variables_nulles_hors_fonction_publique = [
    'traitement_indiciaire_brut',
    'remuneration_principale',
    'primes_fonction_publique',
    'indemnite_residence',
    'supplement_familial_traitement',
    ] + cotisations_nulles_hors_fonction_publique


categories_salarie_du_public = [
    'public_titulaire_etat',
    'public_titulaire_hospitaliere',
    'public_titulaire_territoriale',
    'public_titulaire_militaire'
    ]

index_by_categorie_salarie_du_public = dict(
    (categorie, TypesCategorieSalarie[categorie].index)
    for categorie in categories_salarie_du_public
    )

index_by_categorie_salarie_hors_public = dict(
    (categorie, TypesCategorieSalarie[categorie].index)
    for categorie in TypesCategorieSalarie.__members__.keys()
    if categorie not in categories_salarie_du_public
    )


def check_variable_nullity(data_frame, variable, categorie_salarie, categorie_salarie_index):
    extraction = data_frame.query(
        'categorie_salarie == @categorie_salarie_index'
        )
    if not (extraction[variable] < 1).all():
        print(
            "{} non nul categorie_salarie={} ({})".format(
            variable, categorie_salarie_index, categorie_salarie)
            )
        print(
            extraction.loc[~(extraction[variable] < 1), variable].head()
            )


def check_nullity_public_variables(data_frame):
    for variable in variables_nulles_hors_fonction_publique:
        for categorie_salarie, categorie_salarie_index in index_by_categorie_salarie_hors_public.items():
            print("{}, {}".format(variable, categorie_salarie))
            if variable == 'indemnite_residence' and categorie_salarie == 'public_non_titulaire':
                continue

            check_variable_nullity(data_frame, variable, categorie_salarie, categorie_salarie_index)


def check_nullity_private_variables(data_frame):
    for variable in variables_nulles_hors_prive:
        for categorie_salarie, categorie_salarie_index in index_by_categorie_salarie_du_public.items():
            print("{}, {}".format(variable, categorie_salarie))
            check_variable_nullity(data_frame, variable, categorie_salarie, categorie_salarie_index)


def remove_some_variables_after_check(data_frame):
    zero_variables = [
        'complementaire_sante_salarie',
        'hsup',
        'indemnite_fin_contrat',
        'indemnite_residence',
        'supplement_familial_traitement',
        ]

    for variable in zero_variables:
        assert (data_frame[variable] == 0).all(), "{} is not always = 0".format(variable)
        del data_frame[variable]

    assert (data_frame['nombre_jours_calendaires'] == 366).all()
    del data_frame['nombre_jours_calendaires']


def test_create_salaire_de_base(year, revenu_type = 'net'):
    """
    Test create_salaire_de_base avec données de l'enquête erfs_fpr
    """
    temporary_store = get_store(file_name = 'erfs_fpr')
    individu = temporary_store['individu_for_inversion_{}'.format(year)]

    if revenu_type == 'net':
        salaire_pour_inversion = individu.salaire_net.copy()
    elif revenu_type == 'imposable':
        salaire_pour_inversion = individu.salaire_imposable.copy()

    id_variables = ['idfoy', 'idmen', 'idfam']
    for id_variable in id_variables:
        individu[id_variable] = range(0, len(individu))

    position_variables = ['quifoy', 'quimen', 'quifam']
    for position_variable in position_variables:
        individu[position_variable] = 0

    data = dict(
        input_data_frame_by_entity = dict(
            individu = individu,
            )
        )
    survey_scenario = get_survey_scenario(
        year = year,
        data = data,
        )

    survey_scenario.tax_benefit_system.neutralize_variable('indemnite_residence')

    variables = set(
        variables_de_base
        + variables_nulles_hors_prive
        + variables_nulles_hors_fonction_publique
        )
    data_frame = survey_scenario.create_data_frame_by_entity(
        variables = variables, period = periods.period(year)
        )['individu']
    data_frame['salaire_pour_inversion'] = salaire_pour_inversion
    data_frame.rename(columns = {'salaire_{}'.format(revenu_type): 'salaire'}, inplace = True)

    return survey_scenario, data_frame


def create_individu_for_inversion(year, revenu_type = 'net'):
    assert revenu_type in ['net', 'imposable']
    assert year is not None

    # Using data produced by preprocessing.build_merged_dataframes
    temporary_store = get_store(file_name = 'erfs_fpr')
    individus = temporary_store['individus_{}_post_01'.format(year)]

    if revenu_type == 'net':
        old_by_new_variables = {
            'chomage_i': 'chomage_net',
            'pens_alim_recue_i': 'pensions_alimentaires_percues',
            'rag_i': 'rag_net',
            'retraites_i': 'retraite_nette',
            'ric_i': 'ric_net',
            'rnc_i': 'rnc_net',
            'salaires_i': 'salaire_net',
            }
    elif revenu_type == 'imposable':
        old_by_new_variables = {
            'chomage_i': 'chomage_imposable',
            'pens_alim_recue_i': 'pensions_alimentaires_percues',
            'rag_i': 'rag_net',
            'retraites_i': 'retraite_imposable',
            'ric_i': 'ric_net',
            'rnc_i': 'rnc_net',
            'salaires_i': 'salaire_imposable',
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

    period = periods.period(year)
    # create_revenus(individus, revenu_type = revenu_type)
    # created_variables.append('taux_csg_remplacement')

    create_contrat_de_travail(individus, period = period, salaire_type = revenu_type)
    created_variables.append('contrat_de_travail')
    created_variables.append('heures_remunerees_volume')

    create_categorie_salarie(individus, period = period)
    created_variables.append('categorie_salarie')

    tax_benefit_system = FranceTaxBenefitSystem()
    create_salaire_de_base(individus, period = period, revenu_type = revenu_type, tax_benefit_system = tax_benefit_system)
    created_variables.append('salaire_de_base')

    create_effectif_entreprise(individus, period = period)
    created_variables.append('effectif_entreprise')

    create_traitement_indiciaire_brut(individus, period = period, revenu_type = revenu_type,
        tax_benefit_system = tax_benefit_system)
    created_variables.append('traitement_indiciaire_brut')
    created_variables.append('primes_fonction_publique')

    other_variables = ['salaire_{}'.format(revenu_type)]
    temporary_store['individu_for_inversion_{}'.format(year)] = individus[
        created_variables + other_variables]


if __name__ == '__main__':
    year = 2012
    revenu_type = 'imposable'

    create_individu_for_inversion(year, revenu_type = revenu_type)
    survey_scenario, data_frame = test_create_salaire_de_base(year, revenu_type = revenu_type)

    check_nullity_public_variables(data_frame)
    check_nullity_private_variables(data_frame)
    remove_some_variables_after_check(data_frame)

    data_frame['absolute_error'] =  (data_frame.salaire - data_frame.salaire_pour_inversion).abs()
    data_frame['relative_error'] = (
        (data_frame.salaire - data_frame.salaire_pour_inversion).abs()
        / (data_frame.salaire_pour_inversion + 1 * (data_frame.salaire_pour_inversion == 0))
        )

    absolute_error_threshold = 5
    relative_error_threshold = .001

    dispatch = ['categorie_salarie', 'contrat_de_travail']
    data_frame['absolute_errored'] = data_frame['absolute_error'] > absolute_error_threshold
    data_frame['relative_errored'] = data_frame['relative_error'] > relative_error_threshold
    nb = data_frame.groupby(dispatch)['contrat_de_travail'].count()
    nb_absolute = data_frame.groupby(dispatch)['absolute_errored'].sum().astype(int)
    pct_absolute = data_frame.groupby(dispatch)['absolute_errored'].sum() /  data_frame.groupby(['categorie_salarie', 'contrat_de_travail'])['absolute_errored'].count()
    mean_absolute = data_frame.query('absolute_errored').groupby(dispatch)['absolute_error'].mean()
    max_aboslute = data_frame.groupby(dispatch)['absolute_error'].max()

    pct_relative = data_frame.groupby(dispatch)['relative_errored'].sum() /  data_frame.groupby(dispatch)['relative_errored'].count()
    mean_relative = data_frame.query('relative_errored').groupby(dispatch)['relative_error'].mean()
    max_relative = data_frame.groupby(dispatch)['relative_error'].max()


    max_aboslute
    pct_absolute

    max_relative
    pct_relative
    nb

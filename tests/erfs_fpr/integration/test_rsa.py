import logging

from openfisca_core.model_api import *  # type:ignore
from openfisca_france.entities import Famille, Individu  # type:ignore
from openfisca_france_data.erfs_fpr.scenario import ErfsFprSurveyScenario  # type:ignore
from openfisca_france_data import france_data_tax_benefit_system  # type:ignore

log = logging.getLogger(__name__)


def get_custom_survey_scenario(year = 2012, rebuild_input_data = False):
    tax_benefit_system = france_data_tax_benefit_system

    class rsa_origin(Variable):
        value_type = float
        entity = Famille
        label = "RSA de l'ENA"
        definition_period = MONTH

    class aah_origin(Variable):
        value_type = float
        entity = Famille
        label = "RSA de l'ENA"
        definition_period = MONTH

    class paje_clca_origin(Variable):
        value_type = float
        entity = Famille
        label = "RSA de l'ENA"
        definition_period = MONTH

    class hors_match(Variable):
        value_type = bool
        entity = Individu
        label = "hors match"
        definition_period = MONTH

    class activite_famille_max(Variable):
        value_type = int
        entity = Famille
        label = "activite_famille"
        definition_period = MONTH

        def formula(famille, period):
            activite = famille.members('activite', period)
            return famille.max(activite, role = Famille.PARENT)

    class activite_famille_min(Variable):
        value_type = int
        entity = Famille
        label = "activite_famille"
        definition_period = MONTH

        def formula(famille, period):
            activite = famille.members('activite', period)
            return famille.min(activite, role = Famille.PARENT)

    tax_benefit_system.add_variable(activite_famille_max)
    tax_benefit_system.add_variable(activite_famille_min)

    survey_scenario = ErfsFprSurveyScenario.create(
        tax_benefit_system = tax_benefit_system,
        year = year,
        )
    data = dict(
        input_data_table = dict(),
        input_data_survey_prefix = 'openfisca_erfs_fpr_data',
        )
    survey_scenario.init_from_data(
        data = data,
        rebuild_input_data = rebuild_input_data,
        )
    return survey_scenario


survey_scenario = get_custom_survey_scenario(rebuild_input_data = False)

data_frame_by_entity = survey_scenario.create_data_frame_by_entity(
    variables = [
        'activite_famille_min',
        'activite_famille_max',
        'aspa',
        'asi',
        'etudiant',
        'hors_match',
        'activite',
        'heures_remunerees_volume',
        'nb_parents',
        'rsa',
        'rsa_base_ressources',
        'rsa_base_ressources_individu',
        'rsa_forfait_logement',
        'rsa_montant',
        'rsa_origin',
        'rsa_revenu_activite',
        'rsa_forfait_logement',
        'weight_familles',
        ],
    )

famille = data_frame_by_entity['famille']
individu = data_frame_by_entity['individu']
menage = data_frame_by_entity['menage']

famille.activite_famille_min.value_counts(dropna = False)

famille.groupby(
    [
        'nb_parents',
        'activite_famille_max',
        'activite_famille_min',
        ],
    )['rsa'].sum()

rsa_pivot_table = survey_scenario.compute_pivot_table(
    columns = ['nb_parents'],
    values = ['rsa'],
    aggfunc = 'sum',
    period = 2012,
    )

count_pivot_table = survey_scenario.compute_pivot_table(
    columns = ['nb_parents'],
    values = ['rsa'],
    aggfunc = 'count',
    period = 2012,
    )

survey_scenario.summarize_variable('rsa', weighted = True, force_compute = True)

survey_scenario.summarize_variable('rsa_revenu_activite')
survey_scenario.summarize_variable('rsa_forfait_logement')
survey_scenario.summarize_variable('rsa_base_ressources')

survey_scenario.summarize_variable('rsa_base_ressources_individu', weighted = True)
survey_scenario.summarize_variable('rsa', weighted = True)

survey_scenario.summarize_variable('revenus_capitaux_prelevement_bareme', weighted = True)
survey_scenario.summarize_variable('revenus_capitaux_prelevement_liberatoire', weighted = True)

types_revenus_non_pros = [
    'allocation_securisation_professionnelle',
    'dedommagement_victime_amiante',
    'gains_exceptionnels',
    'pensions_alimentaires_percues',
    'pensions_invalidite',
    'prestation_compensatoire',
    'prime_forfaitaire_mensuelle_reprise_activite',
    'rsa_base_ressources_patrimoine_individu',
    'rsa_indemnites_journalieres_hors_activite',
    ]

for revenu in types_revenus_non_pros:
    survey_scenario.summarize_variable(revenu, weighted = True)

assert 9e9 < (famille.rsa_montant * famille.weight_familles).sum() / 1e9 < 10e9, \
    "Rsa = {} Mds €".format((famille.rsa_montant * famille.weight_familles).sum() / 1e9)

#!/usr/bin/env python2
# -*- coding: utf-8 -*-

#%%

from __future__ import division


import logging
import numpy as np


from openfisca_core.model_api import *
from openfisca_france.entities import Famille, Individu
from openfisca_france_data.erfs_fpr.scenario import ErfsFprSurveyScenario
from openfisca_france_data.tests import base as base_survey


log = logging.getLogger(__name__)


is_travis = 'TRAVIS' in os.environ

if is_travis:
    exit()


def get_survey_scenario(year = 2012, rebuild_input_data = False):
    tax_benefit_system = base_survey.france_data_tax_benefit_system

    class rsa_origin(Variable):
        value_type = float
        entity = Famille
        label = u"RSA de l'ENA"
        definition_period = MONTH

    class aah_origin(Variable):
        value_type = float
        entity = Famille
        label = u"RSA de l'ENA"
        definition_period = MONTH

    class paje_clca_origin(Variable):
        value_type = float
        entity = Famille
        label = u"RSA de l'ENA"
        definition_period = MONTH

    class hors_match(Variable):
        value_type = bool
        entity = Individu
        label = u"hors match"
        definition_period = MONTH

    class activite_famille_max(Variable):
        value_type = int
        entity = Famille
        label = u"activite_famille"
        definition_period = MONTH

        def formula(famille, period):
            activite = famille.members('activite', period)
            return period, famille.max(activite, role = Famille.PARENT)

    class activite_famille_min(Variable):
        value_type = int
        entity = Famille
        label = u"activite_famille"
        definition_period = MONTH

        def formula(famille, period):
            activite = famille.members('activite')
            return period, famille.min(activite, role = Famille.PARENT)

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


survey_scenario = get_survey_scenario(rebuild_input_data = True)


#%%




#%%
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
        'rsa_revenu_activite'
        'rsa_forfait_logement',
        'weight_familles',
        ],
    )
famille = data_frame_by_entity['famille']
individu = data_frame_by_entity['individu']
menage = data_frame_by_entity['menage']



#%%
famille.activite_famille_min.value_counts(dropna = False)

famille.groupby(
    ['nb_parents', 'activite_famille_max', 'activite_famille_min']
    )['rsa'].sum()

#%%

rsa_pivot_table = survey_scenario.compute_pivot_table(
    columns = ['nb_parents', 'activite_famille_max', 'activite_famille_min'],
    values = ['rsa'],
    aggfunc = 'sum',
    )


count_pivot_table = survey_scenario.compute_pivot_table(
    columns = ['nb_parents', 'activite_famille_max', 'activite_famille_min'],
    values = ['rsa'],
    aggfunc = 'count',
    )
#%%

survey_scenario.summarize_variable('rsa', weighted = True, force_compute = True)

survey_scenario.summarize_variable('rsa_revenu_activite')
survey_scenario.summarize_variable('rsa_forfait_logement')
survey_scenario.summarize_variable('rsa_base_ressources')

survey_scenario.summarize_variable('rsa_base_ressources_individu', weighted = True)
survey_scenario.summarize_variable('rsa', weighted = True)

survey_scenario.summarize_variable('rev_cap_bar', weighted = True)
survey_scenario.summarize_variable('rev_cap_lib', weighted = True)


types_revenus_non_pros = [
    'allocation_aide_retour_emploi',
    'allocation_securisation_professionnelle',
    'dedommagement_victime_amiante',
    'div_ms',
    'gains_exceptionnels',
    'pensions_alimentaires_percues',
    'pensions_invalidite',
    'prestation_compensatoire',
    'prime_forfaitaire_mensuelle_reprise_activite',
    'revenus_fonciers_minima_sociaux',
    'rsa_base_ressources_patrimoine_individu',
    'rsa_indemnites_journalieres_hors_activite',
    ]
for revenu in types_revenus_non_pros:
    survey_scenario.summarize_variable(revenu, weighted = True)




#%%

assert 9e9 < (famille.rsa_montant * famille.weight_familles).sum() / 1e9 < 10e9




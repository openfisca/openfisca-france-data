#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#%%

from __future__ import division


import numpy as np


from openfisca_france_data.erfs_fpr.scenario import ErfsFprSurveyScenario
from openfisca_france_data.tests import base as base_survey


def get_survey_scenario(year = 2012, rebuild_input_data = False):
    tax_benefit_system = base_survey.get_cached_reform(
        reform_key = 'inversion_directe_salaires',
        tax_benefit_system = base_survey.france_data_tax_benefit_system,
        )
    survey_scenario = ErfsFprSurveyScenario.create(
        tax_benefit_system = tax_benefit_system,
        reference_tax_benefit_system = tax_benefit_system,
        year = year,
        rebuild_input_data = rebuild_input_data,
        )
    return survey_scenario


survey_scenario = get_survey_scenario()

#%%
data_frame_by_entity = survey_scenario.create_data_frame_by_entity(
    variables = [
        'af_base',
        'af_nbenf',
        'age_en_mois',
        'age',
        'autonomie_financiere',
        'af_eligibilite_base',
        'menage_ordinaire_familles',
        'est_enfant_dans_famille',
        'prestations_familiales_enfant_a_charge',
        'rempli_obligation_scolaire',
        'residence_dom',
        'weight_familles',
        'weight_individus',
        'wprm',
        ],
    )
famille = data_frame_by_entity['famille']
individu = data_frame_by_entity['individu']
menage = data_frame_by_entity['menage']

#%%
population_by_age = individu.groupby('age')[['weight_individus']].sum().reset_index()
# Les 0-16 ans sont au moins 700 000 et au plus 850 000
assert (population_by_age.query('age <= 16 & age >= 0')['weight_individus'] > 7e5).all(), \
    'Les 0-16 ans doivent être au moins 700 000'
assert (population_by_age.query('age <= 16 & age >= 0')['weight_individus'] < 85e4).all(), \
    'Les 0-16 ans doivent être sont au plus 850 000'


#%%

assert famille.weight_familles.sum() < 30e6
assert famille.weight_familles.sum() > 29e6

(famille
    .groupby(['af_nbenf'])['weight_familles']
    .sum()
    .reset_index()
    .query('af_nbenf > 0')
    .weight_familles
    .sum()
    ) > 8e6

#%%
print (famille.af_base * famille.weight_familles).sum()


#%%
famille.groupby(['af_eligibilite_base'])['weight_familles'].sum()
menage.groupby(['residence_dom'])['wprm'].sum()
individu.groupby(['prestations_familiales_enfant_a_charge'])['weight_individus'].sum()  # PROBLEM
individu.groupby(['est_enfant_dans_famille'])['weight_individus'].sum()
individu.groupby(['autonomie_financiere'])['weight_individus'].sum()
individu.groupby(['autonomie_financiere', 'est_enfant_dans_famille', 'rempli_obligation_scolaire'])['weight_individus'].sum()

#%%
survey_scenario.get_memory_usage('rempli_obligation_scolaire')

#%%
# survey_scenario.summarize_variable('age')
famille.groupby(['af_nbenf'])['weight_familles'].sum()

#%%
individu.groupby(['age', 'autonomie_financiere'])['weight_individus'].sum()
individu.groupby(['age', 'est_enfant_dans_famille'])['weight_individus'].sum()
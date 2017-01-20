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


#%%
survey_scenario = get_survey_scenario()

#%%
data_frame_by_entity = survey_scenario.create_data_frame_by_entity(
    variables = [
        'af_base',
        'af_nbenf',
        'age_en_mois',
        'age',
        'autonomie_financiere',
        'autonomie_financiere',
        'champm_familles',
        'est_enfant_dans_famille',
        'weight_familles',
        'weight_individus',
        ],
    )
famille = data_frame_by_entity['famille']
individu = data_frame_by_entity['individu']

#%%
population_by_age = individu.groupby('age')[['weight_individus']].sum().reset_index()
# Les 0-16 ans sont au moins 700 000 et au plus 850 000
assert (population_by_age.query('age <= 16 & age >= 0')['weight_individus'] > 7e5).all(), \
    'Les 0-16 ans doivent être au moins 700 000'
assert (population_by_age.query('age <= 16 & age >= 0')['weight_individus'] < 85e4).all(), \
    'Les 0-16 ans doivent être sont au plus 850 000'


#%%

print famille.weight_familles.sum()
# 17 à 18 millions de familles

#%%
print individu.groupby(['age'])['est_enfant_dans_famille'].agg(min, max, 'mean')



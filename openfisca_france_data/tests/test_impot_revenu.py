#! /usr/bin/env python2
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


survey_scenario = get_survey_scenario(rebuild_input_data = True)

#%%
data_frame_by_entity = survey_scenario.create_data_frame_by_entity(
    variables = [
        'irpp',
        'maries_ou_pacses',
        'nbptr',
        'statut_marital',
        'weight_foyers',
        ],
    )
famille = data_frame_by_entity['famille']
foyer_fiscal = data_frame_by_entity['foyer_fiscal']
individu = data_frame_by_entity['individu']
menage = data_frame_by_entity['menage']


#%%
# statut_occupation
print individu.statut_marital.value_counts()
print foyer_fiscal.groupby('maries_ou_pacses')['weight_foyers'].sum()
print foyer_fiscal.groupby('nbptr')['weight_foyers'].sum()


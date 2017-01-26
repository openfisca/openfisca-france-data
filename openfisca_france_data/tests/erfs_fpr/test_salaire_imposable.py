#! /usr/bin/env python2
# -*- coding: utf-8 -*-

#%%

from __future__ import division


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
survey_scenario.summarize_variable('salaire_de_base', force_compute = True)

#%%
survey_scenario.summarize_variable('salaire_imposable', force_compute = True)
survey_scenario.summarize_variable('salaire_de_base', force_compute = True)

#%%
survey_scenario.summarize_variable('csg_imposable_salaire')


#%%

#%%
data_frame_by_entity = survey_scenario.create_data_frame_by_entity(
    variables = [
        'salaire_de_base',
        'salaire_imposable',
        # 'csg_imposable_salaire',
        # 'categorie_salarie',
        # 'salaire_imposable_pour_inversion',
        # 'weight_individus',
        # 'wprm',
        ],
    )

#famille = data_frame_by_entity['famille']
individu = data_frame_by_entity['individu']
menage = data_frame_by_entity['menage']


#%%

individu.categorie_salarie.value_counts()
#%%
prive = individu.query('categorie_salarie in [0, 1]')
(prive.salaire_imposable - prive.salaire_imposable_pour_inversion).abs().max()

#%%
survey_scenario.summarize_variable('salaire_imposable_pour_inversion')

#%%





#%%
survey_scenario.summarize_variable('csg_deductible_salaire')


#%%
survey_scenario.summarize_variable('chomage_brut')

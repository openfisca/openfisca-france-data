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
        baseline_tax_benefit_system = tax_benefit_system,
        year = year,
        rebuild_input_data = rebuild_input_data,
        )
    return survey_scenario


survey_scenario = get_survey_scenario()

#%%
data_frame_by_entity = survey_scenario.create_data_frame_by_entity(
    variables = [
        'age',
        'aides_logement',
        'aide_logement_montant_brut',
        'apl',
        'alf',
        'als',
        'statut_occupation_logement',
        'weight_familles',
        'weight_individus',
        'wprm',
        ],
    )
famille = data_frame_by_entity['famille']
individu = data_frame_by_entity['individu']
menage = data_frame_by_entity['menage']

#%%
# statut_occupation
statut_occupation_logement_pct = menage.groupby('statut_occupation_logement')['wprm'].sum() / menage.wprm.sum()
# 2 proprietaire
assert .39 < statut_occupation_logement_pct[2] < .41
# accedant
assert .17 < statut_occupation_logement_pct[1] < .18
# locataire (indiferrencie)
assert .39 < statut_occupation_logement_pct[3:7].sum() < .43

#%%

11e10 < (famille.aide_logement_montant_brut * famille.weight_familles).sum()
11e10 < (famille.apl * famille.weight_familles).sum() + (famille.als * famille.weight_familles).sum() + (famille.alf * famille.weight_familles).sum()

## Reste un peu faiblard

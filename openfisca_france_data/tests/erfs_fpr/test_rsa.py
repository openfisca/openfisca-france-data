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
survey_scenario.summarize_variable('salaire_imposable', force_compute = True)
survey_scenario.summarize_variable('salaire_de_base', force_compute = True)

#%%
survey_scenario.summarize_variable('rsa_non_calculable', force_compute = True)


#! /usr/bin/env python2
# -*- coding: utf-8 -*-

#%%


from __future__ import division


from openfisca_france_data.erfs_fpr.scenario import ErfsFprSurveyScenario
from openfisca_france_data.tests import base as base_survey


from openfisca_france_data.erfs_fpr.scenario import ErfsFprSurveyScenario


def get_survey_scenario(year = 2012, rebuild_input_data = False, reform_key = None):
    tax_benefit_system = base_survey.get_cached_reform(
        reform_key = reform_key,
        tax_benefit_system = base_survey.france_data_tax_benefit_system,
        )
    survey_scenario = ErfsFprSurveyScenario.create(
        tax_benefit_system = tax_benefit_system,
        baseline_tax_benefit_system = tax_benefit_system,
        year = year,
        )
    survey_scenario.init_from_survey_tables(
        rebuild_input_data = rebuild_input_data,
        )
    return survey_scenario



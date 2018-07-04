#! /usr/bin/env python2
# -*- coding: utf-8 -*-


from __future__ import division


from openfisca_france_data.erfs_fpr.scenario import ErfsFprSurveyScenario
from openfisca_france_data.tests import base as base_survey


def get_survey_scenario(year = 2012, rebuild_input_data = False, tax_benefit_system = None,
        baseline_tax_benefit_system = None, reform_key = None):
    if tax_benefit_system is None and reform_key is not None:
        tax_benefit_system = base_survey.get_cached_reform(
            reform_key = reform_key,
            tax_benefit_system = base_survey.france_data_tax_benefit_system,
            )
    if baseline_tax_benefit_system is None:
        baseline_tax_benefit_system = tax_benefit_system

    survey_scenario = ErfsFprSurveyScenario.create(
        tax_benefit_system = tax_benefit_system,
        baseline_tax_benefit_system = tax_benefit_system,
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

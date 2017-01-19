#!/usr/bin/env python2
# -*- coding: utf-8 -*-


from openfisca_france_data.erfs.scenario import ErfsSurveyScenario
from openfisca_france_data.erfs_fpr.scenario import ErfsFprSurveyScenario
from openfisca_france_data.tests import base as base_survey


def show_variable(variable, index = None):
    simulation = survey_scenario.simulation
    holder = simulation.get_holder(variable)
    print 'formula: ', holder.__dict__['formula']
    print 'scalar: ', holder.column.scalar
    if holder.column.scalar:
        print holder.array[0]
        return
    for period, array in sorted(holder._array_by_period.iteritems()):
        if index is not None:
            print str(period), array[index]
        else:
            print str(period), array.mean(), array.min(), array.max()



year = 2012
tax_benefit_system = base_survey.get_cached_reform(
    reform_key = 'inversion_directe_salaires',
    tax_benefit_system = base_survey.france_data_tax_benefit_system,
    )
survey_scenario = ErfsFprSurveyScenario.create(
    tax_benefit_system = tax_benefit_system,
    reference_tax_benefit_system = tax_benefit_system,
    year = year,
    # rebuild_input_data = True,
    )


data_frame_by_entity = survey_scenario.create_data_frame_by_entity(
    variables = [
        'age',
        'af_nbenf',
        'age_en_mois',
        'autonomie_financiere',
        'champm_familles',
        'weight_familles',
        'af_base',
        'est_enfant_dans_famille',
        'autonomie_financiere',
        ],
    )

famille = data_frame_by_entity['famille']
famille.groupby('af_nbenf')[['weight_familles']].sum()
individu = data_frame_by_entity['individu']
individu.groupby(['age'])['est_enfant_dans_famille'].agg(min, max, 'mean')

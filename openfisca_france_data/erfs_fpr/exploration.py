#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from __future__ import division

import pandas as pd

from openfisca_survey_manager.survey_collections import SurveyCollection


year = 2012
erfs_fpr_survey_collection = SurveyCollection.load(collection = 'erfs_fpr')
yr = str(year)[-2:]  # 12 for 2012
survey = erfs_fpr_survey_collection.get_survey('erfs_fpr_{}'.format(year))
fpr_menage = survey.get_values(table = 'fpr_menage_{}_retropole'.format(year))
# eec_menage = survey.get_values(table = 'fpr_mrf{}e{}t4'.format(yr, yr))
eec_individu = survey.get_values(table = 'fpr_irf{}e{}t4'.format(yr, yr))
fpr_individu = survey.get_values(table = 'fpr_indiv_{}_retropole'.format(year))

heures = eec_individu.hhc
heures.value_counts()
heures.max()
heures.min()
heures.isnull().sum()


contrat_de_travail = eec_individu[['tpp', 'duhab', 'tppred']]
contrat_de_travail.tpp.value_counts(dropna = False)
contrat_de_travail.duhab.unique()
contrat_de_travail.groupby('tpp')['duhab'].value_counts(dropna = False)
contrat_de_travail.groupby('tppred')['duhab'].value_counts(dropna = False)



store = pd.HDFStore(
    '/home/benjello/openfisca/openfisca-france-data/openfisca_france_data/plugins/aggregates/amounts.h5'
    )

amounts = store['amounts']
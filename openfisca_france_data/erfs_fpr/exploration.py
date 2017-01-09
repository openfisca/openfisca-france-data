#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from __future__ import division

import numpy as np
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



individus = eec_individu
individus.chpub.unique()
assert individus.chpub.isin(range(0, 7)).all(), \
    "chpub n'est pas toujours dans l'intervalle [1, 6]\n{}".format(individus.chpub.value_counts())

individus.loc[individus.encadr == 0, 'encadr'] = 2
assert individus.encadr.isin(range(1, 3)).all(), \
    "encadr n'est pas toujours dans l'intervalle [1, 2]\n{}".format(individus.encadr.value_counts())

assert individus.prosa.isin(range(0, 10)).all(), \
    "prosa n'est pas toujours dans l'intervalle [0, 9]\n{}".format(individus.prosa.value_counts())

statut_values = [0, 11, 12, 13, 21, 22, 33, 34, 35, 43, 44, 45]
assert individus.statut.isin(statut_values).all(), \
    "statut n'est pas toujours dans l'ensemble {} des valeurs antendues.\n{}".format(
        statut_values,
        individus.statut.value_counts()
        )

assert individus.titc.isin(range(4)).all(), \
    "titc n'est pas toujours dans l'ensemble [0, 3] des valeurs antendues.\n{}".format(
        individus.statut.value_counts()
        )

chpub = individus.chpub
titc = individus.titc

# encadrement
assert 'cadre' not in individus.columns
individus['cadre'] = False
individus.loc[individus.prosa.isin([7, 8]), 'cadre'] = True
individus.loc[(individus.prosa == 9) & (individus.encadr == 1), 'cadre'] = True
cadre = (individus.statut == 35) & (chpub > 3) & individus.cadre
del individus['cadre']

# etat_stag = (chpub==1) & (titc == 1)
etat_titulaire = (chpub == 1) & (titc == 2)
etat_contractuel = (chpub == 1) & (titc == 3)

militaire = False  # TODO:

# collect_stag = (chpub==2) & (titc == 1)
collectivites_locales_titulaire = (chpub == 2) & (titc == 2)
collectivites_locales_contractuel = (chpub == 2) & (titc == 3)

# hosp_stag = (chpub==2)*(titc == 1)
hopital_titulaire = (chpub == 3) & (titc == 2)
hopital_contractuel = (chpub == 3) & (titc == 3)

contractuel = collectivites_locales_contractuel | hopital_contractuel | etat_contractuel

individus['categorie_salarie'] = np.select(
    [0, 1, 2, 3, 4, 5, 6],
    [0, cadre, etat_titulaire, militaire, collectivites_locales_titulaire, hopital_titulaire, contractuel]
    )


individus['categorie_salarie'] = (
    0 +
    1 * cadre +
    2 * etat_titulaire +
    3 * militaire +
    4 * collectivites_locales_titulaire +
    5 * hopital_titulaire +
    6 * contractuel
    )


individus['categorie_salarie2'] = (
     0.0 + 1.0 * cadre + 1.0 * etat_titulaire + militaire + collectivites_locales_titulaire +
     hopital_titulaire + contractuel
     )


individus['categorie_salarie'].unique()

df = pd.DataFrame([cadre, etat_titulaire]).transpose()

df

log.info('Les valeurs de categorie_salarie sont: \n {}'.format(
    individus['categorie_salarie'].value_counts(dropna = False)))
assert individus['categorie_salarie'].isin(range(10)).all(), \
    "categorie_salarie n'est pas toujours dans l'intervalle [0, 9]\n{}".format(
        individus.categorie_salarie.value_counts())
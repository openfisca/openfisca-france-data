#! /usr/bin/env python
# -*- coding: utf-8 -*-

import gc
import logging
import numpy as np

from openfisca_france_data.temporary import temporary_store_decorator
from openfisca_france_data.input_data_builders.build_openfisca_survey_data.step_01_pre_processing import (
    create_actrec_variable,
    create_variable_locataire,
    )
from openfisca_survey_manager.survey_collections import SurveyCollection


log = logging.getLogger(__name__)


@temporary_store_decorator(file_name = "erfs_fpr")
def merge_tables(temporary_store = None, year = None):
    assert temporary_store is not None
    # Chargement des tables
    erfs_fpr_survey_collection = SurveyCollection.load(collection = 'erfs_fpr')
    survey = erfs_fpr_survey_collection.get_survey('erfs_fpr_{}'.format(year))
    fpr_menage = survey.get_values(table = 'fpr_menage_2012_retropole')
    eec_menage = survey.get_values(table = 'fpr_mrf12e12t4')
    eec_individu = survey.get_values(table = 'fpr_irf12e12t4')
    fpr_individu = survey.get_values(table = 'fpr_indiv_2012_retropole')

    # Travail sur la cohérence entre les bases
    # Ménages et individus non apparies
    menages_non_apparies = eec_menage[
        ~(eec_menage.ident.isin(fpr_menage.ident.values))
        ].copy()
    individus_non_apparies = eec_menage[
        ~(eec_individu.ident.isin(fpr_individu.ident.values))
        ].copy()

    assert not menages_non_apparies.duplicated().any(), "{} menages sont dupliqués".format(
        menages_non_apparies.duplicated().sum())
    assert not individus_non_apparies.duplicated().any(), "{} individus sont dupliqués".format(
        individus_non_apparies.duplicated().sum())
    # individus_non_apparies = individus_non_apparies.drop_duplicates(subset = 'ident', take_last = True)

    difference = set(individus_non_apparies.ident).symmetric_difference(menages_non_apparies.ident)
    intersection = set(individus_non_apparies.ident) & set(menages_non_apparies.ident)
    log.info("There are {} differences and {} intersections".format(len(difference), len(intersection)))
    del individus_non_apparies, menages_non_apparies, difference, intersection
    gc.collect()

    # Fusion enquete emploi et source fiscale
    menagem = fpr_menage.merge(eec_menage)
    indivim = eec_individu.merge(fpr_individu, on = ['noindiv', 'ident', 'noi'], how = "inner")

    var_list = ([
        'acteu',
        'agepr',
        'cohab',
        'contra',
        'encadr',
        'forter',
        'lien',
        'mrec',
        'naia',
        'noicon',
        'noimer',
        'noiper',
        'prosa',
        'retrai',
        'rstg',
        'statut',
        'stc',
        'titc',
        'txtppb',
        ])

    for var in var_list:
        assert np.issubdtype(indivim[var].dtype, np.integer), \
            "Variable {} dtype is {} and should be an integer".format(
                var, indivim[var].dtype
                )

    create_actrec_variable(indivim)
    create_variable_locataire(menagem)
    menagem = menagem.merge(
        indivim.loc[indivim.lpr == 1, ['ident', 'ddipl']].copy()
        )

    temporary_store['menagem_{}'.format(year)] = menagem
    del eec_menage, fpr_menage, menagem
    gc.collect()
    temporary_store['indivim_{}'.format(year)] = indivim
    del eec_individu, fpr_individu


if __name__ == '__main__':
    import time
    start = time.time()
    logging.basicConfig(level = logging.INFO, filename = 'run_all.log', filemode = 'w')
    year = 2012
    merge_tables(year = year)
    # TODO: create_enfants_a_naitre(year = year)
    log.info("Script finished after {}".format(time.time() - start))
    print time.time() - start

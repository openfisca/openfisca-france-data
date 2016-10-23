#! /usr/bin/env python
# -*- coding: utf-8 -*-

import gc
import logging
import numpy as np

from openfisca_france_data.temporary import temporary_store_decorator
from openfisca_france_data.input_data_builders.build_openfisca_survey_data.step_01_pre_processing import (
    create_variable_locataire,
    )
from openfisca_survey_manager.survey_collections import SurveyCollection


log = logging.getLogger(__name__)


@temporary_store_decorator(file_name = "erfs_fpr")
def merge_tables(temporary_store = None, year = None):
    assert temporary_store is not None
    log.info("Chargement des tables des enquêtes")
    erfs_fpr_survey_collection = SurveyCollection.load(collection = 'erfs_fpr')
    survey = erfs_fpr_survey_collection.get_survey('erfs_fpr_{}'.format(year))
    fpr_menage = survey.get_values(table = 'fpr_menage_2012_retropole')
    eec_menage = survey.get_values(table = 'fpr_mrf12e12t4')
    eec_individu = survey.get_values(table = 'fpr_irf12e12t4')
    fpr_individu = survey.get_values(table = 'fpr_indiv_2012_retropole')

    # Fusion enquete emploi et source fiscale
    menages = fpr_menage.merge(eec_menage)
    individus = eec_individu.merge(fpr_individu, on = ['noindiv', 'ident', 'noi'], how = "inner")

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
        assert np.issubdtype(individus[var].dtype, np.integer), \
            "Variable {} dtype is {} and should be an integer".format(
                var, individus[var].dtype
                )

    create_variable_locataire(menages)
    menages = menages.merge(
        individus.loc[individus.lpr == 1, ['ident', 'ddipl']].copy()
        )

    temporary_store['menages_{}'.format(year)] = menages
    del eec_menage, fpr_menage, menages
    gc.collect()
    temporary_store['individus_{}'.format(year)] = individus
    del eec_individu, fpr_individu


def non_apparies(eec_individu, eec_menage, fpr_individu, fpr_menage):
    """
    Ménages et individus non apparies
    """
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



if __name__ == '__main__':
    import time
    start = time.time()
    logging.basicConfig(level = logging.INFO, filename = 'run_all.log', filemode = 'w')
    year = 2012
    merge_tables(year = year)
    # TODO: create_enfants_a_naitre(year = year)
    log.info("Script finished after {}".format(time.time() - start))
    print time.time() - start

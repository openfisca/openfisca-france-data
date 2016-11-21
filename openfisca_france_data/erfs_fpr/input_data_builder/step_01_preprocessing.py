#! /usr/bin/env python
# -*- coding: utf-8 -*-

import gc
import logging
import numpy as np

from openfisca_france_data.temporary import temporary_store_decorator
from openfisca_france_data.erfs.input_data_builder.step_01_pre_processing import (
    create_variable_locataire,
    )
from openfisca_survey_manager.survey_collections import SurveyCollection


log = logging.getLogger(__name__)


@temporary_store_decorator(file_name = "erfs_fpr")
def build_merged_dataframes(temporary_store = None, year = None):
    assert temporary_store is not None
    assert year is not None
    log.info("Chargement des tables des enquêtes")
    erfs_fpr_survey_collection = SurveyCollection.load(collection = 'erfs_fpr')
    yr = str(year)[-2:]  # 12 for 2012
    survey = erfs_fpr_survey_collection.get_survey('erfs_fpr_{}'.format(year))
    fpr_menage = survey.get_values(table = 'fpr_menage_{}_retropole'.format(year))
    eec_menage = survey.get_values(table = 'fpr_mrf{}e{}t4'.format(yr, yr))
    eec_individu = survey.get_values(table = 'fpr_irf{}e{}t4'.format(yr, yr))
    fpr_individu = survey.get_values(table = 'fpr_indiv_{}_retropole'.format(year))

    individus, menages = merge_tables(fpr_menage, eec_menage, eec_individu, fpr_individu, year)
    temporary_store['menages_{}'.format(year)] = menages
    del eec_menage, fpr_menage, menages
    gc.collect()
    temporary_store['individus_{}'.format(year)] = individus
    del eec_individu, fpr_individu


def merge_tables(fpr_menage = None, eec_menage = None, eec_individu = None, fpr_individu = None, year = None,
        skip_menage = False):
    assert (eec_individu is not None) and (fpr_individu is not None)
    log.info(u"""
Il y a {} individus dans fpr_individu
Il y a {} individus dans eec_individu
""".format(
        len(fpr_individu.noindiv.unique()),
        len(eec_individu.noindiv.unique()),
        ))

    # Fusion enquête emploi et source fiscale

    individus = eec_individu.merge(fpr_individu, on = ['noindiv', 'ident', 'noi'], how = "inner")
    check_naia_naim(individus, year)

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

    if not skip_menage:
        log.info(u"""
Il y a {} ménages dans fpr_menage
Il y a {} ménages dans eec_menage
""".format(
            len(fpr_menage.ident.unique()),
            len(eec_menage.ident.unique()),
        ))
        menages = fpr_menage.merge(eec_menage, on = 'ident', how = 'inner')
        create_variable_locataire(menages)
        menages = menages.merge(
            individus.loc[individus.lpr == 1, ['ident', 'ddipl']].copy()
            )
        log.info(u"""
Il y a {} ménages dans la base ménage fusionnée
""".format(len(menages.ident.unique())))
        #
    #
    log.info(u"""
Il y a {} ménages dans la base individus fusionnée
Il y a {} individus dans la base individus fusionnée
""".format(
        len(individus.ident.unique()),
        len(individus.noindiv.unique()),
        ))

    # Infos sur les non appariés
    if not skip_menage:
        non_apparies(eec_individu, eec_menage, fpr_individu, fpr_menage)

    if skip_menage:
        menages = None

    return individus, menages


def non_apparies(eec_individu, eec_menage, fpr_individu, fpr_menage):
    """
    Ménages et individus non apparies
    """
    menages_non_apparies = eec_menage[
        ~(eec_menage.ident.isin(fpr_menage.ident.values))
        ].copy()
    individus_non_apparies = eec_individu[
        ~(eec_individu.ident.isin(fpr_individu.ident.values))
        ].copy()

    assert not menages_non_apparies.duplicated().any(), "{} menages sont dupliqués".format(
        menages_non_apparies.duplicated().sum())
    assert not individus_non_apparies.duplicated().any(), "{} individus sont dupliqués".format(
        individus_non_apparies.duplicated().sum())

    individus_non_apparies = individus_non_apparies.drop_duplicates(subset = 'ident', keep = 'last')
    difference = set(individus_non_apparies.ident).symmetric_difference(menages_non_apparies.ident)
    intersection = set(individus_non_apparies.ident) & set(menages_non_apparies.ident)
    log.info(
        "Il y a {} differences et {} intersections entre les ménages non appariés et les individus non appariés".format
            (len(difference), len(intersection)))
    del individus_non_apparies, menages_non_apparies, difference, intersection
    gc.collect()


def check_naia_naim(individus, year):
    assert individus.naim.isin(range(1, 13)).all()
    good = ((year >= individus.naia) & (individus.naia > 1890))
    assertion = good.all()
    bad_idents = individus.loc[~good, 'ident'].unique()
    try:
        assert assertion, "Error: \n {}".format(
            individus.loc[
                individus.ident.isin(bad_idents),
                [
                    'ag',
                    'ident',
                    'lien',
                    'naia',
                    'naim',
                    'noi',
                    'noicon',
                    'noimer',
                    'noiper',
                    'prosa',
                    'retrai',
                    'rstg',
                    'statut',
                    'sexe',
                    'lien',
                    'lpr',
                    'chomage_i',
                    'pens_alim_recue_i',
                    'rag_i',
                    'retraites_i',
                    'ric_i',
                    'rnc_i',
                    'salaires_i',
                    ]
                ]
            )
    except AssertionError:
        if year == 2012:
            log.info('Fixing erroneous naia manually')
            individus.loc[
                (individus.ident == 12023304) & (individus.noi == 2),
                'naia'
                ] = 1954
            individus.loc[
                (individus.ident == 12041815) & (individus.noi == 1),
                'naia'
                ] = 2012 - 40
            #
        else:
            AssertionError('naia and naim have invalid values')


if __name__ == '__main__':
    import sys
    import time
    start = time.time()
    logging.basicConfig(level = logging.INFO, stream = sys.stdout)
    # logging.basicConfig(level = logging.INFO, filename = 'run_all.log', filemode = 'w')
    year = 2012
    build_merged_dataframes(year = year)
    # TODO: create_enfants_a_naitre(year = year)
    log.info("Script finished after {}".format(time.time() - start))
    print(time.time() - start)

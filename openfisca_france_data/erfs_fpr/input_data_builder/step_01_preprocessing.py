#! /usr/bin/env python
# -*- coding: utf-8 -*-

import gc
import logging
import numpy as np

from openfisca_survey_manager.temporary import temporary_store_decorator  # type: ignore
from openfisca_france_data.erfs.input_data_builder.step_01_pre_processing import (
    create_variable_locataire,
    )
from openfisca_survey_manager.survey_collections import SurveyCollection  # type: ignore


log = logging.getLogger(__name__)


@temporary_store_decorator(file_name = "erfs_fpr")
def build_merged_dataframes(temporary_store = None, year = None):
    assert temporary_store is not None
    assert year is not None
    log.debug("Chargement des tables des enquêtes")

    erfs_fpr_survey_collection = SurveyCollection.load(collection = "erfs_fpr")
    yr = str(year)[-2:]  # 12 for 2012
    add_suffix_retropole_years = [2012]

    survey = erfs_fpr_survey_collection.get_survey(f"erfs_fpr_{year}")
    eec_menage = survey.get_values(table = f"fpr_mrf{yr}e{yr}t4")
    eec_individu = survey.get_values(table = f"fpr_irf{yr}e{yr}t4")

    if year in add_suffix_retropole_years:
        fpr_individu = survey.get_values(table = f"fpr_indiv_{year}_retropole")
        fpr_menage = survey.get_values(table = f"fpr_menage_{year}_retropole")

    else:
        fpr_individu = survey.get_values(table = f"fpr_indiv_{year}")
        fpr_menage = survey.get_values(table = f"fpr_menage_{year}")

    individus, menages = merge_tables(fpr_menage, eec_menage, eec_individu, fpr_individu, year)
    temporary_store[f"menages_{year}"] = menages
    del eec_menage, fpr_menage, menages
    gc.collect()

    temporary_store[f"individus_{year}_post_01"] = individus
    del eec_individu, fpr_individu


def merge_tables(fpr_menage = None, eec_menage = None, eec_individu = None, fpr_individu = None, year = None,
        skip_menage = False):
    assert (eec_individu is not None) and (fpr_individu is not None)
    log.debug(u"""
Il y a {} individus dans fpr_individu
Il y a {} individus dans eec_individu
""".format(
        len(fpr_individu.noindiv.unique()),
        len(eec_individu.noindiv.unique()),
        ))

    # Fusion enquête emploi et source fiscale

    individus = eec_individu.merge(fpr_individu, on = ['noindiv', 'ident', 'noi'], how = "inner")
    check_naia_naim(individus, year)
    agepr = 'agepr' if year < 2013 else "ageprm"
    cohab = 'cohab' if year < 2013 else "coured"
    lien = 'lien' if year < 2013 else 'lienprm'  # TODO attention pas les mêmes modalités
    prosa = 'prosa' if year < 2013 else 'qprcent'  # TODO attention pas les mêmes modalités
    retrai = 'retrai' if year < 2013 else 'ret'  # TODO attention pas les mêmes modalités
    txtppb = 'txtppb' if year < 2013 else 'txtppred'  # TODO attention pas les mêmes modalités
    var_list = ([
        'acteu',
        agepr,
        cohab,
        'contra',
        'encadr',
        'forter',
        lien,
        'mrec',
        'naia',
        'noicon',
        'noimer',
        'noiper',
        prosa,
        retrai,
        'rstg',
        'statut',
        'stc',
        'titc',
        txtppb,
        ])

    for var in var_list:
        assert np.issubdtype(individus[var].dtype, np.integer), \
            "Variable {} dtype is {} and should be an integer".format(
                var, individus[var].dtype
                )

    if year >= 2013:
        individus['lpr'] = individus.lprm

    if not skip_menage:
        log.debug(u"""
Il y a {} ménages dans fpr_menage
Il y a {} ménages dans eec_menage
""".format(
            len(fpr_menage.ident.unique()),
            len(eec_menage.ident.unique()),
        ))
        common_variables = set(fpr_menage.columns).intersection(eec_menage.columns)
        log.debug(u"""
Les variables suivantes sont communes aux deux tables ménages:
  {}
""".format(common_variables))
        if 'th' in common_variables:
            fpr_menage.rename(columns = dict(th = 'taxe_habitation'), inplace = True)
            log.debug(u"La variable th de la table fpr_menage est renommée taxe_habitation")

        if 'tur5' in common_variables:
            fpr_menage.drop('tur5', axis = 1, inplace = True)
            log.debug(u"La variable tur5 redondante est retirée de la table fpr_menage")

        common_variables = set(fpr_menage.columns).intersection(eec_menage.columns)
        log.debug(u"""
Après renommage seules les variables suivantes sont communes aux deux tables ménages:
  {}
""".format(common_variables))
        menages = fpr_menage.merge(eec_menage, on = 'ident', how = 'inner')
        create_variable_locataire(menages)
        lprm = "lpr" if year < 2013 else "lprm"
        print(year, lprm)
        try:
            menages = menages.merge(
                individus.loc[individus[lprm] == 1, ["ident", "ddipl"]].copy()  # lpr (ou lprm) == 1 ==> C'est la Personne
                # de référence
                )
        except Exception:
            print(individus.dtypes)
            raise
        log.debug(u"""
Il y a {} ménages dans la base ménage fusionnée
""".format(len(menages.ident.unique())))
        #
    #
    log.debug(u"""
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
    log.debug(
        "Il y a {} differences et {} intersections entre les ménages non appariés et les individus non appariés".format(
            len(difference), len(intersection)))
    del individus_non_apparies, menages_non_apparies, difference, intersection
    gc.collect()


def check_naia_naim(individus, year):
    valid_naim = individus.naim.isin(range(1, 13))
    if not valid_naim.all():
        log.debug("There are wrong naim values:\n{}".format(
            individus.naim.value_counts(dropna = False))
            )
        individus.loc[
            individus.naim == 99,
            'naim'
            ] = 1  # np.random.randint(1, 13, sum(~valid_naim))

    assert individus.naim.isin(range(1, 13)).all()
    good = ((year >= individus.naia) & (individus.naia > 1890))
    assertion = good.all()
    bad_idents = individus.loc[~good, "ident"].unique()
    try:
        lpr = "lpr" if year < 2013 else "lprm"
        lien = "lien" if year < 2013 else "lienprm"  # TODO attention pas les mêmes modalités
        prosa = "prosa" if year < 2013 else "qprcent"  # TODO attention pas les mêmes modalités
        retrai = "retrai" if year < 2013 else "ret"  # TODO attention pas les mêmes modalités
        assert assertion, "Error: \n {}".format(
            individus.loc[
                individus.ident.isin(bad_idents),  # WTF is this table supposed to be? I changed the 'lien' in lien
                # and so on for other variables
                [
                    'ag',
                    'ident',
                    lien,
                    'naia',
                    'naim',
                    'noi',
                    'noicon',
                    'noimer',
                    'noiper',
                    prosa,
                    retrai,
                    'rstg',
                    'statut',
                    'sexe',
                    lpr,
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
            log.debug('Fixing erroneous naia manually')
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
    logging.basicConfig(level = logging.DEBUG, stream = sys.stdout)
    # logging.basicConfig(level = logging.DEBUG, filename = 'run_all.log', filemode = 'w')
    year = 2014
    build_merged_dataframes(year = year)
    # TODO: create_enfants_a_naitre(year = year)
    log.info("Script finished after {}".format(time.time() - start))
    print(time.time() - start)

#! /usr/bin/env python
import gc
import logging
import numpy as np

from openfisca_survey_manager.temporary import temporary_store_decorator  # type: ignore
from openfisca_france_data.erfs.input_data_builder.step_01_pre_processing import (
    create_variable_locataire,
    )
from openfisca_survey_manager.survey_collections import SurveyCollection  # type: ignore


log = logging.getLogger(__name__)

def build_table_by_name(year, erfs_fpr_survey_collection):
    """Infer names of the survey and data tables."""
    # where available, use harmoized data
    yr = str(year)[-2:]  # 12 for 2012
    yr1 = str(year + 1)[-2:]  # 13 for 2012
    add_suffix_retropole_years = [2012]
    survey = erfs_fpr_survey_collection.get_survey(f"erfs_fpr_{year}")
    tables = set(survey.tables.keys())

    table_by_name_stata = {
        "eec_individu": f"fpr_irf{yr}e{yr}t4" if year >= 2002 else f"fpr_irf{yr}e{yr1}",
        "eec_menage": f"fpr_mrf{yr}e{yr}t4" if year >= 2002 else f"fpr_mrf{yr}e{yr1}",
        "fpr_individu": f"fpr_indiv_{year}_retropole" if year in add_suffix_retropole_years else f"fpr_indiv_{year}",
        "fpr_menage": f"fpr_menage_{year}_retropole" if year in add_suffix_retropole_years else f"fpr_menage_{year}"
        }

    capitalized_table_by_name_stata = dict(
        (name, table.upper())
        for name, table in table_by_name_stata.items()
        )

    table_by_name_sas = {
        "eec_individu": "IRF",
        "eec_menage": "MRF",
        "fpr_individu": "Individu",
        "fpr_menage": "Menage"
        }

    if tables == set(table_by_name_stata.values()):
        table_by_name = table_by_name_stata.copy()

    elif tables == set(capitalized_table_by_name_stata.values()):
        table_by_name = capitalized_table_by_name_stata.copy()

    elif tables == set(table_by_name_sas.values()):
        table_by_name = table_by_name_sas.copy()

    else:
        raise ValueError(f"""
Incorrect table pattern: {tables} differs from:
    - stata: {set(table_by_name_stata.values())}
    - capitalized_stata: {set(capitalized_table_by_name_stata.values())}
    - sas: {set(table_by_name_sas.values())}
""")

    table_by_name["survey"] = f"erfs_fpr_{year}"

    return table_by_name


@temporary_store_decorator(file_name = "erfs_fpr")
def build_merged_dataframes(temporary_store = None, year = None):
    assert temporary_store is not None
    assert year is not None
    erfs_fpr_survey_collection = SurveyCollection.load(collection = "erfs_fpr",
        )

    # infer names of the survey and data tables
    table_by_name = build_table_by_name(year, erfs_fpr_survey_collection)

    log.debug("Loading tables for year {} [{}]".format(year, table_by_name))

    # load survey and tables
    survey = erfs_fpr_survey_collection.get_survey(table_by_name['survey'])

    eec_individu = survey.get_values(table = table_by_name['eec_individu'], ignorecase= True)
    eec_menage = survey.get_values(table = table_by_name['eec_menage'], ignorecase=True)

    fpr_individu = survey.get_values(table = table_by_name['fpr_individu'], ignorecase = True)
    fpr_menage = survey.get_values(table = table_by_name['fpr_menage'], ignorecase = True)

    # transform to lowercase
    for table in (fpr_menage, eec_menage, eec_individu, fpr_individu):
        table.columns = [k.lower() for k in table.columns]

    # check column names prior to 2002
    if 'nopers' in eec_individu.columns:
        eec_individu.rename(columns = {'nopers':'noindiv'}, inplace = True)

    # merge EEC and FPR tables
    individus, menages = merge_tables(fpr_menage, eec_menage, eec_individu, fpr_individu, year)

    # check name of revenus fonciers variable
    if 'rev_fonciers' in menages.columns:
        log.info('Renaming rev_fonciers to rev_fonciers_bruts.')
        menages.rename(columns = {'rev_fonciers':'rev_fonciers_bruts'}, inplace = True)

    # store household table
    temporary_store[f"menages_{year}"] = menages
    del eec_menage, fpr_menage, menages
    gc.collect()

    # store individual-level table
    temporary_store[f"individus_{year}_post_01"] = individus
    del eec_individu, fpr_individu
    gc.collect()


def merge_tables(fpr_menage = None, eec_menage = None, eec_individu = None, fpr_individu = None, year = None,
        skip_menage = False):

    # Step 1: Individual-Level Data

    assert (eec_individu is not None) and (fpr_individu is not None)

    # Fusion enquête emploi et source fiscale
    nobs = {}
    nobs['fpr_ind'] = len(fpr_individu.noindiv.unique())
    nobs['eec_ind'] = len(eec_individu.noindiv.unique())

    # check name of 'acteu' variable and rename if necessary
    if 'act' in eec_individu.columns:
        eec_individu.rename(columns = {'act':'acteu'}, inplace = True)


    log.debug('There are {} obs. in the FPR individual-level data [unique(noindiv)]'.format(nobs['fpr_ind']))
    log.debug('There are {} obs. in the EEC individual-level data [unique(noindiv)]'.format(nobs['eec_ind']))

    log.debug('Columns in FPR-Ind table: {}.'.format(','.join(fpr_individu.columns)))
    log.debug('Columns in EEC-Ind table: {}.'.format(','.join(eec_individu.columns)))

    # merge tables
    individus = eec_individu.merge(fpr_individu, on = ['noindiv', 'ident', 'noi'], how = "inner")

    nobs['fpr_eec_ind'] = len(individus.noindiv.unique())
    log.debug('There are {} obs. in the FPR-EEC individual-level data [unique(noindiv)]'.format(nobs['fpr_eec_ind']))

    # check TBD
    check_naia_naim(individus, year)

    # establish list of variables, taking into account differences over time
    agepr = 'agepr' if year < 2013 else "ageprm"
    cohab = 'cohab' if year < 2013 else "coured"
    lien = 'lien' if year < 2013 else 'lienprm'  # TODO attention pas les mêmes modalités
    prosa = 'prosa' if year < 2013 else 'qprcent'  # TODO attention pas les mêmes modalités
    retrai = 'retrai' if year < 2013 else 'ret'  # TODO attention pas les mêmes modalités
    txtppb = 'txtpp' if year < 2004 else 'txtppb' if year < 2013 else 'txtppred'  # TODO attention pas les mêmes modalités
                                                                                # + pas utilisee (cf step_03 todo_create)
    acteu = 'act' if year < 2005 else 'acteu' # mêmes modalités (définition a changé)
    cstot = 'dcstot' if year < 2002 else 'cstotr' # mêmes modalité (0 = non-réponse)
    var_list = ([
        acteu,
        agepr,
        cohab,
        'contra',
        'forter',
        lien,
        'mrec',
        'naia',
        'noicon',
        'noimer',
        prosa,
        #retrai,
        'rstg',
        'statut',
        'stc',
        'titc',
        txtppb,
        ]
         + (["noiper"] if "noiper" in individus.columns else [])
         + (["encadr"] if "encadr" in individus.columns else [])
         + ([retrai] if retrai in individus.columns else []) #n'existe pas avant 2004
         + ([cstot] if cstot in individus.columns else [])) #existe 1996 - 2003, remplace retrai


    # fill NAs and type conversion
    for var in var_list:
        individus[var]=individus[var].fillna(0)
        individus[var]=individus[var].astype(np.int64)
        assert np.issubdtype(individus[var].dtype, np.integer), \
            "Variable {} dtype is {} and should be an integer".format(
                var, individus[var].dtype
                )

    # TBD
    if year >= 2013:
        individus['lpr'] = individus.lprm

    # Step 2: Household-Level Data
    if not skip_menage:

        assert (eec_menage is not None) and (fpr_menage is not None)

        nobs['fpr_men'] = len(fpr_menage.ident.unique())
        nobs['eec_men'] = len(eec_menage.ident.unique())

        log.debug('There are {} obs. in the FPR household-level data [unique(ident)]'.format(nobs['fpr_men']))
        log.debug('There are {} obs. in the EEC household-level data [unique(ident)]'.format(nobs['eec_men']))

        common_variables_pre = set(fpr_menage.columns).intersection(eec_menage.columns)

        if 'th' in common_variables_pre:
            fpr_menage.rename(columns = dict(th = 'taxe_habitation'), inplace = True)
            log.debug("Household-level tables: Renamed variable 'th' to 'taxe_habitation'")

        if 'tur5' in common_variables_pre:
            fpr_menage.drop('tur5', axis = 1, inplace = True)
            log.debug("Household-level tables: Variable 'tur5' has been removed from household-level data (FPR)")

        common_variables = set(fpr_menage.columns).intersection(eec_menage.columns)
        dropped_vars = common_variables_pre.symmetric_difference(common_variables)

        log.debug('Common variables in the household-level tables: [{}]'.format(','.join(common_variables)))

        if len(dropped_vars) > 0:
            log.debug('These household-level variables have been dropped: [{}]'.format(','.join(dropped_vars)))
        else:
            log.debug('No household-level variables have been dropped.')

        # merge FPR and EEC household-level data
        menages = fpr_menage.merge(eec_menage, on = 'ident', how = 'inner')

        nobs['fpr_eec_men'] = len(menages.ident.unique())
        log.debug('There are {} obs. in the FPR-EEC household-level data [unique(noindiv)]'.format(nobs['fpr_eec_men']))

        create_variable_locataire(menages)

        lprm = "lpr" if year < 2013 else "lprm"

        try:
            menages = menages.merge(
                individus.loc[individus[lprm] == 1, ["ident", "ddipl"]].copy()
                # lpr (ou lprm) == 1 ==> C'est la personne de référence
                )
        except Exception:
            print(individus.dtypes)
            raise

        nobs['merge_men'] = len(menages.ident.unique())
        nobs['merge_ind'] = len(menages.ident.unique())

        log.debug('There are {} individuals [before: {}] and {} households [before: {}] in the merged data table.'.format(nobs['merge_ind'], nobs['fpr_eec_ind'], nobs['merge_men'], nobs['fpr_eec_men']))


    # Infos sur les non appariés
    if not skip_menage:
        non_apparies(eec_individu, eec_menage, fpr_individu, fpr_menage)

    if skip_menage:
        menages = None

    m = individus.select_dtypes(np.number)
    individus[m.columns]= individus[m.columns].fillna(0)
    individus[m.columns]= individus[m.columns].astype('int64')

    m = menages.select_dtypes(np.number)
    menages[m.columns]= menages[m.columns].fillna(0)
    menages[m.columns]= menages[m.columns].astype('int64')

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

    log.debug("There are {} differences and {} intersections between the unmerged households and individuals.".format(len(difference), len(intersection)))

    del individus_non_apparies, menages_non_apparies, difference, intersection
    gc.collect()


def check_naia_naim(individus, year):
    valid_naim = individus.naim.isin(range(1, 13))
    if not valid_naim.all():
        log.debug('There are incorrect month or birth values (naim). They will be reset to 1.')

        individus.loc[
            individus.naim == 99,
            'naim'
            ] = 1  # np.random.randint(1, 13, sum(~valid_naim))
        individus.loc[
            individus.naim == 0,
            'naim'
            ] = 1
        individus.loc[
            individus.naim.isnull(),
            'naim'
            ] = 1

    assert individus.naim.isin(range(1, 13)).all(), f"naim values: {individus.naim.unique()}"
    assert isinstance(year, int)
    bad_noindiv = individus.loc[
        ~((year >= individus.naia) & (individus.naia > 1890)),
        "noindiv",
        ].unique()

    for id in bad_noindiv:
        individus.loc[individus.noindiv == id,'naia'] = year - individus.loc[individus.noindiv == id, 'ageq']

    good = ((year >= individus.naia) & (individus.naia > 1890))
    assertion = good.all()
    bad_years = individus.loc[~good, "naia"].unique()
    bad_idents = individus.loc[~good, "ident"].unique()

    log.debug('There are incorrect years of birth [naia: {}] for individuals with ident [{}].'.format(';'.join([str(by) for by in bad_years]), ';'.join([str(bi) for bi in bad_idents])))

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
                    + (["noiper"] if "noiper" in individus.columns else [])
                ]
            )
    except AssertionError:
        if year == 2012:
            log.debug('Fixing erroneous years of birth [naia] manually for 2012.')
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
            AssertionError('There have been issues with the year and month of birth (naia, naim) that need to be checked manually.')


if __name__ == '__main__':
    import sys
    import time
    start = time.time()
    logging.basicConfig(level = logging.DEBUG, stream = sys.stdout)
    # logging.basicConfig(level = logging.DEBUG, filename = 'run_all.log', filemode = 'w')
    year = 2014
    build_merged_dataframes(year = year)
    # TODO: create_enfants_a_naitre(year = year)
    log.info("Step 1 finished after {}".format(time.time() - start))
    print(time.time() - start)

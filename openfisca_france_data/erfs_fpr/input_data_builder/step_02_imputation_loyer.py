#! /usr/bin/env python


"""This module provides routines to impute menage level variable to erfs_fpr data.
These variables are loyer and is some case zone_apl.

There are two ways of doing that:
 - using an external IPP imputation with iNSEE enquête logement done using stata
 - performing an inputation using R StatMatch library using rpy2 (to be extensively tested)

"""


# This step requires to have R installed with StatMatch library
# You'll also need rpy2 2.3x available at
# https://bitbucket.org/lgautier/rpy2/src/511312d70346f3f66c989e35443b2823e9b56d56?at=version_2.3.x
# (the version on python website is not compatible, working correctly for the debian's testing version)


import gc
import logging
import numpy
import os
import pandas as pd

# problem with rpy last version is not working
try:
    import rpy2
    import rpy2.robjects.pandas2ri
except ImportError:
    rpy2 = None

from openfisca_france_data.utils import (
    assert_variable_in_range, count_NA)
from openfisca_survey_manager.temporary import temporary_store_decorator
from openfisca_survey_manager import matching
from openfisca_survey_manager.statshelpers import mark_weighted_percentiles
from openfisca_survey_manager.survey_collections import SurveyCollection


log = logging.getLogger(__name__)


@temporary_store_decorator(file_name = 'erfs_fpr')
def merge_imputation_loyer(stata_file = None, temporary_store = None, year = None):
    assert year is not None
    assert stata_file is not None
    menages = temporary_store['menages_{}'.format(year)]
    logement = pd.read_stata(stata_file, preserve_dtypes = False, encoding = 'latin1')
    logement['ident12'] = logement.ident12.astype('int')
    logement.rename(columns = dict(zone_apl_EL = 'zone_apl', loyer_EL = 'loyer', ident12 = 'ident'), inplace = True)
    logement = logement[['zone_apl', 'loyer', 'ident']]
    menages = menages.merge(
        logement,
        left_on = 'ident',
        right_on = 'ident',
        how = 'left',
        )
    menages.rename(columns = dict(so = 'statut_occupation_logement'), inplace = True)
    temporary_store['menages_{}'.format(year)] = menages
    return menages


@temporary_store_decorator(file_name = 'erfs_fpr')
def imputation_loyer(temporary_store = None, year = None):
    assert temporary_store is not None
    assert year is not None

    kind = 'erfs_fpr'
    erf = create_comparable_erf_data_frame(temporary_store = temporary_store, year = year)
    logement = create_comparable_logement_data_frame(temporary_store = temporary_store, year = year)

    logement = logement.loc[logement.lmlm.notnull()].copy()
    log.info("Dropping {} observations form logement".format(logement.lmlm.isnull().sum()))

    if kind == 'erfs_fpr':
        allvars = [
            'deci',
            'hnph2',
            'magtr',
            'mcs8',
            'mdiplo',
            'mtybd',
            'statut_occupation',
            ]
    else:
        allvars = [
            'deci',
            'hnph2',
            'iaat_bis',
            'magtr',
            'mcs8',
            'mdiplo',
            'mtybd',
            'statut_occupation',
            'tu99_recoded',
            ]

    # TODO keep the variable indices

    erf = erf[allvars + ['ident', 'wprm']].copy()

    for variable in allvars:
        erf_unique_values = set(erf[variable].unique())
        logement_unique_values = set(logement[variable].unique())
        if not erf_unique_values <= logement_unique_values:
            print('''
                {} span wrong
                erf: {},
                logement: {}
                concerns {} observations
                '''.format(
                    variable,
                    erf_unique_values,
                    logement_unique_values,
                    erf[variable].isin(erf_unique_values - logement_unique_values).sum()
                    )
                )

    if kind == 'erfs_fpr':
        log.info("dropping {} erf observations".format(len(erf.query('mtybd == 0 | mcs8 == 0'))))
        erf = erf.query('mtybd != 0 & mcs8 != 0').copy()

    else:
        log.info("dropping {} erf observations".format(len(erf.query('iaat_bis == 0 | mtybd == 0 | mcs8 == 0'))))
        erf = erf.query('iaat_bis != 0 & mtybd != 0 & mcs8 != 0').copy()

    for variable in allvars:
        erf_unique_values = set(erf[variable].unique())
        logement_unique_values = set(logement[variable].unique())
        assert erf_unique_values <= logement_unique_values

    if kind == 'erfs_fpr':
        classes = "deci"
    else:
        classes = ['deci', 'tu99_recoded']

    matchvars = list(set(allvars) - set(classes))

    fill_erf_nnd, fill_erf_nnd_1 = matching.nnd_hotdeck_using_rpy2(
        receiver = erf,
        donor = logement,
        matching_variables = matchvars,
        z_variables = "lmlm",
        donor_classes = classes,
        )

    fill_erf_nnd.rename(columns = {'lmlm': 'loyer'}, inplace = True)

    loyers_imputes = fill_erf_nnd[['ident', 'loyer']].copy()
    menages = temporary_store['menages_{}'.format(year)]
    for loyer_var in ['loyer_x', 'loyer_y', 'loyer']:
        if loyer_var in menages.columns:
            del menages[loyer_var]

    menages = menages.merge(loyers_imputes, on = 'ident', how = 'left')
    assert 'loyer' in menages.columns, "La variable loyer n'est pas présente dans menages"

    temporary_store['menages_{}'.format(year)] = menages
    return


# Helpers


def prepare_erf_menage(temporary_store = None, year = None, kind = None):
    """
    Préparation de la sous-table ERFS de travail
    """
    assert temporary_store is not None
    assert year is not None

    log.info("Préparation de la table ménage de l'ERF")
    if kind == "erfs_fpr":
        # revenus_variables = [
        #     "chomage",
        #     "rag",
        #     "retraites",
        #     "rev_etranger"
        #     "rev_financier_prelev_lib_imputes",
        #     "rev_fonciers_bruts",
        #     "rev_valeurs_mobilieres_bruts",
        #     "ric",
        #     "rnc",
        #     ]
        revenus_variables = ["revdecm"]
        localisation_variables = [
            "pol10",
            "tau10",
            "tu10",
            ]
        nationalite_variables = [
            "nfr"
            ]
    else:
        revenus_variables = [
            "zperm",
            "zracm",
            "zragm",
            "zricm",
            "zrncm",
            "ztsam",
            ]
        localisation_variables = [
            "aai1",  # aai1: Année achèvement de l'immeuble (8 postes); Année achèvement de l'immeuble aai2
            "pol99",
            "tau99",
            "tu99",
            ]
        nationalite_variables = [
            "nat28pr",
            ]

    menage_variables = revenus_variables + localisation_variables + [
        "agpr",
        "cstotpr",
        "ident",
        "nb_uci",
        "nbenfc",
        "nbpiec",
        "reg",
        "so",
        "spr",
        "typmen5",
        "wprm",
        ]

    if year == 2008:  # Tau99 not present
        menage_variables = menage_variables.pop('tau99')

    erf_menages = temporary_store['menages_{}'.format(year)]
    erf_menages = erf_menages[menage_variables].copy()

    if kind == "erfs_fpr":
        erf_menages['revtot'] = 0  # TODO change this
    else:
        erf_menages['revtot'] = (
            erf_menages.zperm +
            erf_menages.zragm +
            erf_menages.zricm +
            erf_menages.zrncm +
            erf_menages.ztsam +
            erf_menages.zracm
            )

    # Niveau de vie de la personne de référence
    erf_menages['nvpr'] = erf_menages.revtot.astype('float') / erf_menages.nb_uci.astype('float')
    erf_menages.loc[erf_menages.nvpr < 0, 'nvpr'] = 0
    erf_menages.rename(columns = dict(so = 'statut_occupation'), inplace = True)

    log.info("Preparation de la tables individus de l'ERF")
    erfindm = temporary_store['individus_{}'.format(year)]
    erfindm = erfindm.loc[erfindm.lpr == 1, ['ident', 'dip11']].copy()

    log.info("Fusion des tables menage et individus de l'ERF")
    erf = erf_menages.merge(erfindm, on = 'ident', how = 'inner')
    del erf_menages, erfindm
    assert not erf.duplicated().any(), \
        "Il y a {} ménages dupliqués".format(erf.duplicated().sum())
    # erf = erf.drop_duplicates('ident')
    erf.rename(
        columns = {
            'dip11': 'mdiplo',
            'nat28pr': 'mnatio',
            'nbpiec': 'hnph2',
            },
        inplace = True,
        )
    # Extraction des seuls locataires
    erf = erf.loc[erf.statut_occupation.isin(range(3, 6))]
    gc.collect()

    return erf


def compute_decile(erf):
    dec, values = mark_weighted_percentiles(
        erf.nvpr.values,
        numpy.arange(1, 11),
        erf.wprm.values,
        2,
        return_quantiles = True
        )
    values.sort()
    erf['deci'] = (
        1 +
        (erf.nvpr > values[1]) +
        (erf.nvpr > values[2]) +
        (erf.nvpr > values[3]) +
        (erf.nvpr > values[4]) +
        (erf.nvpr > values[5]) +
        (erf.nvpr > values[6]) +
        (erf.nvpr > values[7]) +
        (erf.nvpr > values[8]) +
        (erf.nvpr > values[9])
        )
    assert erf.deci.isin(range(1, 11)).all()
    del dec, values
    gc.collect()


def format_variable_magtr(erf):
    """
    Format varaible magtr
    TODO describe using enquête logement
    """
    if (erf.agpr == '.').any():
        erf = erf[erf.agpr != '.'].copy()
    erf['agpr'] = erf.agpr.astype('int')
    erf['magtr'] = 3
    erf.loc[erf.agpr < 65, 'magtr'] = 2
    erf.loc[erf.agpr < 40, 'magtr'] = 1
    assert erf.magtr.isin(range(1, 5)).all()
    del erf['agpr']


def format_variable_mcs8(erf):
    assert erf.cstotpr.notnull().all()
    erf['mcs8'] = erf.cstotpr.astype('float') / 10.0
    erf.mcs8 = numpy.floor(erf.mcs8).astype('int')
    # TODO: assert erf.mcs8.isin(range(1, 9))
    del erf['cstotpr']
    assert erf.mcs8.isin(range(0, 9)).all()
    erf.loc[erf.mcs8.isin([4, 8]), 'mcs8'] = 4
    erf.loc[erf.mcs8.isin([5, 6, 7]), 'mcs8'] = 5
    # TODO: assert erf.mcs8.isin(range(1, 6)).all(), erf.mcs8.value_counts()
    assert erf.mcs8.isin(range(0, 6)).all()


def format_variable_mtybd(erf):
    erf['mtybd'] = 0
    erf.loc[(erf.typmen5 == 1) & (erf.spr != 2), 'mtybd'] = 1
    erf.loc[(erf.typmen5 == 1) & (erf.spr == 2), 'mtybd'] = 2
    erf.loc[erf.typmen5 == 5, 'mtybd'] = 3
    erf.loc[erf.typmen5 == 3, 'mtybd'] = 7
    erf.loc[erf.nbenfc == 1, 'mtybd'] = 4
    erf.loc[erf.nbenfc == 2, 'mtybd'] = 5
    erf.loc[erf.nbenfc >= 3, 'mtybd'] = 6
    erf.drop(
        ['nbenfc', 'spr', 'typmen5'],
        axis = 1,
        inplace = True,
        )
    assert erf.mtybd.isin(range(0, 8)).all()
    # TODO: assert erf.mtybd.isin(range(1,8)).all(),


def format_variable_hnph2(erf):
    # 3 logements ont 0 pièces !!
    erf.loc[erf.hnph2 < 1, 'hnph2'] = 1
    erf.loc[erf.hnph2 >= 6, 'hnph2'] = 6
    assert erf.hnph2.isin(range(1, 7)).all()
    # TODO: il reste un NA 2003
    #       il rest un NA en 2008  (Not rechecked)


def format_variable_mnatio(erf, kind = None):
    if kind == 'erfs_fpr':
        pass
    else:
        erf.loc[erf.mnatio == 10, 'mnatio'] = 1
        mnatio_range = range(11, 16) + range(21, 30) + range(31, 33) + range(41, 49) + range(51, 53) + [60] + [62]
        erf.loc[erf.mnatio.isin(mnatio_range), 'mnatio'] = 2
        assert erf.mnatio.isin(range(1, 3)).all(), 'valeurs pour mnatio\n{}'.format(erf.mnatio.value_counts())


def format_variable_iaat_bis(erf, kind = None):
    # iaat_bis is a contraction of iaat varaible of enquête logement
    # iaat_bis DATE D'ACHEVEMENT DE LA CONSTRUCTION
    # Voir http://www.insee.fr/fr/ppp/bases-de-donnees/fichiers_detail/eec10/doc/pdf/eec10_qlogement.pdf
    if kind == 'erfs_fpr':
        pass
    else:
        erf['iaat_bis'] = 0
        erf.loc[erf.aai1.isin([1, 2, 3]), 'iaat_bis'] = 1
        erf.loc[erf.aai1 == 4, 'iaat_bis'] = 2
        erf.loc[erf.aai1 == 5, 'iaat_bis'] = 3
        erf.loc[erf.aai1 == 6, 'iaat_bis'] = 4
        erf.loc[erf.aai1 == 7, 'iaat_bis'] = 5
        erf.loc[erf.aai1 == 8, 'iaat_bis'] = 6
        # TODO: assert erf.iaat_bis.isin(range(1, 7)).all()
        assert erf.iaat_bis.isin(range(0, 7)).all()


def format_variable_mdiplo(erf):
    erf.loc[erf.mdiplo.isin([71, ""]), 'mdiplo'] = 1
    erf.loc[erf.mdiplo.isin([70, 60, 50]), 'mdiplo'] = 2
    erf.loc[erf.mdiplo.isin([41, 42, 31, 33]), 'mdiplo'] = 3
    erf.loc[erf.mdiplo.isin([10, 11, 30]), 'mdiplo'] = 4
    # TODO: assert erf.mdiplo.isin(range(1, 5)).all()
    assert erf.mdiplo.isin(range(0, 5)).all()


def format_variable_tu99_recoded(erf, kind = None):
    if kind == 'erfs_fpr':
        # TODO use tu10
        pass
    else:
        erf['tu99_recoded'] = erf.tu99.copy()
        erf.loc[erf.tu99 == 0, 'tu99_recoded'] = 1
        erf.loc[erf.tu99.isin([1, 2, 3]), 'tu99_recoded'] = 2
        erf.loc[erf.tu99.isin([4, 5, 6]), 'tu99_recoded'] = 3
        erf.loc[erf.tu99 == 7, 'tu99_recoded'] = 4
        erf.loc[erf.tu99 == 8, 'tu99_recoded'] = 5
        assert erf.tu99_recoded.isin(range(1, 6)).all()
        del erf['tu99']


def check(erf, kind = None):
    erf.wprm = erf.wprm.astype('int')
    if kind == 'erfs_fpr':
        check_variables = [
            'hnph2',
            'magtr',
            'mcs8',
            'mdiplo',
            'mtybd',
            'statut_occupation',
            ]
    else:
        check_variables = [
            'hnph2',
            'iaat_bis',
            'magtr',
            'mcs8',
            'mdiplo',
            'mnatio',
            'mtybd',
            'statut_occupation',
            'tu99_recoded',
            ]
    gc.collect()

    non_integer_variables_to_filter = list()
    integer_variables_to_filter = list()
    for check_variable in check_variables:
        if erf[check_variable].isnull().any():
            log.info("Des valeurs NaN sont encore présentes dans la variable {} la table ERF".format(check_variable))
            non_integer_variables_to_filter.append(check_variable)

        if (erf[check_variable] == 0).any():
            if numpy.issubdtype(erf[check_variable].dtype, numpy.integer):
                log.info(
                    "Des valeurs nulles sont encore présentes dans la variable {} la table ERF".format(check_variable))
                integer_variables_to_filter.append(check_variable)

    assert len(non_integer_variables_to_filter) == 0, non_integer_variables_to_filter
    # assert len(integer_variables_to_filter) == 0, integer_variables_to_filter

    # On vérifie au final que l'on n'a pas de doublons d'individus
    assert not erf.ident.duplicated().any(), 'Il y a {} doublons'.format(erf.ident.duplicated().sum())
    return erf


def create_comparable_erf_data_frame(temporary_store = None, year = None):
    """
    Préparation des variables de la table ERFS qui serviront à l'imputation
    """
    assert temporary_store is not None
    assert year is not None

    erf = prepare_erf_menage(temporary_store = temporary_store, year = year, kind = "erfs_fpr")
    compute_decile(erf)  # deci = decile de revenu par unité de consommation

    # TODO: faire le lien avec men_vars,
    # il manque "pol99","reg","tau99" et ici on a en plus logt, 'nvpr','revtot','dip11','deci'
    variables = [
        'aai1',
        'agpr',
        'cstotpr',
        'deci',
        'dip11',
        'ident',
        'nat28pr',
        'nb_uci',
        'nbenfc',
        'nbpiec',
        'nvpr',
        'revtot',
        'spr',
        'statut_occupation',
        'tu99',
        'typmen5',
        'wprm',
        'zperm',
        'zracm',
        'zragm',
        'zricm',
        'zrncm',
        'ztsam',
        ]

    format_variable_magtr(erf)
    format_variable_mcs8(erf)
    format_variable_mtybd(erf)
    format_variable_hnph2(erf)

    format_variable_mnatio(erf, kind = 'erfs_fpr')
    format_variable_iaat_bis(erf, kind = 'erfs_fpr')
    format_variable_mdiplo(erf)
    format_variable_tu99_recoded(erf, kind = 'erfs_fpr')
    check(erf, kind = 'erfs_fpr')
    return erf


def create_comparable_logement_data_frame(temporary_store = None, year = None):
    assert temporary_store is not None
    assert year is not None
    logement_adresse_variables = ["gzc2"]
    logement_menage_variables = [
        "maa1at",
        "magtr",
        "mcs8",
        "mdiplo",
        "mrcho",
        "mrret",
        "mrsal",
        "mrtns",
        "mtybd",
        "muc1",
        "qex",
        "sec1",
        ]

    if year == 2003:
        logement_menage_variables.extend(["hnph2", "ident", "lmlm", "mnatior", "typse"])
        logement_adresse_variables.extend(["iaat", "ident", "tu99"])
    if year > 2005:  # and year < 2010:
        logement_menage_variables.extend(["idlog", "mnatio"])
        logement_adresse_variables.extend(["idlog"])  # pas de typse en 2006
        logement_logement_variables = ["hnph2", "iaat", "idlog", "lmlm", "tu99"]  # pas de typse en 2006

    # Travail sur la table logement
    # Table menage
    if year == 2003:
        year_lgt = 2003
    if year > 2005:  # and year < 2010:
        year_lgt = 2006

    logement_survey_collection = SurveyCollection.load(collection = 'logement')
    logement_survey = logement_survey_collection.get_survey('logement_{}'.format(year_lgt))

    log.info("Preparing logement menage table")

    try:
        logement_menage = logement_survey.get_values(
            table = "menage", variables = logement_menage_variables)
    except Exception:
        logement_menage = logement_survey.get_values(
            table = "menage1", variables = logement_menage_variables)

    logement_menage.rename(columns = {'idlog': 'ident'}, inplace = True)

    for revenus in ['mrcho', 'mrret', 'mrsal', 'mrtns']:
        logement_menage[revenus].fillna(0, inplace = True)

    logement_menage['revtot'] = (
        logement_menage.mrcho +
        logement_menage.mrret +
        logement_menage.mrsal +
        logement_menage.mrtns
        )
    # TODO : Virer les revenus négatifs ? mrtns :  118 revenus négatifs sur 42845 en 2006
    assert logement_menage.revtot.notnull().all()
    logement_menage['nvpr'] = 10.0 * logement_menage['revtot'] / logement_menage['muc1']

    assert logement_menage.qex.notnull().all()
    assert (logement_menage.qex > 0).all()

    dec, values = mark_weighted_percentiles(
        logement_menage['nvpr'].values,
        numpy.arange(1, 11),
        logement_menage['qex'].values,
        2,
        return_quantiles = True,
        )
    values.sort()
    logement_menage['deci'] = (
        1 +
        (logement_menage.nvpr > values[1]) +
        (logement_menage.nvpr > values[2]) +
        (logement_menage.nvpr > values[3]) +
        (logement_menage.nvpr > values[4]) +
        (logement_menage.nvpr > values[5]) +
        (logement_menage.nvpr > values[6]) +
        (logement_menage.nvpr > values[7]) +
        (logement_menage.nvpr > values[8]) +
        (logement_menage.nvpr > values[9])
        )

    del dec, values
    assert logement_menage['deci'].isin(range(1, 11)).all(), "Logement decile are out of range'"
    gc.collect()

    if year_lgt == 2006:
        log.info('Preparing logement logement table')
        try:
            lgtlgt = logement_survey.get_values(
                table = "lgt_logt", variables = logement_logement_variables)
        except Exception:
            lgtlgt = logement_survey.get_values(
                table = "logement", variables = logement_logement_variables)

        lgtlgt.rename(columns = {'idlog': 'ident'}, inplace = True)
        logement_menage = logement_menage.merge(lgtlgt, left_on = 'ident', right_on = 'ident', how = 'inner')
        del lgtlgt

    data = logement_menage.loc[logement_menage.sec1.isin([21, 22, 23, 24, 30])].copy()
    del logement_menage
    gc.collect()

    if year_lgt == 2006:
        data.rename(columns = {'mnatio': 'mnatior'}, inplace = True)

    data = data.loc[data.mnatior.notnull()].copy()
    data = data.loc[data.sec1.notnull()].copy()
    data['tmp'] = data.sec1.astype("int")
    data.loc[data.sec1.isin([21, 22, 23]), 'tmp'] = 3
    data.loc[data.sec1 == 24, 'tmp'] = 4
    data.loc[data.sec1 == 30, 'tmp'] = 5
    data['statut_occupation'] = data.tmp
    count_NA('statut_occupation', data)
    logement_menage = data[data.statut_occupation.notnull()].copy()

    # Table adresse
    log.info("Préparation de la table adresse de l'enquête logement")

    logement_adresse = logement_survey.get_values(table = "adresse", variables = logement_adresse_variables)
    logement_adresse.rename(columns = {'idlog': 'ident'}, inplace = True)

    log.info("Fusion des tables logement et ménage de l'enquête logement")
    Logement = logement_menage.merge(logement_adresse, on = 'ident', how = 'inner')

    Logement.loc[Logement.hnph2 >= 6, 'hnph2'] = 6
    Logement.loc[Logement.hnph2 < 1, 'hnph2'] = 1
    count_NA('hnph2', Logement)
    assert Logement.hnph2.notnull().any(), "Some hnph2 are null"
    # Logement=(Logement[Logement['hnph2'].notnull()]) # Mis en comment car 0 NA pour hnph2

    # On est dans la même étape within ici et par la suite ( cf code R )
    # TODO : ici problème je transforme les 07 en 7
    # car Python considère les 0n comme des nombres octaux ( < 08 ).
    # J'espère que ce n'est pas important.
    Logement.loc[Logement.mnatior.isin([0, 1]), 'mnatior'] = 1
    Logement.loc[Logement.mnatior.isin([2, 3, 4, 5, 6, 7, 8, 9, 10, 11]), 'mnatior'] = 2
    count_NA('mnatior', Logement)
    assert_variable_in_range('mnatior', [1, 3], Logement)

    Logement['iaat_bis'] = 0
    Logement.loc[Logement.iaat.isin([1, 2, 3, 4, 5]), 'iaat_bis'] = 1  # avant 1967
    Logement.loc[Logement.iaat == 6, 'iaat_bis'] = 2  # 1968 - 1974
    Logement.loc[Logement.iaat == 7, 'iaat_bis'] = 3  # 1975 - 1981
    Logement.loc[Logement.iaat == 8, 'iaat_bis'] = 4  # 1982 - 1989
    Logement.loc[Logement.iaat == 9, 'iaat_bis'] = 5  # 1990 - 1998
    Logement.loc[Logement.iaat == 10, 'iaat_bis'] = 6  # après 1999
    assert Logement.iaat_bis.isin(range(1, 7)).all()

    Logement.loc[Logement.mdiplo == 1, 'mdiplo'] = 1
    Logement.loc[Logement.mdiplo.isin([2, 3, 4]), 'mdiplo'] = 2
    Logement.loc[Logement.mdiplo.isin([5, 6, 7, 8]), 'mdiplo'] = 3
    Logement.loc[Logement.mdiplo == 9, 'mdiplo'] = 4
    Logement.loc[Logement.mdiplo.isnull(), 'mdiplo'] = 0
    # TODO: assert Logement.mdiplo.isin(range(1, 5)).all()
    assert Logement.mdiplo.isin(range(0, 5)).all()
    Logement.mdiplo = Logement.mdiplo.astype('int')

    Logement.loc[Logement.mtybd == 110, 'mtybd'] = 1
    Logement.loc[Logement.mtybd == 120, 'mtybd'] = 2
    Logement.loc[Logement.mtybd == 200, 'mtybd'] = 3
    Logement.loc[Logement.mtybd.isin([311, 321, 401]), 'mtybd'] = 4
    Logement.loc[Logement.mtybd.isin([312, 322, 402]), 'mtybd'] = 5
    Logement.loc[Logement.mtybd.isin([313, 323, 403]), 'mtybd'] = 6
    Logement.loc[Logement.mtybd == 400, 'mtybd'] = 7
    assert Logement.mtybd.isin(range(1, 8)).all()
    Logement.mtybd = Logement.mtybd.astype('int')

    Logement['tu99_recoded'] = Logement.tu99.copy()
    count_NA('tu99', Logement)
    Logement.loc[Logement.tu99 == 0, 'tu99_recoded'] = 1
    Logement.loc[Logement.tu99.isin([1, 2, 3]), 'tu99_recoded'] = 2
    Logement.loc[Logement.tu99.isin([4, 5, 6]), 'tu99_recoded'] = 3
    Logement.loc[Logement.tu99 == 7, 'tu99_recoded'] = 4
    Logement.loc[Logement.tu99 == 8, 'tu99_recoded'] = 5
    count_NA('tu99_recoded', Logement)
    assert_variable_in_range('tu99_recoded', [1, 6], Logement)

    Logement.loc[Logement.gzc2 == 1, 'gzc2'] = 1
    Logement.loc[Logement.gzc2.isin([2, 3, 4, 5, 6]), 'gzc2'] = 2
    Logement.loc[Logement.gzc2 == 7, 'gzc2'] = 3
    count_NA('gzc2', Logement)
    # TODO: assert_variable_in_range('gzc2', [1, 4], Logement)

    Logement.loc[Logement.magtr.isin([1, 2]), 'magtr'] = 1
    Logement.loc[Logement.magtr.isin([3, 4]), 'magtr'] = 2
    Logement.loc[Logement.magtr == 5, 'magtr'] = 3
    assert Logement.magtr.isin(range(1, 4)).all()

    # Logement.loc[Logement.mcs8 == 1, 'mcs8'] = 1
    # Logement.loc[Logement.mcs8 == 2, 'mcs8'] = 2
    # Logement.loc[Logement.mcs8 == 3, 'mcs8'] = 3
    Logement.loc[Logement.mcs8.isin([4, 8]), 'mcs8'] = 4
    Logement.loc[Logement.mcs8.isin([5, 6, 7]), 'mcs8'] = 5
    assert Logement.mcs8.isin(range(1, 6)).all()

    Logement['logloy'] = numpy.log(Logement['lmlm'].values)
    kept_variables = [
        'deci',
        'hnph2',
        'iaat_bis',
        'lmlm',
        'magtr',
        'mcs8',
        'mdiplo',
        'mtybd',
        'qex',
        'statut_occupation',
        'tu99_recoded',
        # 'ident',
        ]

    logement = Logement[kept_variables].copy()
    # logement.rename(columns = {'qex': 'wprm'}, inplace = True)
    return logement


if __name__ == '__main__':
    import sys
    logging.basicConfig(level = logging.INFO, stream = sys.stdout)
    year = 2012
    from openfisca_france_data.erfs_fpr.input_data_builder import step_01_preprocessing
    step_01_preprocessing.build_merged_dataframes(year = year)
    openfisca_survey_collection = SurveyCollection(name = 'openfisca')
    output_data_directory = openfisca_survey_collection.config.get('data', 'output_directory')
    stata_file = os.path.join(output_data_directory, 'log_men_ERFS.dta')
    menages = merge_imputation_loyer(stata_file = stata_file, year = year)

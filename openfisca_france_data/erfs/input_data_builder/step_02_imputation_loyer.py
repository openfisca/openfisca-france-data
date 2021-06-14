#! /usr/bin/env python


# This step requires to have R installed with StatMatch library
# You'll also need rpy2 2.3x available at
# https://bitbucket.org/lgautier/rpy2/src/511312d70346f3f66c989e35443b2823e9b56d56?at=version_2.3.x
# (the version on python website is not compatible, working correctly for the debian's testing version)


import gc
import logging
import numpy
import pandas

# problem with rpy last version is not working
try:
    import rpy2
    import rpy2.robjects.pandas2ri
except ImportError:
    rpy2 = None

from openfisca_france_data.utils import assert_variable_in_range, count_NA
from openfisca_survey_manager.temporary import temporary_store_decorator, save_hdf_r_readable
from openfisca_survey_manager.statshelpers import mark_weighted_percentiles
from openfisca_survey_manager.survey_collections import SurveyCollection


log = logging.getLogger(__name__)


def create_comparable_erf_data_frame(temporary_store = None, year = None):
    '''
    Imputation des loyers
    '''
    assert temporary_store is not None
    assert year is not None
    # Préparation des variables qui serviront à l'imputation
    # Année achèvement de l'immeuble (8 postes) aai1
    # Année achèvement de l'immeuble aai2
    menage_variables = [
        "aai1",
        "agpr",
        "cstotpr",
        "ident",
        "nat28pr",
        "nb_uci",
        "nbenfc",
        "nbpiec",
        "pol99",
        "reg",
        "so",
        "spr",
        "tau99",
        "tu99",
        "typmen5",
        "wprm",
        "zperm",
        "zracm",
        "zragm",
        "zricm",
        "zrncm",
        "ztsam",
        ]

    if year == 2008:  # Tau99 not present
        menage_variables = menage_variables.pop('tau99')

    # Travail sur la base ERF
    log.info("Préparation de la table ménage de l'ERF")
    erf_menages = temporary_store['menagem_{}'.format(year)]
    erf_menages = erf_menages[menage_variables].copy()

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
    erfindm = temporary_store['indivim_{}'.format(year)]
    erfindm = erfindm[['ident', 'dip11']][erfindm.lpr == 1].copy()

    log.info("Merging talbes menage et individus de l'ERF")
    erf = erfmenm.merge(erfindm, on = 'ident', how = 'inner')
    erf = erf.drop_duplicates('ident')

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

    # TODO: faire le lien avec men_vars,
    # il manque "pol99","reg","tau99" et ici on a en plus logt, 'nvpr','revtot','dip11','deci'
    erf = erf[
        [
            'ident',
            'ztsam',
            'zperm',
            'zragm',
            'zricm',
            'zrncm',
            'zracm',
            'nb_uci',
            'statut_occupation',
            'nbpiec',
            'typmen5',
            'spr',
            'nbenfc',
            'agpr',
            'cstotpr',
            'nat28pr',
            'tu99',
            'aai1',
            'wprm',
            'nvpr',
            'revtot',
            'dip11',
            'deci',
            ]
        ][erf.statut_occupation.isin(range(3, 6))].copy()

    erf.rename(
        columns = {
            'dip11': 'mdiplo',
            'nbpiec': 'hnph2',
            'nat28pr': 'mnatio',
            'nbpiec': 'hnph2',
            },
        inplace = True)

    if (erf.agpr == '.').any():
        erf = erf[erf.agpr != '.'].copy()

    erf['agpr'] = erf.agpr.astype('int')
    erf['magtr'] = 3
    erf.magtr[erf.agpr < 65] = 2
    erf.magtr[erf.agpr < 40] = 1
    assert erf.magtr.isin(range(1, 5)).all()

    assert erf.cstotpr.notnull().all()
    erf['mcs8'] = erf.cstotpr.astype('float') / 10.0
    erf.mcs8 = numpy.floor(erf.mcs8).astype('int')
    # TODO: assert erf.mcs8.isin(range(1, 9))
    assert erf.mcs8.isin(range(0, 9)).all()

    erf['mtybd'] = 0
    erf.mtybd[(erf.typmen5 == 1) & (erf.spr != 2)] = 1
    erf.mtybd[(erf.typmen5 == 1) & (erf.spr == 2)] = 2
    erf.mtybd[erf.typmen5 == 5] = 3
    erf.mtybd[erf.typmen5 == 3] = 7
    erf.mtybd[erf.nbenfc == 1] = 4
    erf.mtybd[erf.nbenfc == 2] = 5
    erf.mtybd[erf.nbenfc >= 3] = 6
    assert erf.mtybd.isin(range(0, 8)).all()
    # TODO: assert erf.mtybd.isin(range(1,8)).all(),

    # 3 logements ont 0 pièces !!
    erf.hnph2[erf.hnph2 < 1] = 1
    erf.hnph2[erf.hnph2 >= 6] = 6
    assert erf.hnph2.isin(range(1, 7)).all()

    # TODO: il reste un NA 2003
    #       il rest un NA en 2008  (Not rechecked)

    erf.mnatio[erf.mnatio == 10] = 1
    mnatio_range = range(11, 16) + range(21, 30) + range(31, 33) + range(41, 49) + range(51, 53) + [60] + [62]
    erf.mnatio[erf.mnatio.isin(mnatio_range)] = 2
    assert erf.mnatio.isin(range(1, 3)).all()

    # iaat_bis is a contraction of iaat varaible of enquête logement
    # iaat_bis DATE D'ACHEVEMENT DE LA CONSTRUCTION
    # Voir http://www.insee.fr/fr/ppp/bases-de-donnees/fichiers_detail/eec10/doc/pdf/eec10_qlogement.pdf
    erf['iaat_bis'] = 0
    erf.iaat_bis[erf.aai1.isin([1, 2, 3])] = 1
    erf.iaat_bis[erf.aai1 == 4] = 2
    erf.iaat_bis[erf.aai1 == 5] = 3
    erf.iaat_bis[erf.aai1 == 6] = 4
    erf.iaat_bis[erf.aai1 == 7] = 5
    erf.iaat_bis[erf.aai1 == 8] = 6
    # TODO: assert erf.iaat_bis.isin(range(1, 7)).all()
    assert erf.iaat_bis.isin(range(0, 7)).all()

    # Il reste un NA en 2003
    # reste un NA en 2008
    # TODO: comparer logement et erf pour être sur que cela colle ???
    erf.mdiplo[erf.mdiplo.isin([71, ""])] = 1
    erf.mdiplo[erf.mdiplo.isin([70, 60, 50])] = 2
    erf.mdiplo[erf.mdiplo.isin([41, 42, 31, 33])] = 3
    erf.mdiplo[erf.mdiplo.isin([10, 11, 30])] = 4
    # TODO: assert erf.mdiplo.isin(range(1, 5)).all()
    assert erf.mdiplo.isin(range(0, 5)).all()

    erf['tu99_recoded'] = erf.tu99.copy()
    erf.tu99_recoded[erf.tu99 == 0] = 1
    erf.tu99_recoded[erf.tu99.isin([1, 2, 3])] = 2
    erf.tu99_recoded[erf.tu99.isin([4, 5, 6])] = 3
    erf.tu99_recoded[erf.tu99 == 7] = 4
    erf.tu99_recoded[erf.tu99 == 8] = 5
    assert erf.tu99_recoded.isin(range(1, 6)).all()

    erf.loc[erf.mcs8.isin([4, 8]), 'mcs8'] = 4
    erf.loc[erf.mcs8.isin([5, 6, 7]), 'mcs8'] = 5
    # TODO: assert erf.mcs8.isin(range(1, 6)).all(), erf.mcs8.value_counts()
    assert erf.mcs8.isin(range(0, 6)).all()

    erf.wprm = erf.wprm.astype('int')

    for dropped_variable in ['agpr', 'cstotpr', 'nbenfc', 'spr', 'tu99', 'typmen5']:
        del erf[dropped_variable]
    gc.collect()

    check_variables = [
        'statut_occupation',
        'magtr',
        'mcs8',
        'mtybd',
        'hnph2',
        'mnatio',
        'iaat_bis',
        'mdiplo',
        'tu99_recoded',
        ]

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
    assert not erf['ident'].duplicated().any(), 'Il y a {} doublons'.format(erf['ident'].duplicated().sum())
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
    if year < 2010 and year > 2005:
        logement_menage_variables.extend(["idlog", "mnatio"])
        logement_adresse_variables.extend(["idlog"])  # pas de typse en 2006
        logement_logement_variables = ["hnph2", "iaat", "idlog", "lmlm", "tu99"]  # pas de typse en 2006

    # Travail sur la table logement
    # Table menage
    if year == 2003:
        year_lgt = 2003
    if year > 2005 and year < 2010:
        year_lgt = 2006

    logement_survey_collection = SurveyCollection.load(collection = 'logement')
    logement_survey = logement_survey_collection.get_survey('logement_{}'.format(year_lgt))

    log.info("Preparing logement menage table")

    try:
        logement_menage = logement_survey.get_values(
            table = "lgt_menage", variables = logement_menage_variables)
    except Exception:
        logement_menage = logement_survey.get_values(
            table = "menage1", variables = logement_menage_variables)

    logement_menage.rename(columns = {'idlog': 'ident'}, inplace = True)

    logement_menage['mrcho'].fillna(0, inplace = True)
    logement_menage['mrret'].fillna(0, inplace = True)
    logement_menage['mrsal'].fillna(0, inplace = True)
    logement_menage['mrtns'].fillna(0, inplace = True)
    logement_menage['revtot'] = (
        logement_menage['mrcho'] +
        logement_menage['mrret'] +
        logement_menage['mrsal'] +
        logement_menage['mrtns']
        )  # TODO : Virer les revenus négatifs ? mrtns :  118 revenus négatifs sur 42845 en 2006
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

    data = logement_menage[logement_menage['sec1'].isin([21, 22, 23, 24, 30])]
    del logement_menage
    gc.collect()

    if year_lgt == 2006:
        data.rename(columns = {'mnatio': 'mnatior'}, inplace = True)

    data = (data[data['mnatior'].notnull()])
    data = (data[data['sec1'].notnull()])
    data['tmp'] = data['sec1'].astype("int")
    data['tmp'][data['sec1'].isin([21, 22, 23])] = 3
    data['tmp'][data['sec1'] == 24] = 4
    data['tmp'][data['sec1'] == 30] = 5
    data['statut_occupation'] = data['tmp']
    count_NA('statut_occupation', data)
    data = (data[data['statut_occupation'].notnull()])
    logement_menage = data

    # Table adresse
    log.info("Préparation de la table adresse de l'enquête logement")

    logement_adresse = logement_survey.get_values(table = "adresse", variables = logement_adresse_variables)
    logement_adresse.rename(columns = {'idlog': 'ident'}, inplace = True)

    log.info("Fusion des tables logement et ménage de l'enquête logement")
    Logement = logement_menage.merge(logement_adresse, on = 'ident', how = 'inner')

    Logement.hnph2[Logement.hnph2 >= 6] = 6
    Logement.hnph2[Logement.hnph2 < 1] = 1
    count_NA('hnph2', Logement)
    assert Logement.hnph2.notnull().any(), "Some hnph2 are null"
#     Logement=(Logement[Logement['hnph2'].notnull()]) # Mis en comment car 0 NA pour hnph2

    # On est dans la même étape within ici et par la suite ( cf code R )
    # TODO : ici problème je transforme les 07 en 7
    # car Python considère les 0n comme des nombres octaux ( < 08 ).
    # J'espère que ce n'est pas important.
    Logement.mnatior[Logement['mnatior'].isin([0, 1])] = 1
    Logement.mnatior[Logement['mnatior'].isin([2, 3, 4, 5, 6, 7, 8, 9, 10, 11])] = 2
    count_NA('mnatior', Logement)
    assert_variable_in_range('mnatior', [1, 3], Logement)

    Logement['iaat_bis'] = 0
    Logement.iaat_bis[Logement.iaat.isin([1, 2, 3, 4, 5])] = 1  # avant 1967
    Logement.iaat_bis[Logement.iaat == 6] = 2  # 1968 - 1974
    Logement.iaat_bis[Logement.iaat == 7] = 3  # 1975 - 1981
    Logement.iaat_bis[Logement.iaat == 8] = 4  # 1982 - 1989
    Logement.iaat_bis[Logement.iaat == 9] = 5  # 1990 - 1998
    Logement.iaat_bis[Logement.iaat == 10] = 6  # après 1999
    assert Logement.iaat_bis.isin(range(1, 7)).all()

    Logement.mdiplo[Logement.mdiplo == 1] = 1
    Logement.mdiplo[Logement.mdiplo.isin([2, 3, 4])] = 2
    Logement.mdiplo[Logement.mdiplo.isin([5, 6, 7, 8])] = 3
    Logement.mdiplo[Logement.mdiplo == 9] = 4
    Logement.mdiplo[Logement.mdiplo.isnull()] = 0
    # TODO: assert Logement.mdiplo.isin(range(1, 5)).all()
    assert Logement.mdiplo.isin(range(0, 5)).all()
    Logement.mdiplo = Logement.mdiplo.astype('int')

    Logement.mtybd[Logement['mtybd'] == 110] = 1
    Logement.mtybd[Logement['mtybd'] == 120] = 2
    Logement.mtybd[Logement['mtybd'] == 200] = 3
    Logement.mtybd[Logement['mtybd'].isin([311, 321, 401])] = 4
    Logement.mtybd[Logement['mtybd'].isin([312, 322, 402])] = 5
    Logement.mtybd[Logement['mtybd'].isin([313, 323, 403])] = 6
    Logement.mtybd[Logement['mtybd'] == 400] = 7
    assert Logement.mtybd.isin(range(1, 8)).all()
    Logement.mtybd = Logement.mtybd.astype('int')

    Logement['tu99_recoded'] = Logement['tu99'].copy()
    count_NA('tu99', Logement)
    Logement.tu99_recoded[Logement['tu99'] == 0] = 1
    Logement.tu99_recoded[Logement['tu99'].isin([1, 2, 3])] = 2
    Logement.tu99_recoded[Logement['tu99'].isin([4, 5, 6])] = 3
    Logement.tu99_recoded[Logement['tu99'] == 7] = 4
    Logement.tu99_recoded[Logement['tu99'] == 8] = 5
    count_NA('tu99_recoded', Logement)
    assert_variable_in_range('tu99_recoded', [1, 6], Logement)

    Logement.gzc2[Logement['gzc2'] == 1] = 1
    Logement.gzc2[Logement['gzc2'].isin([2, 3, 4, 5, 6])] = 2
    Logement.gzc2[Logement['gzc2'] == 7] = 3
    count_NA('gzc2', Logement)
    # TODO: assert_variable_in_range('gzc2', [1, 4], Logement)

    Logement.magtr[Logement['magtr'].isin([1, 2])] = 1
    Logement.magtr[Logement['magtr'].isin([3, 4])] = 2
    Logement.magtr[Logement['magtr'] == 5] = 3
    assert Logement.magtr.isin(range(1, 4)).all()

    Logement['mcs8'][Logement['mcs8'] == 1] = 1
    Logement['mcs8'][Logement['mcs8'] == 2] = 2
    Logement['mcs8'][Logement['mcs8'] == 3] = 3
    Logement['mcs8'][Logement['mcs8'].isin([4, 8])] = 4
    Logement['mcs8'][Logement['mcs8'].isin([5, 6, 7])] = 5
    assert Logement.mcs8.isin(range(1, 6)).all()

    Logement['logloy'] = numpy.log(Logement['lmlm'].values)
    kept_variables = [
        'deci',
        'hnph2',
        'iaat_bis',
        # 'ident',
        'lmlm',
        'statut_occupation',
        'magtr',
        'mcs8',
        'mdiplo',
        'mtybd',
        'qex',
        'tu99_recoded',
        ]

    logement = Logement[kept_variables].copy()
    # logement.rename(columns = {'qex': 'wprm'}, inplace = True)
    return logement


@temporary_store_decorator(file_name = 'erfs')
def imputation_loyer(temporary_store = None, year = None):
    assert temporary_store is not None
    assert year is not None

    erf = create_comparable_erf_data_frame(temporary_store = temporary_store, year = year)

    logement = create_comparable_logement_data_frame(temporary_store = temporary_store, year = year)
    log.info("dropping {} observations form logement".format(logement.lmlm.isnull().sum()))
    logement = logement.loc[logement.lmlm.notnull()].copy()

    allvars = ['statut_occupation', 'hnph2', 'iaat_bis', 'mdiplo', 'mtybd', 'tu99_recoded', 'magtr', 'mcs8', 'deci']

    # TODO keep the variable indices
    erf = erf[allvars + ['wprm', 'ident']].copy()

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

    # print("dropping {} erf observations".format(len(erf.query('iaat_bis == 0 | mtybd == 0 | mcs8 == 0'))))
    erf = erf.query('iaat_bis != 0 & mtybd != 0 & mcs8 != 0').copy()

    for variable in allvars:
        erf_unique_values = set(erf[variable].unique())
        logement_unique_values = set(logement[variable].unique())
        assert erf_unique_values <= logement_unique_values

    classes = ['tu99_recoded', 'deci']
    matchvars = list(set(allvars) - set(classes))

    # Clean for unicode column names
    erf.rename(
        columns = dict([(col, str(col)) for col in erf.columns]),
        inplace = True
        )

    save_hdf_r_readable(erf.astype('int32'), file_name = "erf_imputation")
    save_hdf_r_readable(logement.astype('int32'), file_name = "logement_imputation")

    import subprocess
    import os
    os.path.abspath
    imputation_loyer_R = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'imputation_loyer.R')
    temporary_store_directory = os.path.dirname(temporary_store.filename)
    print(imputation_loyer_R)
    try:
        subprocess.check_call(['/usr/bin/Rscript', imputation_loyer_R, temporary_store_directory])
    except WindowsError:
        subprocess.check_call(['C:/Program Files/R/R-2.15.1/bin/x64/Rscript.exe',
            imputation_loyer_R, temporary_store_directory], shell = True)

    fill_erf_nnd = pandas.read_hdf(os.path.join(temporary_store_directory, 'imputation.h5'), 'fill_erf_nnd')
    assert set(fill_erf_nnd.ident) == set(erf.ident.astype('int32'))

#    rpy2.robjects.pandas2ri.activate()  # Permet à rpy2 de convertir les dataframes
#    sm = rpy2.robjects.packages.importr("StatMatch")  # Launch R you need to have StatMatch installed in R
#
#    out_nnd = sm.NND_hotdeck(
#        data_rec = erf.astype('int32'),
#        data_don = logement.astype('int32'),
#        match_vars = rpy2.robjects.vectors.StrVector(matchvars),
#        don_class = rpy2.robjects.vectors.StrVector(classes),
#        dist_fun = "Gower",
#        )
#
#
#    mtc_ids = out_nnd[0].reshape(len(erf), 2)  # Essential to avoid a bug in next line
#
#    fill_erf_nnd = sm.create_fused(
#        data_rec = erf.astype('int32'),
#        data_don = logement.astype('int32'),
#        mtc_ids = mtc_ids,
#        z_vars = "lmlm",
#        )

    fill_erf_nnd.rename(columns = {'lmlm': 'loyer'}, inplace = True)
    loyers_imputes = fill_erf_nnd[['ident', 'loyer']].copy()
    menagem = temporary_store['menagem_{}'.format(year)]
    for loyer_var in ['loyer_x', 'loyer_y', 'loyer']:
        if loyer_var in menagem.columns:
            del menagem[loyer_var]

    menagem = menagem.merge(loyers_imputes, on = 'ident', how = 'left')
    assert 'loyer' in menagem.columns, "La variable loyer n'est pas présente dans menagem"

    temporary_store['menagem_{}'.format(year)] = menagem
    return


if __name__ == '__main__':
    import sys
    logging.basicConfig(level = logging.INFO, stream = sys.stdout)
    year = 2009

    imputation_loyer(year = year)

    # menagem, erf, fill_erf_nnd, logement = imputation_loyer(year = year)

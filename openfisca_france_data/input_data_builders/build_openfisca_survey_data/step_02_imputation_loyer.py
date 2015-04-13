#! /usr/bin/env python
# -*- coding: utf-8 -*-


# OpenFisca -- A versatile microsimulation software
# By: OpenFisca Team <contact@openfisca.fr>
#
# Copyright (C) 2011, 2012, 2013, 2014, 2015 OpenFisca Team
# https://github.com/openfisca
#
# This file is part of OpenFisca.
#
# OpenFisca is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# OpenFisca is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


# This step requires to have R installed with StatMatch library
# You'll also need rpy2 2.3x available at
# https://bitbucket.org/lgautier/rpy2/src/511312d70346f3f66c989e35443b2823e9b56d56?at=version_2.3.x
# (the version on python website is not compatible, working correctly for the debian's testing version)


from __future__ import division


import gc
import logging
import numpy

# problem with rpy last version is not working
try:
    from rpy2.robjects.packages import importr
    import rpy2.robjects.vectors as vectors
except ImportError:
    importr = None
    vectors = None

from openfisca_france_data import default_config_files_directory as config_files_directory
from openfisca_france_data.input_data_builders.build_openfisca_survey_data.utils import (
    assert_variable_in_range, count_NA)
from openfisca_france_data.temporary import temporary_store_decorator
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
    menm_vars = [
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
        "tau99"
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
        menm_vars = menm_vars.pop('tau99')

    indm_vars = ["dip11", 'ident', "lpr", "noi"]
    # Travail sur la base ERF
    # Preparing ERF menages tables
    erfmenm = temporary_store.select('menagem_{}'.format(year))

    erfmenm['revtot'] = (
        erfmenm.ztsam + erfmenm.zperm + erfmenm.zragm + erfmenm.zricm + erfmenm.zrncm + erfmenm.zracm
        )
    # Niveau de vie de la personne de référence
    erfmenm['nvpr'] = erfmenm.revtot.astype('float') / erfmenm.nb_uci.astype('float')
    erfmenm.nvpr[erfmenm.nvpr < 0] = 0
    erfmenm['logt'] = erfmenm.so

    # Preparing ERF individuals table
    erfindm = temporary_store['indivim_{}'.format(year)]

    erfindm = erfindm[['ident', 'dip11']][erfindm.lpr == 1].copy()

    log.info(u"Merging talbes menage et individus de l'ERF")
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
    assert_variable_in_range('deci', [1, 11], erf)
    count_NA('deci', erf)
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
            'logt',
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
        ][erf['so'].isin(range(3, 6))]

    erf.rename(
        columns = {
            'aai1': 'iaat',
            'dip11': 'mdiplo',
            'nbpiec': 'hnph2',
            'nat28pr': 'mnatio',
            'nbpiec': 'hnph2',
            },
        inplace = True)

    count_NA('agpr', erf)
    if (erf.agpr == '.').any():
        erf = erf[erf.agpr != '.'].copy()

    erf['agpr'] = erf['agpr'].astype('int64')
    # TODO: moche, pourquoi créer deux variables quand une suffit ?
    erf['magtr'] = 3
    erf.magtr[erf.agpr < 65] = 2
    erf.magtr[erf.agpr < 40] = 1
    count_NA('magtr', erf)
    assert erf.magtr.isin(range(1, 5)).all()

    count_NA('cstotpr', erf)
    erf['mcs8'] = erf.cstotpr.astype('float') / 10.0
    erf.mcs8 = numpy.floor(erf.mcs8)
    count_NA('mcs8', erf)

    erf['mtybd'] = 0
    erf.mtybd[(erf.typmen5 == 1) & (erf.spr != 2)] = 1
    erf.mtybd[(erf.typmen5 == 1) & (erf.spr == 2)] = 2
    erf.mtybd[erf.typmen5 == 5] = 3
    erf.mtybd[erf.typmen5 == 3] = 7
    erf.mtybd[erf.nbenfc == 1] = 4
    erf.mtybd[erf.nbenfc == 2] = 5
    erf.mtybd[erf.nbenfc >= 3] = 6
    assert erf.mtybd.isin(range(0, 8)).all()
    # assert erf.mtybd.isin(range(1,8)).all() # bug,

    # TODO : 3 logements ont 0 pièces !!
    erf.hnph2[erf.hnph2 < 1] = 1
    erf.hnph2[erf.hnph2 >= 6] = 6
    count_NA('hnph2', erf)
    assert erf.hnph2.isin(range(1, 7)).all()

    # TODO: il reste un NA 2003
    #       il rest un NA en 2008  (Not rechecked)

    erf.mnatio[erf.mnatio == 10] = 1
    mnatio_range = range(11, 16) + range(21, 30) + range(31, 33) + range(41, 49) + range(51, 53) + [60] + [62]
    erf.mnatio[erf.mnatio.isin(mnatio_range)] = 2
    count_NA('mnatio', erf)
    assert erf.mnatio.isin(range(1, 3)).all()

    erf.iaat[erf.mnatio.isin([1, 2, 3])] = 1
    erf.iaat[erf.mnatio == 4] = 2
    erf.iaat[erf.mnatio == 5] = 3
    erf.iaat[erf.mnatio == 6] = 4
    erf.iaat[erf.mnatio == 7] = 5
    erf.iaat[erf.mnatio == 8] = 6
    assert erf.iaat.isin(range(1, 7)).all()

    # Il reste un NA en 2003
    # reste un NA en 2008
    # TODO: comparer logement et erf pour être sur que cela colle ???

    erf.mdiplo[erf.mdiplo.isin([71, ""])] = 1
    erf.mdiplo[erf.mdiplo.isin([70, 60, 50])] = 2
    erf.mdiplo[erf.mdiplo.isin([41, 42, 31, 33])] = 3
    erf.mdiplo[erf.mdiplo.isin([10, 11, 30])] = 4
    # TODO: assert erf.mdiplo.isin(range(0, 5)).all()
    assert erf.mdiplo.isin(range(0, 5)).all()

    erf['tu99_recoded'] = erf['tu99'].copy()
    erf.tu99_recoded[erf['tu99'] == 0] = 1
    erf.tu99_recoded[erf['tu99'].isin([1, 2, 3])] = 2
    erf.tu99_recoded[erf['tu99'].isin([4, 5, 6])] = 3
    erf.tu99_recoded[erf['tu99'] == 7] = 4
    erf.tu99_recoded[erf['tu99'] == 8] = 5
    count_NA('tu99_recoded', erf)
    assert erf.tu99_recoded.isin(range(1, 6)).all()

    erf.mcs8[erf.mcs8.isin([4, 8])] = 4
    erf.mcs8[erf.mcs8.isin([5, 6, 7])] = 5
    count_NA('mcs8', erf)

    # Drop NA = 0 values
    if not erf.mcs8.isin(range(1, 6)).all():
        erf = erf[erf.mcs8 != 0].copy()

    erf.wprm = erf.wprm.astype('int')
    count_NA('wprm', erf)

    for dropped_variable in ['agpr', 'cstotpr', 'nbenfc', 'spr', 'tu99', 'typmen5']:
        del erf[dropped_variable]
    gc.collect()

    check_variables = [
        'logt',
        'magtr',
        'mcs8',
        'mtybd',
        'hnph2',
        'mnatio',
        'iaat',
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

    erf = erf.dropna(subset = non_integer_variables_to_filter)
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

    logement_survey_collection = SurveyCollection.load(collection = 'logement',
            config_files_directory = config_files_directory)
    logement_survey = logement_survey_collection.get_survey('logement_{}'.format(year_lgt))

    log.info("Preparing logement menage table")

    logement_menage = logement_survey.get_values(table = "lgt_menage", variables = logement_menage_variables)
    logement_menage.rename(columns = {'idlog': 'ident'}, inplace = True)

    logement_menage['mrcho'].fillna(0, inplace = True)
    logement_menage['mrret'].fillna(0, inplace = True)
    logement_menage['mrsal'].fillna(0, inplace = True)
    logement_menage['mrtns'].fillna(0, inplace = True)
    logement_menage['revtot'] = logement_menage['mrcho'] + logement_menage ['mrret'] + logement_menage['mrsal'] + logement_menage['mrtns'] # TODO : Virer les revenus négatifs ? mrtns :  118 revenus négatifs sur 42845 en 2006
    count_NA('revtot', logement_menage)
    logement_menage['nvpr'] = 10.0 * logement_menage['revtot'] / logement_menage['muc1']

    count_NA('qex', logement_menage)
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
        lgtlgt = logement_survey.get_values(table = "lgt_logt", variables = logement_logement_variables)
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
    data['tmp'] = data['sec1'].astype("int64")
    data['tmp'][data['sec1'].isin([21, 22, 23])] = 3
    data['tmp'][data['sec1'] == 24] = 4
    data['tmp'][data['sec1'] == 30] = 5
    data['logt'] = data['tmp']
    count_NA('logt', data)
    data = (data[data['logt'].notnull()])
    logement_menage = data

    # Table adresse
    log.info(u"Préparation de la table adresse de l'enquête logement")

    logement_adresse = logement_survey.get_values(table = "adresse", variables = logement_adresse_variables)
    logement_adresse.rename(columns = {'idlog': 'ident'}, inplace = True)

    log.info(u"Fusion des tables logement et ménage de l'enquête logement")
    Logement = logement_menage.merge(logement_adresse, on = 'ident', how = 'inner')

    Logement.hnph2[Logement['hnph2'] >= 6] = 6
    Logement.hnph2[Logement['hnph2'] < 1] = 1
    count_NA('hnph2', Logement)
    assert Logement['hnph2'].notnull().any(), "Some hnph2 are null"
#     Logement=(Logement[Logement['hnph2'].notnull()]) # Mis en comment car 0 NA pour hnph2

    # On est dans la même étape within ici et par la suite ( cf code R )
    # TODO : ici problème je transforme les 07 en 7
    # car Python considère les 0n comme des nombres octaux ( < 08 ).
    # J'espère que ce n'est pas important.
    Logement.mnatior[Logement['mnatior'].isin([0, 1])] = 1
    Logement.mnatior[Logement['mnatior'].isin([2, 3, 4, 5, 6, 7, 8, 9, 10, 11])] = 2
    count_NA('mnatior', Logement)
    assert_variable_in_range('mnatior', [1, 3], Logement)

    Logement.iaat[Logement.iaat.isin([1, 2, 3, 4, 5])] = 1
    Logement.iaat[Logement.iaat == 6] = 2
    Logement.iaat[Logement.iaat == 7] = 3
    Logement.iaat[Logement.iaat == 8] = 4
    Logement.iaat[Logement.iaat == 9] = 5
    Logement.iaat[Logement.iaat == 10] = 6
    assert Logement.iaat.isin(range(1, 7)).all()

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
    count_NA('magtr', Logement)
    assert_variable_in_range('magtr', [1, 4], Logement)

    Logement['mcs8'][Logement['mcs8'] == 1] = 1
    Logement['mcs8'][Logement['mcs8'] == 2] = 2
    Logement['mcs8'][Logement['mcs8'] == 3] = 3
    Logement['mcs8'][Logement['mcs8'].isin([4, 8])] = 4
    Logement['mcs8'][Logement['mcs8'].isin([5, 6, 7])] = 5
    count_NA('mcs8', Logement)
    assert_variable_in_range('mcs8', [1, 6], Logement)

    Logement['logloy'] = numpy.log(Logement['lmlm'].values)
    #    Logement.dropna(
    #        axis = 0,
    #        subset = ['mdiplo', 'mtybd', 'magtr', 'mcs8', 'maa1at'],
    #        inplace = True)
    # Imputation des loyers proprement dite
    log.info('Compute imputed rents')
    kept_variables = [
        'deci',
        'hnph2',
        'iaat',
        'ident',
        'lmlm',
        'logt',
        'magtr',
        'mcs8',
        'mdiplo',
        'mtybd',
        'qex',
        'tu99_recoded',
        ]

    logement = Logement[kept_variables].copy()
    logement.rename(columns = {'qex': 'wprm'}, inplace = True)
    return logement


@temporary_store_decorator(config_files_directory = config_files_directory, file_name = 'erfs')
def imputation_loyer(temporary_store = None, year = None):
    assert temporary_store is not None
    assert year is not None

    erf = create_comparable_erf_data_frame(temporary_store = temporary_store, year = year)
    erf = erf[['logt', 'hnph2', 'iaat', 'mdiplo', 'mtybd', 'tu99_recoded', 'magtr', 'mcs8', 'deci', 'wprm', 'ident']]
    erf = erf.dropna(how = 'any')  # TODO : faire un check avant de dropper les lignes avec des NA

    logement = create_comparable_logement_data_frame(temporary_store = temporary_store, year = year)
    logement = logement.dropna(how = 'any')

    allvars = ['logt', 'hnph2', 'iaat', 'mdiplo', 'mtybd', 'tu99_recoded', 'magtr', 'mcs8', 'deci']
    classes = ['magtr', 'tu99_recoded']
    matchvars = list(set(allvars) - set(classes))

    for variable in allvars:
        count_NA(variable, logement)
        count_NA(variable, erf)

    erf['mcs8'] = erf['mcs8'].astype(int)

    rpy2.robjects.pandas2ri.activate()  # Permet à rpy2 de convertir les dataframes
    sm = importr("StatMatch")  # Launch R you need to have StatMatch installed in R

    out_nnd = sm.NND_hotdeck(data_rec = erf,
                             data_don = logement,
                             match_vars = vectors.StrVector(matchvars),
                             don_class = vectors.StrVector(classes),
                             dist_fun = "Gower",
                             )
    mtc_ids = out_nnd[0].reshape(len(erf), 2)  # Essential to avoid a bug in next line
    fill_erf_nnd = sm.create_fused(
        data_rec = erf,
        data_don = logement,
        mtc_ids = mtc_ids,
        z_vars = vectors.StrVector(["lmlm"]),
        )
    del allvars, matchvars, classes, out_nnd
    gc.collect()

    fill_erf_nnd.rename(columns = {'lmlm': 'loym'}, inplace = True)
    loy_imput = fill_erf_nnd[['ident', 'loym']]

    menagem = temporary_store['menagem_{}'.format(year)]

    for var in ["loym", "loym_x", "loym_y", "loym_z"]:
        if var in menagem:
            del menagem[var]
            log.info("{} have been deleted".format(var))

    menagem = menagem.merge(loy_imput, on = 'ident', how = 'left')
    assert 'loym' in menagem.columns, u"La variable loym n'est pas présente dans menagem"
    temporary_store['menagem_{}'.format(year)] = menagem

if __name__ == '__main__':
    import sys
    logging.basicConfig(level = logging.INFO, stream = sys.stdout)
    year = 2009
    imputation_loyer(year = year)
    log.info(u"étape 02 imputation des loyers terminée")
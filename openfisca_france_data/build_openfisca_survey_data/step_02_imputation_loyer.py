#! /usr/bin/env python
# -*- coding: utf-8 -*-


# OpenFisca -- A versatile microsimulation software
# By: OpenFisca Team <contact@openfisca.fr>
#
# Copyright (C) 2011, 2012, 2013, 2014 OpenFisca Team
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


from __future__ import division


import gc
import logging
import math


from numpy import arange, float64, floor, int64, maximum as NaN
from pandas import DataFrame
import pandas.rpy.common as com


from rpy2.robjects.packages import importr
import rpy2.robjects.pandas2ri
import rpy2.robjects.vectors as vectors


from openfisca_france.model.common import mark_weighted_percentiles
from openfisca_france_data.surveys import SurveyCollection
from openfisca_france_data.build_openfisca_survey_data import load_temp, save_temp
from openfisca_france_data.build_openfisca_survey_data.utilitaries import assert_variable_in_range, count_NA


log = logging.getLogger(__name__)


def create_comparable_erf_data_frame(year):
    '''
    Imputation des loyers
    '''

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
    LgtAdrVars = ["gzc2"]
    LgtMenVars = [
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
        LgtMenVars.extend(["hnph2", "ident", "lmlm", "mnatior", "typse"])
        LgtAdrVars.extend(["iaat", "ident", "tu99"])
    if year < 2010 and year > 2005:
        LgtMenVars.extend(["idlog", "mnatio"])
        LgtAdrVars.extend(["idlog"])  # pas de typse en 2006
        LgtLgtVars = ["hnph2", "iaat", "idlog", "lmlm", "tu99"]  # pas de typse en 2006

    ## Travail sur la base ERF
    #Preparing ERF menages tables

    erfmenm = load_temp(name = "menagem", year = year)
#     erfmenm = df.get_values(table="erf_menage",variables=menm_vars)
    erfmenm['revtot'] = (
        erfmenm['ztsam'] + erfmenm['zperm'] + erfmenm['zragm'] +
        erfmenm['zricm'] + erfmenm['zrncm'] + erfmenm['zracm']
        )
    # Niveau de vie de la personne de référence
    erfmenm['nvpr'] = erfmenm['revtot'].astype(float64) / erfmenm['nb_uci'].astype(float64)

    erfmenm['nvpr'][erfmenm['nvpr'] < 0] = 0
    erfmenm['logt'] = erfmenm['so']

    #Preparing ERF individuals table
    erfindm = load_temp(name = "indivim", year = year)
#     erfindm = df.get_values(table = "eec_indivi", variables = indm_vars)

    # TODO: clean this later
    erfindm['dip11'] = 0
    count_NA('dip11', erfindm) == 0
#     erfindm['dip11'] = 99
    erfindm = erfindm[['ident', 'dip11']][erfindm['lpr'] == 1].copy()

    print('merging erf menage and individu')
    erf = erfmenm.merge(erfindm, on ='ident', how='inner')
    erf = erf.drop_duplicates('ident')

    # control(erf) La colonne existe mais est vide,
    # on a du confondre cette colonne avec dip11 ?
    print erf['nvpr'].describe()
    print erf['wprm'].describe()
    dec, values = mark_weighted_percentiles(
        erf['nvpr'].values,
        arange(1,11),
        erf['wprm'].values,
        2,
        return_quantiles = True
        )
    values.sort()
    erf['deci'] = (
        1 +
        (erf['nvpr']>values[1]) +
        (erf['nvpr']>values[2]) +
        (erf['nvpr']>values[3]) +
        (erf['nvpr']>values[4]) +
        (erf['nvpr']>values[5]) +
        (erf['nvpr']>values[6]) +
        (erf['nvpr']>values[7]) +
        (erf['nvpr']>values[8]) +
        (erf['nvpr']>values[9])
        )
#    erf['deci'] = 1 + sum( (erf['nvpr'] > values[i]) for i in range(1,10) )

    # Problème : tous les individus sont soit dans le premier, soit dans le dernier décile. WTF
    assert_variable_in_range('deci',[1,11], erf)
    count_NA('deci',erf)
    del dec, values
    gc.collect()

    #TODO: faire le lien avec men_vars, il manque "pol99","reg","tau99" et ici on a en plus logt, 'nvpr','revtot','dip11','deci'
    erf = erf[['ident','ztsam','zperm','zragm','zricm','zrncm','zracm',
                 'nb_uci', 'logt' ,'nbpiec','typmen5','spr','nbenfc','agpr','cstotpr',
                 'nat28pr','tu99','aai1','wprm', 'nvpr','revtot','dip11','deci']][erf['so'].isin(range(3,6))]

    erf.rename(columns = {
        'aai1': 'iaat',
        'dip11': 'mdiplo',
        'nbpiec': 'hnph2',
        'nat28pr': 'mnatio',
        'nbpiec': 'hnph2',
        }, inplace = True)

    # TODO: ne traite pas les types comme dans R teste-les pour voir comment pandas les gère

    count_NA('agpr', erf)
    erf['agpr'] = erf['agpr'].astype('int64')
    # TODO: moche, pourquoi créer deux variables quand une suffit ?
    erf['magtr'] = 3
    erf['magtr'][erf['agpr'] < 65] = 2
    erf['magtr'][erf['agpr'] < 40] = 1
    count_NA('magtr', erf)
    assert erf['magtr'].isin(range(1, 5)).all()

    count_NA('cstotpr', erf)
    erf['mcs8'] = erf['cstotpr'].astype('float') / 10.0
    erf['mcs8'] = floor(erf['mcs8'])
    count_NA('mcs8', erf)

    # TODO il reste 41 NA's 2003
    erf['mtybd'] = NaN
    erf['mtybd'][(erf['typmen5'] == 1) & (erf['spr'] != 2)] = 1
    erf['mtybd'][(erf['typmen5'] == 1) & (erf['spr'] == 2)] = 2
    erf['mtybd'][erf['typmen5'] == 5] = 3
    erf['mtybd'][erf['typmen5'] == 3] = 7
    erf['mtybd'][erf['nbenfc'] == 1] = 4
    erf['mtybd'][erf['nbenfc'] == 2] = 5
    erf['mtybd'][erf['nbenfc'] >= 3] = 6
    count_NA('mtybd', erf)

#     print erf['mtybd'].dtype.fields
    #assert_variable_inrange('mtybd', [1,7], erf) # bug, on trouve 7.0 qui fait assert

    # TODO : 3 logements ont 0 pièces !!
    erf['hnph2'][erf['hnph2'] < 1] = 1
    erf['hnph2'][erf['hnph2'] >= 6] = 6
    count_NA('hnph2', erf)
    assert_variable_in_range('hnph2', [1, 7], erf)

# # TODO: il reste un NA 2003
# #       il rest un NA en 2008

    tmp = erf['mnatio']
    erf['mnatio'][erf['mnatio'] == 10] = 1
    mnatio_range = range(11, 16) + range(21, 30) + range(31, 33) + range(41, 49) + range(51, 53) + [60] + [62]
    erf['mnatio'][erf['mnatio'].isin(mnatio_range)] = 2

    count_NA('mnatio', erf)
    assert_variable_in_range('mnatio', [1, 3], erf)

    erf['iaat'][erf['mnatio'].isin([1,2,3])] = 1
    erf['iaat'][erf['mnatio'] == 4] = 2
    erf['iaat'][erf['mnatio'] == 5] = 3
    erf['iaat'][erf['mnatio'] == 6] = 4
    erf['iaat'][erf['mnatio'] == 7] = 5
    erf['iaat'][erf['mnatio'] == 8] = 6
    count_NA('iaat', erf)
    assert_variable_in_range('iaat', [1,7], erf)

# # Il reste un NA en 2003
# #    reste un NA en 2008
# table(erf$iaat, useNA="ifany")
    # TODO: comparer logement et erf pour ?tre sur que cela colle

    erf['mdiplo'][erf['mdiplo'].isin([71, ""])] = 1
    erf['mdiplo'][erf['mdiplo'].isin([70, 60, 50])] = 2
    erf['mdiplo'][erf['mdiplo'].isin([41, 42, 31, 33])] = 3
    erf['mdiplo'][erf['mdiplo'].isin([10, 11, 30])] = 4
    count_NA('mdiplo', erf)
    #assert_variable_inrange('mdiplo', [1,5], erf) # On a un 99 qui se balade
    erf['tu99_recoded'] = erf['tu99'].copy()
    erf['tu99_recoded'][erf['tu99'] == 0] = 1
    erf['tu99_recoded'][erf['tu99'].isin([1, 2, 3])] = 2
    erf['tu99_recoded'][erf['tu99'].isin([4, 5, 6])] = 3
    erf['tu99_recoded'][erf['tu99'] == 7] = 4
    erf['tu99_recoded'][erf['tu99'] == 8] = 5
    count_NA('tu99_recoded', erf)
    assert_variable_in_range('tu99_recoded', [1, 6], erf)

    erf.mcs8[erf['mcs8'].isin([4, 8])] = 4
    erf.mcs8[erf['mcs8'].isin([5, 6, 7])] = 5
    count_NA('mcs8', erf)

    if ~(erf.mcs8.isin(range(1, 6)).all()):
        log.info(u"{} valeurs de mcs8 sont hors de la plage allant de 1 à 5 ".format((~erf.mcs8.isin(range(1, 6))).sum()))
        log.info(u"Ces entrées sont éliminées")
        erf.dropna(subset = ['mcs8'], inplace = True)

    erf['wprm'] = erf['wprm'].astype('int64')
    count_NA('wprm', erf)

    for dropped_variable in ['agpr', 'cstotpr', 'nbenfc', 'spr', 'tu99', 'typmen5']:
        del erf[dropped_variable]
    gc.collect()

    assert erf[[
        'logt',
        'magtr',
        'mcs8',
        'mtybd',
        'hnph2',
        'mnatio',
        'iaat',
        'mdiplo',
        'tu99_recoded',
        ]].isnull().any(), "Des valeurs NaN sont encore présentes dans la table ERF"

    erf = erf.dropna(subset = [
        'logt',
        'magtr',
        'mcs8',
        'mtybd',
        'hnph2',
        'mnatio',
        'iaat',
        'mdiplo',
        'tu99_recoded',
        ])
    #On vérifie au final que l'on n'a pas de doublons d'individus
    assert erf['ident'].duplicated().any(), 'Il ya des doublons'
    return erf


def create_comparable_logement_data_frame(year):

    ## Travail sur la table logement
    # Table menage
    if year == 2003:
        year_lgt = 2003
    if year > 2005 and year < 2010:
        year_lgt = 2006

    logement_survey_collection = SurveyCollection.load(collection='logement')
    logement_survey = logement_survey_collection.surveys['logement_{}'.format(year)]



    log.info("Preparing logement menage table")
#     Lgtmen = load_temp(name = "indivim",year = year) # Je rajoute une étape bidon
    Lgtmen = logement_survey.get_values(table = "lgt_menage", variables = LgtMenVars)
    Lgtmen.rename(columns = {'idlog': 'ident'}, inplace = True)

    Lgtmen['mrcho'].fillna(0, inplace = True)
    Lgtmen['mrret'].fillna(0, inplace = True)
    Lgtmen['mrsal'].fillna(0, inplace = True)
    Lgtmen['mrtns'].fillna(0, inplace = True)
    Lgtmen['revtot'] = Lgtmen['mrcho'] + Lgtmen ['mrret'] + Lgtmen['mrsal'] + Lgtmen['mrtns'] # Virer les revenus négatifs ?
    count_NA('revtot', Lgtmen)
    Lgtmen['nvpr'] = 10.0 * Lgtmen['revtot'] / Lgtmen['muc1']

    count_NA('qex', Lgtmen)
    dec, values = mark_weighted_percentiles(
        Lgtmen['nvpr'].values,
        arange(1, 11),
        Lgtmen['qex'].values,
        2,
        return_quantiles = True,
        )
    values.sort()
    Lgtmen['deci'] = (1 +
        (Lgtmen['nvpr'] > values[1]) +
        (Lgtmen['nvpr'] > values[2]) +
        (Lgtmen['nvpr'] > values[3]) +
        (Lgtmen['nvpr'] > values[4]) +
        (Lgtmen['nvpr'] > values[5]) +
        (Lgtmen['nvpr'] > values[6]) +
        (Lgtmen['nvpr'] > values[7]) +
        (Lgtmen['nvpr'] > values[8]) +
        (Lgtmen['nvpr'] > values[9]))

    del dec, values
    assert Lgtmen['deci'].isin(range(1,11)), "Logement decile are out of range'"
    gc.collect()

    ##Table logement (pas en 2003 mais en 2006)
# str(lgtmen)
# if (year_lgt=="2006"){
#   message("preparing logement logement table")
#   lgtlgt <- LoadIn(lgtLgtFil,lgtLgtVars)
#   lgtlgt <- upData(lgtlgt, rename=renameidlgt)
#   lgtmen <- merge(lgtmen, lgtlgt, by.x="ident", by.y="ident")

    if year_lgt == 2006:
        log.info('Preparing logement logement table')
        lgtlgt = logement_survey.get_values(table = "lgt_logt", variables = LgtLgtVars)
        lgtlgt.rename(columns = {'idlog': 'ident'}, inplace = True)
        Lgtmen = Lgtmen.merge(lgtlgt, left_on = 'ident', right_on = 'ident', how = 'inner')
        del lgtlgt

    data = Lgtmen[Lgtmen['sec1'].isin([21, 22, 23, 24, 30])]
    del Lgtmen
    gc.collect()

    if year_lgt == 2006:
        data.rename(columns = {'mnatio': 'mnatior'}, inplace = True)

    data = (data[data['mnatior'].notnull()])
    data = (data[data['sec1'].notnull()])
    data['tmp'] = data['sec1'].astype(int64)
    data['tmp'][data['sec1'].isin([21,22,23])] = 3
    data['tmp'][data['sec1'] == 24] = 4
    data['tmp'][data['sec1'] == 30] = 5
    data['logt'] = data['tmp']
    count_NA('logt', data)
    data = (data[data['logt'].notnull()])
    Lgtmen = data

# ## Table adresse
    print "preparing logement adresse table"
# lgtadr <- LoadIn(lgtAdrFil,lgtAdrVars)
# lgtadr <- upData(lgtadr, rename=renameidlgt)
    # Je rajoute une étae bidon
    Lgtadr = logement_survey.get_values(table = "adresse", variables = LgtAdrVars)
    Lgtadr.rename(columns = {'idlog':'ident'}, inplace = True)

    log.info('Merging logement and menage tables')
    Logement = Lgtmen.merge(Lgtadr, on = 'ident', how = 'inner')

    Logement.hnph2[Logement['hnph2'] >= 6] = 6
    Logement.hnph2[Logement['hnph2'] < 1] = 1
    count_NA('hnph2', Logement)
    assert Logement['hnph2'].notnull().all(), "Some hnph2 are null"
#     Logement=(Logement[Logement['hnph2'].notnull()]) # Mis en comment car 0 NA pour hnph2

    # On est dans la même étape within ici et par la suite ( cf code R )
    # TODO : ici problème je transforme les 07 en 7
    # car Python considère les 0n comme des nombres octaux ( < 08 ).
    # J'espère que ce n'est pas important.
    Logement.mnatior[Logement['mnatior'].isin([0, 1])] = 1
    Logement.mnatior[Logement['mnatior'].isin([2, 3, 4, 5, 6, 7, 8, 9, 10, 11])] = 2
    count_NA('mnatior', Logement)
    assert_variable_inrange('mnatior', [1,3], Logement)

    Logement.iaat[Logement['iaat'].isin([1, 2, 3, 4, 5])] = 1
    Logement.iaat[Logement['iaat'] == 6] = 2
    Logement.iaat[Logement['iaat'] == 7] = 3
    Logement.iaat[Logement['iaat'] == 8] = 4
    Logement.iaat[Logement['iaat'] == 9] = 5
    Logement.iaat[Logement['iaat'] == 10] = 6
    count_NA('iaat', Logement)
    assert_variable_inrange('iaat', [1,7], Logement)

    Logement.mdiplo[Logement['mdiplo'] == 1] = 1
    Logement.mdiplo[Logement['mdiplo'].isin([2, 3, 4])] = 2
    Logement.mdiplo[Logement['mdiplo'].isin([5, 6, 7, 8])] = 3
    Logement.mdiplo[Logement['mdiplo'] == 9] = 4
    count_NA('mdiplo', Logement)
    assert_variable_inrange('mdiplo', [1,5], Logement)

    Logement.mtybd[Logement['mtybd'] == 110] = 1
    Logement.mtybd[Logement['mtybd'] == 120] = 2
    Logement.mtybd[Logement['mtybd'] == 200] = 3
    Logement.mtybd[Logement['mtybd'].isin([311, 321, 401])] = 4
    Logement.mtybd[Logement['mtybd'].isin([312, 322, 402])] = 5
    Logement.mtybd[Logement['mtybd'].isin([313, 323, 403])] = 6
    Logement.mtybd[Logement['mtybd'] == 400] = 7
    count_NA('mtybd', Logement)
    assert_variable_inrange('mtybd', [1,8], Logement)

    Logement['tu99_recoded'] = Logement['tu99'].copy()
    count_NA('tu99', Logement)
    Logement.tu99_recoded[Logement['tu99'] == 0] = 1
    Logement.tu99_recoded[Logement['tu99'].isin([1,2,3])] = 2
    Logement.tu99_recoded[Logement['tu99'].isin([4,5,6])] = 3
    Logement.tu99_recoded[Logement['tu99'] == 7] = 4
    Logement.tu99_recoded[Logement['tu99'] == 8] = 5
    count_NA('tu99_recoded', Logement)
    assert_variable_inrange('tu99_recoded', [1,6], Logement)

    Logement.gzc2[Logement['gzc2'] == 1] = 1
    Logement.gzc2[Logement['gzc2'].isin([2, 3, 4, 5, 6])] = 2
    Logement.gzc2[Logement['gzc2'] == 7] = 3
    count_NA('gzc2', Logement)
    assert_variable_inrange('gzc2', [1,4], Logement)

    Logement.magtr[Logement['magtr'].isin([1,2])] = 1
    Logement.magtr[Logement['magtr'].isin([3,4])] = 2
    Logement.magtr[Logement['magtr'] == 5] = 3
    count_NA('magtr', Logement)
    assert_variable_in_range('magtr', [1, 4], Logement)

    Logement['mcs8'][Logement['mcs8'] == 1] = 1
    Logement['mcs8'][Logement['mcs8'] == 2] = 2
    Logement['mcs8'][Logement['mcs8'] == 3] = 3
    Logement['mcs8'][Logement['mcs8'].isin([4,8])] = 4
    Logement['mcs8'][Logement['mcs8'].isin([5,6,7])] = 5
    count_NA('mcs8', Logement)
    assert_variable_in_range('mcs8', [1, 6], Logement)

    Logement['logloy'] = Logement['lmlm'].apply(lambda x: math.log(x))
    Logement = Logement.dropna(
        axis = 0,
        subset = ['mdiplo', 'mtybd', 'magtr', 'mcs8', 'maa1at'],
        inlace = True)
    ## Imputation des loyers proprement dite
    log.info('Compute imputed rents')
    kept_varaibels = [
        'lmlm',
        'logt' ,
        'hnph2' ,
        'iaat' ,
        'mdiplo',
        'mtybd' ,
        'tu99_recoded',
        'magtr',
        'mcs8',
        'deci',
        'ident'
        ]
    Logt = Logement[[]]
    Logt['wprm'] = Logement['qex'].copy()
    return Logt


def imputation_loyer(year):

    erf = create_comparable_erf_data_frame(year)
    erf = erf[['logt' , 'hnph2' , 'iaat' , 'mdiplo' , 'mtybd' , 'tu99_recoded' , 'magtr' , 'mcs8' , 'deci', 'wprm' , 'ident']]
    erf = erf.dropna(how = 'any') # Si j'ai bien compris ce que l'on fait en R : dropper les lignes avec des NA

    Logt = create_comparable_logement_data_frame(year)
    Logt = Logt.dropna(how = 'any')

    allvars = ['logt', 'hnph2', 'iaat', 'mdiplo', 'mtybd', 'tu99_recoded', 'magtr', 'mcs8', 'deci']
    classes = ['magtr', 'tu99_recoded']
    matchvars = list(set(allvars)-set(classes))
    erf['mcs8'] = erf['mcs8'].astype(int)

    rpy2.robjects.pandas2ri.activate()  # Permet à rpy2 de convertir les dataframes
    try:
        sm = importr("StatMatch")
    except:
        import os
        sm = importr("StatMatch", lib_loc = "/home/benjello/R/x86_64-pc-linux-gnu-library/3.1/StatMatch/")
    out_nnd = sm.NND_hotdeck(data_rec = erf,
                             data_don = Logt,
                             match_vars = vectors.StrVector(matchvars),
                             don_class = vectors.StrVector(classes),
                             dist_fun = "Gower",
                             )
    fill_erf_nnd = sm.create_fused(data_rec = erf,
                                   data_don = Logt,
                                   mtc_ids = out_nnd[0],
                                   z_vars = vectors.StrVector(["lmlm"]),
                                   )
    del allvars, matchvars, classes, out_nnd
    gc.collect()

    fill_erf_nnd = com.convert_robj(fill_erf_nnd)
    fill_erf_nnd = DataFrame(fill_erf_nnd)
    (fill_erf_nnd).rename(columns={'lmlm': 'loym'}, inplace = True)

    loy_imput = (fill_erf_nnd)[['ident', 'loym']]

    erfmenm = load_temp(name = "menagem", year = year)
    erfmenm = erfmenm.merge(loy_imput, on='ident', how='left')
    assert 'loym' in erfmenm.columns, 'No loym in erfmenm columns'
    save_temp(erfmenm, name = "menagem", year=year)

if __name__ == '__main__':
    import sys
    logging.basicConfig(level = logging.INFO, stream = sys.stdout)
    year = 2006
    imputation_loyer(year = year)


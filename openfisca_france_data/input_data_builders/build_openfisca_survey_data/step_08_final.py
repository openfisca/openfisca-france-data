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


from __future__ import division

import gc

import logging
import numpy as np
from numpy import where, NaN, random, unique
from pandas import read_csv
import os


from openfisca_france_data import default_config_files_directory as config_files_directory
from openfisca_france_data.temporary import temporary_store_decorator
from openfisca_france_data.input_data_builders.build_openfisca_survey_data.utils import (
    check_structure,
    control,
    id_formatter,
    print_id,
    rectify_dtype,
    set_variables_default_value,
    )

log = logging.getLogger(__name__)


@temporary_store_decorator(config_files_directory = config_files_directory, file_name = 'erfs')
def final(temporary_store = None, year = None, check = True):

    assert temporary_store is not None
    assert year is not None

    log.info(u'08_final: derniers réglages')

    # On définit comme célibataires les individus dont on n'a pas retrouvé la déclaration
    final = temporary_store['final_{}'.format(year)]
    log.info('check doublons'.format(len(final[final.duplicated(['noindiv'])])))
    final.statmarit = where(final.statmarit.isnull(), 2, final.statmarit)

    # activite des fip
    log.info('    gestion des FIP de final')
    final_fip = final[["choi", "sali", "alr", "rsti", "age"]][final.quelfic == "FIP"].copy()

    log.info(set(["choi", "sali", "alr", "rsti"]).difference(set(final_fip.columns)))
    for var in ["choi", "sali", "alr", "rsti"]:
        final_fip[var].fillna(0, inplace = True)
        assert final_fip[var].notnull().all(), "Some NaN are remaining in column {}".format(var)

    final_fip["activite"] = 2 # TODO comment choisr la valeur par défaut ?
    final_fip.activite = where(final_fip.choi > 0, 1, final_fip.activite)
    final_fip.activite = where(final_fip.sali > 0, 0, final_fip.activite)
    final_fip.activite = where(final_fip.age > 21, 2, final_fip.activite)  # ne peuvent être rattachés que les étudiants

    final.update(final_fip)
    temporary_store['final_{}'.format(year)] = final
    log.info("final has been updated with fip")

    menagem = temporary_store['menagem_{}'.format(year)]
    assert 'ident' in menagem.columns
    assert 'so' in menagem.columns
    menagem.rename(
        columns = dict(ident = "idmen", so = "statut_occupation"),
        inplace = True
        )
    menagem["cstotpragr"] = np.floor(menagem["cstotpr"] / 10)

    # 2008 tau99 removed TODO: check ! and check incidence
    variables = [
        "champm",
        "cstotpragr",
        "ddipl",
        "idmen",
        "nbinde",
        "pol99",
        "reg",
        "statut_occupation",
        "tau99",
        "tu99",
        "typmen15",
        "wprm",
        "zthabm",
        ]
    if year == 2008:
        variables.remove("tau99")
    famille_variables = ["m_afeamam", "m_agedm", "m_clcam", "m_colcam", 'm_mgamm', 'm_mgdomm']

    if 'loyer' in menagem.columns:
        variables.append('loyer')
# if ("naf16pr" %in% names(menagem)) {
#   naf16pr <- factor(menagem$naf16pr)
#   levels(naf16pr) <-  0:16
#   menagem$naf16pr <- as.character(naf16pr)
#   menagem[is.na(menagem$naf16pr), "naf16pr" ] <- "-1"  # Sans objet
#   variables <- c(variables,"naf16pr")
# } else if ("nafg17npr" %in% names(menagem)) {
#   # TODO: pb in 2008 with xx
#   if (year == "2008"){
#     menagem[ menagem$nafg17npr == "xx" & !is.na(menagem$nafg17npr), "nafg17npr"] <- "00"
#   }
#   nafg17npr <- factor(menagem$nafg17npr)
#   levels(nafg17npr) <-  0:17
#   menagem$nafg17npr <- as.character(nafg17npr)
#   menagem[is.na(menagem$nafg17npr), "nafg17npr" ] <- "-1"  # Sans objet
# }
#
#TODO: TODO: pytohn translation needed
#    if "naf16pr" in menagem.columns:
#        naf16pr <- factor(menagem$naf16pr)
#   levels(naf16pr) <-  0:16
#   menagem$naf16pr <- as.character(naf16pr)
#   menagem[is.na(menagem$naf16pr), "naf16pr" ] <- "-1"  # Sans objet
#   variables <- c(variables,"naf16pr")
# } else if ("nafg17npr" %in% names(menagem)) {
#   # TODO: pb in 2008 with xx
#   if (year == "2008"){
#     menagem[ menagem$nafg17npr == "xx" & !is.na(menagem$nafg17npr), "nafg17npr"] <- "00"
#   }
#   nafg17npr <- factor(menagem$nafg17npr)
#   levels(nafg17npr) <-  0:17
#   menagem$nafg17npr <- as.character(nafg17npr)
#   menagem[is.na(menagem$nafg17npr), "nafg17npr" ] <- "-1"  # Sans objet
# }
    # TODO: 2008tau99 is not present should be provided by 02_loy.... is it really needed
    all_variables = variables + famille_variables

    log.info("liste de toutes les variables : {}".format(all_variables))
    log.info(menagem.info())
    available_variables = list(set(all_variables).intersection(set(menagem.columns)))
    log.info("liste des variables à extraire de menagem: {}".format(available_variables))
    loyersMenages = menagem[available_variables].copy()
#
# # Recodage de typmen15: modalités de 1:15
# table(loyersMenages$typmen15, useNA="ifany")
# loyersMenages <- within(loyersMenages, {
#   typmen15[typmen15==10 ] <- 1
#   typmen15[typmen15==11 ] <- 2
#   typmen15[typmen15==21 ] <- 3
#   typmen15[typmen15==22 ] <- 4
#   typmen15[typmen15==23 ] <- 5
#   typmen15[typmen15==31 ] <- 6
#   typmen15[typmen15==32 ] <- 7
#   typmen15[typmen15==33 ] <- 8
#   typmen15[typmen15==41 ] <- 9
#   typmen15[typmen15==42 ] <- 10
#   typmen15[typmen15==43 ] <- 11
#   typmen15[typmen15==44 ] <- 12
#   typmen15[typmen15==51 ] <- 13
#   typmen15[typmen15==52 ] <- 14
#   typmen15[typmen15==53 ] <- 15
# })
#
#
# TODO: MBJ UNNECESSARY ?
#
# # Pb avec ddipl, pas de modalités 2: on décale les chaps >=3
# # Cependant on fait cela après avoir fait les traitement suivants
# table(loyersMenages$ddipl, useNA="ifany")
# # On convertit les ddipl en numeric
# loyersMenages$ddipl <- as.numeric(loyersMenages$ddipl)
# table(loyersMenages$ddipl, useNA="ifany")
# #   On met les non renseignés ie, NA et "" à sans diplome (modalité 7)
# loyersMenages[is.na(loyersMenages$ddipl), "ddipl"] <- 7
#
# loyersMenages[loyersMenages$ddipl>1, "ddipl"] <- loyersMenages$ddipl[loyersMenages$ddipl>1]-1
#
    log.info("loyersMenages \n {}".format(loyersMenages.info()))
    loyersMenages.ddipl = where(loyersMenages.ddipl.isnull(), 7, loyersMenages.ddipl)
    loyersMenages.ddipl = where(loyersMenages.ddipl > 1,
                                loyersMenages.ddipl - 1,
                                loyersMenages.ddipl)
    loyersMenages.ddipl = loyersMenages.ddipl.astype("int32")

    final['act5'] = NaN
    final.act5 = where(final.actrec == 1, 2, final.act5)  # indépendants
    final.act5 = where(final.actrec.isin([2, 3]), 1, final.act5)  # salariés

    final.act5 = where(final.actrec == 4, 3, final.act5)  # chômeur
    final.act5 = where(final.actrec == 7, 4, final.act5)  # retraité
    final.act5 = where(final.actrec == 8, 5, final.act5)  # autres inactifs

    log.info("{}".format(final.act5.value_counts()))

#     assert final.act5.notnull().all(), 'there are NaN inside final.act5'
# final$wprm <- NULL # with the intention to extract wprm from menage to deal with FIPs
# final$taxe_habitation <- final$zthabm # rename zthabm to taxe_habitation
# final$zthabm <- NULL
#
# final2 <- merge(final, loyersMenages, by="idmen", all.x=TRUE)
    log.info('    création de final2')
    del final["wprm"]
    gc.collect()
    final.rename(columns = dict(zthabm = "taxe_habitation"), inplace = True)  # rename zthabm to taxe_habitation
    final2 = final.merge(loyersMenages, on = "idmen", how = "left")  # TODO: Check
    log.info("{}".format(loyersMenages.head()))
    gc.collect()
    print_id(final2)
# # TODO: merging with patrimoine
    log.info('    traitement des zones apl')
    import pkg_resources
    openfisca_france_data_location = pkg_resources.get_distribution('openfisca-france-data').location
    zone_apl_imputation_data_file_path = os.path.join(
        openfisca_france_data_location,
        'openfisca_france_data',
        'zone_apl_data',
        'zone_apl',
        'zone_apl_imputation_data.csv',
        )
    apl_imp = read_csv(zone_apl_imputation_data_file_path)

    log.info("{}".format(apl_imp.head(10)))
    if year == 2008:
        zone_apl = final2.xs(["tu99", "pol99", "reg"], axis = 1)
    else:
        zone_apl = final2.xs(["tu99", "pol99", "tau99", "reg"], axis = 1)

    for i in range(len(apl_imp["TU99"])):
        tu = apl_imp["TU99"][i]
        pol = apl_imp["POL99"][i]
        tau = apl_imp["TAU99"][i]
        reg = apl_imp["REG"][i]

    if year == 2008:
        indices = (final2["tu99"] == tu) & (final2["pol99"] == pol) & (final2["reg"] == reg)
        selection = (apl_imp["TU99"] == tu) & (apl_imp["POL99"] == pol) & (apl_imp["REG"] == reg)
    else:
        indices = (final2["tu99"] == tu) & (final2["pol99"] == pol) & (final2["tau99"] == tau) & (final2["reg"] == reg)
        selection = (
            (apl_imp["TU99"] == tu) &
            (apl_imp["POL99"] == pol) &
            (apl_imp["TAU99"] == tau) &
            (apl_imp["REG"] == reg)
            )

    z = random.uniform(size=indices.sum())
    log.info(len(z))
    log.info(len(indices))
    log.info(len(indices) / len(z))
    probs = apl_imp[["proba_zone1", "proba_zone2"]][selection].copy()
    log.info(probs)
    log.info(probs['proba_zone1'].values)
    proba_zone_1 = probs['proba_zone1'].values[0]
    proba_zone_2 = probs['proba_zone2'].values[0]

    final2["zone_apl"] = 3
    final2["zone_apl"][indices] = (
        1 + (z > proba_zone_1) + (z > (proba_zone_1 + proba_zone_2))
        )
    del indices, probs

    log.info('    performing cleaning on final2')
    log.info('{} sali nuls'.format(len(final2[final2['sali'].isnull()])))
    log.info("{} individus d'âges nuls".format(len(final2[final2.age.isnull()])))
    log.info("longueur de final2 avant purge : {}".format(len(final2)))
#     columns_w_nan = []
#     for col in final2.columns:
#         if final2[final2['idfoy'].notnull()][col].isnull().any() and not final2[col].isnull().all():
#             columns_w_nan.append(col)
#     print columns_w_nan
    log.info('check doublons : {}'.format(len(final2[final2.duplicated(['noindiv'])])))
    log.info("{}".format(final2.age.isnull().sum()))

#     print final2.loc[final2.duplicated('noindiv'), ['noindiv', 'quifam']].to_string()
    #TODO: JS: des chefs de famille et conjoints en double il faut trouver la source des ces doublons !
#     final2 = final2.drop_duplicates(['noindiv'])

    final2 = final2[~(final2.age.isnull())]
    log.info(u"longueur de final2 après purge: {}".format(len(final2)))
    print_id(final2)

#
# # var <- names(foyer)
# #a1 <- c('f7rb', 'f7ra', 'f7gx', 'f2aa', 'f7gt', 'f2an', 'f2am', 'f7gw', 'f7gs', 'f8td', 'f7nz', 'f1br', 'f7jy', 'f7cu', 'f7xi', 'f7xo', 'f7xn', 'f7xw', 'f7xy', 'f6hj', 'f7qt', 'f7ql', 'f7qm', 'f7qd', 'f7qb', 'f7qc', 'f1ar', 'f7my', 'f3vv', 'f3vu', 'f3vt', 'f7gu', 'f3vd', 'f2al', 'f2bh', 'f7fm', 'f8uy', 'f7td', 'f7gv', 'f7is', 'f7iy', 'f7il', 'f7im', 'f7ij', 'f7ik', 'f1er', 'f7wl', 'f7wk', 'f7we', 'f6eh', 'f7la', 'f7uh', 'f7ly', 'f8wy', 'f8wx', 'f8wv', 'f7sb', 'f7sc', 'f7sd', 'f7se', 'f7sf', 'f7sh', 'f7si',  'f1dr', 'f7hs', 'f7hr', 'f7hy', 'f7hk', 'f7hj', 'f7hm', 'f7hl', 'f7ho', 'f7hn', 'f4gc', 'f4gb', 'f4ga', 'f4gg', 'f4gf', 'f4ge', 'f7vz', 'f7vy', 'f7vx', 'f7vw', 'f7xe', 'f6aa', 'f1cr', 'f7ka', 'f7ky', 'f7db', 'f7dq', 'f2da')
# #a2 <- setdiff(a1,names(foyer))
# #b1 <- c('pondfin', 'alt', 'hsup', 'ass_mat', 'zone_apl', 'inactif', 'ass', 'aer', 'code_postal', 'activite', 'type_sal', 'jour_xyz', 'boursier', 'etr', 'partiel1', 'partiel2', 'empl_dir', 'gar_dom', 'categ_inv', 'opt_colca', 'csg_taux_plein','coloc')
# # hsup feuille d'impot
# # boursier pas dispo
# # inactif etc : extraire cela des donn?es clca etc
#
# # tester activit? car 0 vaut actif
# table(is.na(final2$activite),useNA="ifany")
#
# saveTmp(final2, file= "final2.Rdata")

    control(final2, debug = True)
    log.info(final2.age.isnull().sum())
    final2 = final2.drop_duplicates(subset = 'noindiv')

    log.info('    Filter to manage the new 3-tables structures:')
    # On récupère les foyer, famille, ménages qui ont un chef :
    liste_men = unique(final2.loc[final2['quimen'] == 0, 'idmen'].values)
    liste_fam = unique(final2.loc[final2['quifam'] == 0, 'idfam'].values)
    liste_foy = unique(final2.loc[final2['quifoy'] == 0, 'idfoy'].values)

    #On ne conserve dans final2 que ces foyers là :
    log.info('final2 avant le filtrage {}'.format(len(final2)))
    final2 = final2.loc[final2.idmen.isin(liste_men)]
    final2 = final2.loc[final2.idfam.isin(liste_fam)]
    final2 = final2.loc[final2.idfoy.isin(liste_foy)]
    log.info('final2 après le filtrage {}'.format(len(final2)))

    rectify_dtype(final2, verbose = False)
#    home = os.path.expanduser("~")
#    test_filename = os.path.join(home, filename + ".h5")
#    if os.path.exists(test_filename):
#        import warnings
#        import datetime
#        time_stamp = datetime.datetime.now().strftime('%Y_%m_%d_%H_%M')
#        renamed_file = os.path.join(DATA_SOURCES_DIR, filename + "_" + time_stamp + ".h5")
#        warnings.warn("A file with the same name already exists \n Renaming current output and saving to " + renamed_file)
#        test_filename = renamed_file
    data_frame = final2

    if year == 2006:  # Hack crade pur régler un problème rémanent
        data_frame = data_frame[data_frame.idfam != 602177906].copy()

    for id_variable in ['idfam', 'idfoy', 'idmen', 'noi', 'quifam', 'quifoy', 'quimen']:
        data_frame[id_variable] = data_frame[id_variable].astype('int')

    check = False
    if check:
        check_structure(data_frame)

    gc.collect()
    for entity_id in ['idmen', 'idfoy', 'idfam']:
        log.info('Reformat ids: {}'.format(entity_id))
        data_frame = id_formatter(data_frame, entity_id)

    log.info('Dealing with loyer')
    if 'loyer' in data_frame.columns:
        assert 'loyer' in data_frame.columns
        data_frame.loyer = data_frame.loyer * 12.0
    log.info('Set variables to their default values')
    set_variables_default_value(data_frame, year)

    temporary_store['input_{}'.format(year)] = data_frame
    return data_frame


if __name__ == '__main__':
    import sys
    logging.basicConfig(level = logging.INFO, stream = sys.stdout)
    year = 2009
    final(year = year)

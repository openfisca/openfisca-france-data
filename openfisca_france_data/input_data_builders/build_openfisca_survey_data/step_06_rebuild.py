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


import gc
import logging

from pandas import Series, concat, DataFrame
import numpy as np
from numpy import where

from openfisca_france_data.temporary import temporary_store_decorator
from openfisca_france_data import default_config_files_directory as config_files_directory
from openfisca_france_data.input_data_builders.build_openfisca_survey_data.base import year_specific_by_generic_data_frame_name

from openfisca_france_data.input_data_builders.build_openfisca_survey_data.utils import print_id, control
from openfisca_survey_manager.survey_collections import SurveyCollection


log = logging.getLogger(__name__)


@temporary_store_decorator(config_files_directory = config_files_directory, file_name = 'erfs')
def create_totals(temporary_store = None, year = None):
    assert temporary_store is not None
    assert year is not None
    year_specific_by_generic = year_specific_by_generic_data_frame_name(year)

    # On part de la table individu de l'ERFS
    # on renomme les variables
    log.info(u"Creating Totals")
    log.info(u"Etape 1 : Chargement des données")

    erfs_survey_collection = SurveyCollection.load(collection = 'erfs', config_files_directory = config_files_directory)
    data = erfs_survey_collection.get_survey('erfs_{}'.format(year))

    indivim = temporary_store['indivim_{}'.format(year)]

    assert not indivim.duplicated(['noindiv']).any(), "Présence de doublons"

    # Deals individuals with imputed income : some individuals are in 'erf individu table' but
    # not in the 'foyer' table. We need to create a foyer for them.

    selection = Series()
    for var in ["zsali", "zchoi", "zrsti", "zalri", "zrtoi", "zragi", "zrici", "zrnci"]:
        varo = var[:-1] + "o"
        test = indivim[var] != indivim[varo]
        if len(selection) == 0:
            selection = test
        else:
            selection = (test) | (selection)

    indivi_i = indivim[selection].copy()
    indivi_i.rename(
        columns = {
            "ident": "idmen",
            "persfip": "quifoy",
            "zsali": "sali2",  # Inclu les salaires non imposables des agents d'assurance
            "zchoi": "choi2",
            "zrsti": "rsti2",
            "zalri": "alr2"
            },
        inplace = True,
        )

    indivi_i.quifoy = where(indivi_i.quifoy.isnull(), "vous", indivi_i.quifoy)
    indivi_i.quelfic = "FIP_IMP"

    # We merge them with the other individuals
    indivim.rename(
        columns = dict(
            ident = "idmen",
            persfip = "quifoy",
            zsali = "sali2",  # Inclu les salaires non imposables des agents d'assurance
            zchoi = "choi2",
            zrsti = "rsti2",
            zalri = "alr2",
            ),
        inplace = True,
        )

    if not (set(list(indivim.noindiv)) > set(list(indivi_i.noindiv))):
        raise Exception("Individual ")
    indivim.set_index("noindiv", inplace = True)
    indivi_i.set_index("noindiv", inplace = True)
    indivi = indivim
    del indivim
    indivi.update(indivi_i)

    indivi.reset_index(inplace = True)

    log.info("Etape 2 : isolation des FIP")
    fip_imp = indivi.quelfic == "FIP_IMP"
    indivi["idfoy"] = (
        indivi.idmen.astype("int64") * 100 +
        (indivi.declar1.str[0:2]).convert_objects(convert_numeric=True)
        )

    indivi.loc[fip_imp, "idfoy"] = np.nan
    # Certains FIP (ou du moins avec revenus imputés) ont un numéro de déclaration d'impôt ( pourquoi ?)
    fip_has_declar = (fip_imp) & (indivi.declar1.notnull())

    indivi["idfoy"] = where(
        fip_has_declar,
        indivi.idmen * 100 + indivi.declar1.str[0:2].convert_objects(convert_numeric = True),
        indivi.idfoy)
    del fip_has_declar

    fip_no_declar = (fip_imp) & (indivi.declar1.isnull())
    del fip_imp
    indivi["idfoy"] = where(fip_no_declar, indivi["idmen"] * 100 + 50, indivi["idfoy"])

    indivi_fnd = indivi[["idfoy", "noindiv"]][fip_no_declar].copy()

    while any(indivi_fnd.duplicated(subset = ["idfoy"])):
        indivi_fnd["idfoy"] = where(
            indivi_fnd.duplicated(subset = ["idfoy"]),
            indivi_fnd["idfoy"] + 1,
            indivi_fnd["idfoy"]
            )

    # assert indivi_fnd["idfoy"].duplicated().value_counts()[False] == len(indivi_fnd["idfoy"].values), "Duplicates remaining"
    assert len(indivi[indivi.duplicated(['noindiv'])]) == 0, "Doublons"

    indivi.idfoy[fip_no_declar] = indivi_fnd.idfoy.copy()
    del indivi_fnd, fip_no_declar

    log.info(u"Etape 3 : Récupération des EE_NRT")

    nrt = indivi.quelfic == "EE_NRT"
    indivi.idfoy = where(nrt, indivi.idmen * 100 + indivi.noi, indivi.idfoy)
    indivi.quifoy[nrt] = "vous"
    del nrt

    pref_or_cref = indivi.lpr.isin([1, 2])
    adults = (indivi.quelfic.isin(["EE", "EE_CAF"])) & (pref_or_cref)
    indivi.idfoy = where(adults, indivi.idmen * 100 + indivi.noi, indivi.idfoy)
    indivi.loc[adults, "quifoy"] = "vous"
    del adults
    # TODO: hack to avoid assert error
    log.info("{}".format(indivi.loc[indivi['lpr'].isin([1, 2]), "idfoy"].notnull().value_counts()))
    assert indivi.idfoy[indivi.lpr.dropna().isin([1, 2])].all()

    log.info(u"Etape 4 : Rattachement des enfants aux déclarations")

    assert not(indivi.noindiv.duplicated().any()), "Some noindiv appear twice"
    lpr3_or_lpr4 = indivi['lpr'].isin([3, 4])
    enf_ee = (lpr3_or_lpr4) & (indivi.quelfic.isin(["EE", "EE_CAF"]))
    assert indivi.noindiv[enf_ee].notnull().all(), " Some noindiv are not set, which will ruin next stage"
    assert not(indivi.noindiv[enf_ee].duplicated().any()), "Some noindiv appear twice"

    pere = DataFrame({
        "noindiv_enf": indivi.noindiv.loc[enf_ee],
        "noindiv": 100 * indivi.idmen.loc[enf_ee] + indivi.noiper.loc[enf_ee]
        })
    mere = DataFrame({
        "noindiv_enf": indivi.noindiv.loc[enf_ee],
        "noindiv": 100 * indivi.idmen.loc[enf_ee] + indivi.noimer.loc[enf_ee]
        })

    foyer = data.get_values(variables = ["noindiv", "zimpof"], table = year_specific_by_generic["foyer"])
    pere = pere.merge(foyer, how = "inner", on = "noindiv")
    mere = mere.merge(foyer, how = "inner", on = "noindiv")
    df = pere.merge(mere, how = "outer", on = "noindiv_enf", suffixes=('_p', '_m'))

    log.info(u"    4.1 : gestion des personnes dans 2 foyers")
    for col in ["noindiv_p", "noindiv_m", "noindiv_enf"]:
        df[col] = df[col].fillna(0, inplace = True)  # beacause groupby drop groups with NA in index
    df = df.groupby(by = ["noindiv_p", "noindiv_m", "noindiv_enf"]).sum()
    df.reset_index(inplace = True)

    df["which"] = ""
    df.which = where((df.zimpof_m.notnull()) & (df.zimpof_p.isnull()), "mere", "")
    df.which = where((df.zimpof_p.notnull()) & (df.zimpof_m.isnull()), "pere", "")
    both = (df.zimpof_p.notnull()) & (df.zimpof_m.notnull())
    df.which = where(both & (df.zimpof_p > df.zimpof_m), "pere", "mere")
    df.which = where(both & (df.zimpof_m >= df.zimpof_p), "mere", "pere")

    assert df.which.notnull().all(), "Some enf_ee individuals are not matched with any pere or mere"
    del lpr3_or_lpr4, pere, mere

    df.rename(columns = {"noindiv_enf": "noindiv"}, inplace = True)
    df['idfoy'] = where(df.which == "pere", df.noindiv_p, df.noindiv_m)
    df['idfoy'] = where(df.which == "mere", df.noindiv_m, df.noindiv_p)

    assert df["idfoy"].notnull().all()

    dropped = [col for col in df.columns if col not in ["idfoy", "noindiv"]]
    df.drop(dropped, axis = 1, inplace = True)

    assert not(df.duplicated().any())

    df.set_index("noindiv", inplace = True, verify_integrity = True)
    indivi.set_index("noindiv", inplace = True, verify_integrity = True)

    ind_notnull = indivi["idfoy"].notnull().sum()
    ind_isnull = indivi["idfoy"].isnull().sum()
    indivi = indivi.combine_first(df)
    assert ind_notnull + ind_isnull == (
        indivi["idfoy"].notnull().sum() +
        indivi["idfoy"].isnull().sum()
        )
    indivi.reset_index(inplace = True)
    assert not(indivi.duplicated().any())

    # MBJ: issue delt with when moving from R code to python
    # TODO il faut rajouterles enfants_fip et créer un ménage pour les majeurs
    # On suit guide méthodo erf 2003 page 135
    # On supprime les conjoints FIP et les FIP de 25 ans et plus;
    # On conserve les enfants FIP de 19 à 24 ans;
    # On supprime les FIP de 18 ans et moins, exceptés les FIP nés en 2002 dans un
    # ménage en 6ème interrogation car ce sont des enfants nés aprés la date d'enquète
    # EEC que l'on ne retrouvera pas dans les EEC suivantes.
    #
    log.info(u"    4.2 : On enlève les individus pour lesquels il manque le déclarant")
    fip = temporary_store['fipDat_{}'.format(year)]
    fip["declar"] = np.nan
    fip["agepf"] = np.nan

    fip.drop(["actrec", "year", "noidec"], axis = 1, inplace = True)
    fip.naia = fip.naia.astype("int32")
    fip.rename(
        columns = dict(
            ident = "idmen",
            persfip = "quifoy",
            zsali = "sali2",  # Inclu les salaires non imposables des agents d'assurance
            zchoi = "choi2",
            zrsti = "rsti2",
            zalri = "alr2"),
        inplace = True)

    is_fip_19_25 = ((year - fip.naia - 1) >= 19) & ((year - fip.naia - 1) < 25)

    # TODO: BUT for the time being we keep them in thier vous menage so the following lines are commented
    # The idmen are of the form 60XXXX we use idmen 61XXXX, 62XXXX for the idmen of the kids over 18 and less than 25
    # fip[is_fip_19_25 ,"idmen"] <- (99-fip[is_fip_19_25,"noi"]+1)*100000 + fip[is_fip_19_25,"idmen"]
    # fip[is_fip_19_25 ,"lpr"]  <- 1
    #
    # indivi <- rbind.fill(indivi,fip[is_fip_19_25,])

    indivi = concat([indivi, fip.loc[is_fip_19_25]])
    del is_fip_19_25
    indivi['age'] = year - indivi.naia - 1
    indivi['age_en_mois'] = 12 * indivi.age + 12 - indivi.naim

    indivi["quimen"] = 0
    indivi.quimen[indivi.lpr == 1] = 0
    indivi.quimen[indivi.lpr == 2] = 1
    indivi.quimen[indivi.lpr == 3] = 2
    indivi.quimen[indivi.lpr == 4] = 3
    indivi['not_pr_cpr'] = None  # Create a new row
    indivi.not_pr_cpr[indivi.lpr <= 2] = False
    indivi.not_pr_cpr[indivi.lpr > 2] = True

    assert indivi.not_pr_cpr.isin([True, False]).all()

    log.info(u"    4.3 : Creating non pr=0 and cpr=1 idmen's")
    indivi.reset_index(inplace = True)

    test1 = indivi[['quimen', 'idmen']][indivi.not_pr_cpr].copy()
    test1['quimen'] = 2

    j = 2
    while any(test1.duplicated(['quimen', 'idmen'])):
        test1.loc[test1.duplicated(['quimen', 'idmen']), 'quimen'] = j + 1
        j += 1
    print_id(indivi)
    indivi.update(test1)

    print_id(indivi)

    # indivi.set_index(['quimen']) #TODO: check relevance
    # TODO problème avec certains idfoy qui n'ont pas de vous
    log.info(u"Etape 5 : Gestion des idfoy qui n'ont pas de vous")
    all_ind = indivi.drop_duplicates('idfoy')
    with_ = indivi.loc[indivi.quifoy == 'vous', 'idfoy']
    without = all_ind[~(all_ind.idfoy.isin(with_.values))]

    log.info(u"On cherche si le déclarant donné par la deuxième déclaration est bien un vous")

    # TODO: the following should be delt with at the import of the tables
    indivi.replace(
        to_replace = {
            'declar2': {'NA': np.nan, '': np.nan}
            },
        inplace = True
        )

    has_declar2 = (indivi.idfoy.isin(without.idfoy.values)) & (indivi.declar2.notnull())

    decl2_idfoy = (
        indivi.loc[has_declar2, "idmen"].astype('int') * 100 +
        indivi.loc[has_declar2, "declar2"].str[0:2].astype('int')        )
    indivi.loc[has_declar2, 'idfoy'] = where(decl2_idfoy.isin(with_.values), decl2_idfoy, None)
    del all_ind, with_, without, has_declar2

    log.info(u"    5.1 : Elimination idfoy restant")
    idfoyList = indivi.loc[indivi.quifoy == "vous", 'idfoy'].drop_duplicates()
    indivi = indivi[indivi.idfoy.isin(idfoyList.values)]
    del idfoyList
    print_id(indivi)

    # Sélectionne les variables à garder pour les steps suivants
    myvars = [
        "actrec",
        "age",
        "age_en_mois",
        "chpub",
        "encadr",
        "idfoy",
        "idmen",
        "nbsala",
        "noi",
        "noindiv",
        "prosa",
        "quelfic",
        "quifoy",
        "quimen",
        "statut",
        "titc",
        "txtppb",
        "wprm",
        "rc1rev",
        "maahe",
        ]

    assert len(set(myvars).difference(set(indivi.columns))) == 0, \
        "Manquent les colonnes suivantes : {}".format(set(myvars).difference(set(indivi.columns)))

    indivi = indivi[myvars].copy()
    # TODO les actrec des fip ne sont pas codées (on le fera à la fin quand on aura rassemblé
    # les infos provenant des déclarations)
    log.info(u"Etape 6 : Création des variables descriptives")
    log.info(u"    6.1 : variable activité")
    indivi['activite'] = None
    indivi['activite'][indivi.actrec <= 3] = 0
    indivi['activite'][indivi.actrec == 4] = 1
    indivi['activite'][indivi.actrec == 5] = 2
    indivi['activite'][indivi.actrec == 7] = 3
    indivi['activite'][indivi.actrec == 8] = 4
    indivi['activite'][indivi.age <= 13] = 2  # ce sont en fait les actrec=9
    log.info("{}".format(indivi['activite'].value_counts(dropna = False)))
    # TODO: MBJ problem avec les actrec
    # TODO: FIX AND REMOVE
    indivi.activite[indivi.actrec.isnull()] = 5
    indivi.titc[indivi.titc.isnull()] = 0
    assert indivi.titc.notnull().all(), u"Problème avec les titc" # On a 420 NaN pour les varaibels statut, titc etc

    log.info(u"    6.2 : variable statut")
    indivi.statut[indivi.statut.isnull()] = 0
    indivi.statut = indivi.statut.astype('int')
    indivi.statut[indivi.statut == 11] = 1
    indivi.statut[indivi.statut == 12] = 2
    indivi.statut[indivi.statut == 13] = 3
    indivi.statut[indivi.statut == 21] = 4
    indivi.statut[indivi.statut == 22] = 5
    indivi.statut[indivi.statut == 33] = 6
    indivi.statut[indivi.statut == 34] = 7
    indivi.statut[indivi.statut == 35] = 8
    indivi.statut[indivi.statut == 43] = 9
    indivi.statut[indivi.statut == 44] = 10
    indivi.statut[indivi.statut == 45] = 11
    assert indivi.statut.isin(range(12)).all(), u"statut value over range"


    log.info(u"    6.3 : variable txtppb")
    indivi.txtppb.fillna(0, inplace = True)
    assert indivi.txtppb.notnull().all()

    indivi.nbsala.fillna(0, inplace = True)
    indivi['nbsala'] = indivi.nbsala.astype('int')
    indivi.nbsala[indivi.nbsala == 99] = 10
    assert indivi.nbsala.isin(range(11)).all()

    log.info(u"    6.4 : variable chpub et CSP")
    indivi.chpub.fillna(0, inplace = True)
    indivi.chpub = indivi.chpub.astype('int')
    indivi.chpub[indivi.chpub.isnull()] = 0
    assert indivi.chpub.isin(range(11)).all()

    indivi['cadre'] = 0
    indivi.prosa.fillna(0, inplace = True)
    assert indivi['prosa'].notnull().all()
    log.info("{}".format(indivi['encadr'].value_counts(dropna = False)))

    # encadr : 1=oui, 2=non
    indivi.encadr.fillna(2, inplace = True)
    indivi.encadr[indivi.encadr == 0] = 2

    assert indivi.encadr.notnull().all()
    assert indivi.encadr.isin([1, 2]).all()

    indivi['cadre'][indivi.prosa.isin([7, 8])] = 1
    indivi['cadre'][(indivi.prosa == 9) & (indivi.encadr == 1)] = 1

    assert indivi['cadre'].isin(range(2)).all()

    log.info(
        u"Etape 7: on vérifie qu'il ne manque pas d'info sur les liens avec la personne de référence")
    log.info(
        u"nb de doublons idfam/quifam {}".format(len(indivi[indivi.duplicated(subset = ['idfoy', 'quifoy'])])))

    log.info(u"On crée les n° de personnes à charge")
    assert indivi['idfoy'].notnull().all()
    print_id(indivi)
    indivi['quifoy2'] = 2
    indivi.quifoy2[indivi.quifoy == 'vous'] = 0
    indivi.quifoy2[indivi.quifoy == 'conj'] = 1
    indivi.quifoy2[indivi.quifoy == 'pac'] = 2

    del indivi['quifoy']
    indivi['quifoy'] = indivi.quifoy2
    del indivi['quifoy2']

    print_id(indivi)
    test2 = indivi[['quifoy', 'idfoy', 'noindiv']][indivi['quifoy'] == 2].copy()
    print_id(test2)

    j = 2
    while test2.duplicated(['quifoy', 'idfoy']).any():
        test2.loc[test2.duplicated(['quifoy', 'idfoy']), 'quifoy'] = j
        j += 1

    print_id(test2)
    indivi = indivi.merge(test2, on = ['noindiv', 'idfoy'], how = "left")
    indivi['quifoy'] = indivi['quifoy_x']
    indivi['quifoy'] = where(indivi['quifoy_x'] == 2, indivi['quifoy_y'], indivi['quifoy_x'])
    del indivi['quifoy_x'], indivi['quifoy_y']
    print_id(indivi)

    del test2, fip
    log.info(
        u"nb de doublons idfam/quifam' {}".format(
            len(indivi[indivi.duplicated(subset = ['idfoy', 'quifoy'])])
            )
        )
    print_id(indivi)

    log.info(u"Etape 8 : création des fichiers totaux")
    famille = temporary_store['famc_{}'.format(year)]

    log.info(u"    8.1 : création de tot2 & tot3")
    tot2 = indivi.merge(famille, on = 'noindiv', how = 'inner')
#     del famille # TODO: MBJ increase in number of menage/foyer when merging with family ...
    del famille

    control(tot2, debug = True, verbose = True)
    assert tot2.quifam.notnull().all()

    temporary_store['tot2_{}'.format(year)] = tot2
    del indivi
    log.info(u"    tot2 saved")

    tot2.merge(foyer, how = 'left')

    tot2 = tot2[tot2.idmen.notnull()].copy()

    print_id(tot2)
    tot3 = tot2
    # TODO: check where they come from
    tot3 = tot3.drop_duplicates(subset = 'noindiv')
    log.info("{}".format(len(tot3)))

    # Block to remove any unwanted duplicated pair
    control(tot3, debug = True, verbose = True)
    tot3 = tot3.drop_duplicates(subset = ['idfoy', 'quifoy'])
    tot3 = tot3.drop_duplicates(subset = ['idfam', 'quifam'])
    tot3 = tot3.drop_duplicates(subset = ['idmen', 'quimen'])
    tot3 = tot3.drop_duplicates(subset = ['noindiv'])
    control(tot3)

    log.info(u"    8.2 : On ajoute les variables individualisables")

    allvars = temporary_store['ind_vars_to_remove_{}'.format(year)]
    vars2 = set(tot3.columns).difference(set(allvars))
    tot3 = tot3[list(vars2)]
    log.info("{}".format(len(tot3)))

    assert not(tot3.duplicated(subset = ['noindiv']).any()), "doublon dans tot3['noindiv']"
    lg_dup = len(tot3[tot3.duplicated(['idfoy', 'quifoy'])])
    assert lg_dup == 0, "{} pairs of idfoy/quifoy in tot3 are duplicated".format(lg_dup)

    temporary_store['tot3_{}'.format(year)] = tot3
    control(tot3)

    del tot2, allvars, tot3, vars2
    log.info(u"tot3 sauvegardé")
    gc.collect()


@temporary_store_decorator(config_files_directory = config_files_directory, file_name = 'erfs')
def create_final(temporary_store = None, year = None):

    assert temporary_store is not None
    assert year is not None

    log.info(u"création de final")
    foy_ind = temporary_store['foy_ind_{}'.format(year)]
    tot3 = temporary_store['tot3_{}'.format(year)]

    foy_ind.set_index(['idfoy', 'quifoy'], inplace = True)
    tot3.set_index(['idfoy', 'quifoy'], inplace = True)
    final = concat([tot3, foy_ind], join_axes=[tot3.index], axis=1)
    final.reset_index(inplace = True)
    foy_ind.reset_index(inplace = True)
    tot3.reset_index(inplace = True)

    # tot3 = tot3.drop_duplicates(subset=['idfam', 'quifam'])
    final = final[final.idmen.notnull()]

    control(final, verbose=True)
    del tot3, foy_ind
    gc.collect()

    # final <- merge(final, sif, by = c('noindiv'), all.x = TRUE)
    log.info("    loading fip")
    sif = temporary_store['sif_{}'.format(year)]

    log.info("{}".format(sif.columns))
    log.info("    update final using fip")
    final = final.merge(sif, on=["noindiv"], how="left")
    # TODO: IL FAUT UNE METHODE POUR GERER LES DOUBLES DECLARATIONS

    control(final, debug=True)

    final['caseP'] = final.caseP.fillna(False)
    final['caseF'] = final.caseF.fillna(False)
    print_id(final)

    temporary_store['final_{}'.format(year)] = final
    log.info(u"final sauvegardé")
    del sif, final

if __name__ == '__main__':
    year = 2009
    create_totals(year = year)
    create_final(year = year)
    log.info(u"étape 06 remise en forme des données terminée")

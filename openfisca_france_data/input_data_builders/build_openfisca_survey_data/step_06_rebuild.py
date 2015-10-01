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
from openfisca_france_data.input_data_builders.build_openfisca_survey_data.base import (
    year_specific_by_generic_data_frame_name
    )
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
    for var_i in ["zsali", "zchoi", "zrsti", "zalri", "zrtoi", "zragi", "zrici", "zrnci"]:
        var_o = var_i[:-1] + "o"
        test = indivim[var_i] != indivim[var_o]
        if selection.empty:
            selection = test
        else:
            selection = test | selection

    indivi_i = indivim[selection].copy()
    indivi_i.rename(
        columns = {
            "ident": "idmen",
            "persfip": "quifoy",
            "zsali": "sali",  # Inclu les salaires non imposables des agents d'assurance
            "zchoi": "choi",
            "zrsti": "rsti",
            "zalri": "alr"
            },
        inplace = True,
        )
    assert indivi_i.quifoy.notnull().all()
    indivi_i.loc[indivi_i.quifoy == "", "quifoy"] = "vous"
    indivi_i.quelfic = "FIP_IMP"

   # We merge them with the other individuals
    indivim.rename(
        columns = dict(
            ident = "idmen",
            persfip = "quifoy",
            zsali = "sali",  # Inclu les salaires non imposables des agents d'assurance
            zchoi = "choi",
            zrsti = "rsti",
            zalri = "alr",
            ),
        inplace = True,
        )

    if not (set(list(indivim.noindiv)) > set(list(indivi_i.noindiv))):
        raise Exception("Individual ")
    indivim.set_index("noindiv", inplace = True, verify_integrity = True)
    indivi_i.set_index("noindiv", inplace = True, verify_integrity = True)
    indivi = indivim
    del indivim
    indivi.update(indivi_i)
    indivi.reset_index(inplace = True)
    assert not(indivi.noindiv.duplicated().any()), "Doublons"

    log.info("Etape 2 : isolation des FIP")
    fip_imp = indivi.quelfic == "FIP_IMP"
    indivi["idfoy"] = (
        indivi.idmen.astype("int64") * 100 +
        (indivi.declar1.str[0:2]).convert_objects(convert_numeric=True)
        )

    # indivi.loc[fip_imp, "idfoy"] = np.nan
    # Certains FIP (ou du moins avec revenus imputés) ont un numéro de déclaration d'impôt ( pourquoi ?)
    assert indivi_i.declar1.notnull().all()
    assert (indivi_i.declar1 == "").sum() > 0
    fip_has_declar = (fip_imp) & (indivi.declar1 != "")

    indivi.loc[fip_has_declar, "idfoy"] = (
        indivi.idmen * 100 + indivi.declar1.str[0:2].convert_objects(convert_numeric = True))
    del fip_has_declar

    fip_no_declar = (fip_imp) & (indivi.declar1 == "")
    del fip_imp
    indivi.loc[fip_no_declar, "idfoy"] = indivi["idmen"] * 100 + 50

    indivi_fnd = indivi.loc[fip_no_declar, ["idfoy", "noindiv"]].copy()

    while any(indivi_fnd.duplicated(subset = ["idfoy"])):
        indivi_fnd["idfoy"] = where(
            indivi_fnd.duplicated(subset = ["idfoy"]),
            indivi_fnd["idfoy"] + 1,
            indivi_fnd["idfoy"]
            )

    # assert indivi_fnd["idfoy"].duplicated().value_counts()[False] == len(indivi_fnd["idfoy"].values), \
    #    "Duplicates remaining"
    assert not(indivi.noindiv.duplicated().any()), "Doublons"

    indivi.idfoy.loc[fip_no_declar] = indivi_fnd.idfoy.copy()
    del indivi_fnd, fip_no_declar

    log.info(u"Etape 3 : Récupération des EE_NRT")
    nrt = indivi.quelfic == "EE_NRT"
    indivi.loc[nrt, 'idfoy'] = indivi.idmen * 100 + indivi.noi
    indivi.loc[nrt, 'quifoy'] = "vous"
    del nrt

    pref_or_cref = indivi.lpr.isin([1, 2])
    adults = (indivi.quelfic.isin(["EE", "EE_CAF"])) & (pref_or_cref)
    indivi.loc[adults, "idfoy"] = indivi.idmen * 100 + indivi.noi
    indivi.loc[adults, "quifoy"] = "vous"
    del adults
    assert indivi.idfoy[indivi.lpr.dropna().isin([1, 2])].all()

    log.info(u"Etape 4 : Rattachement des enfants aux déclarations")
    assert not(indivi.noindiv.duplicated().any()), "Some noindiv appear twice"
    lpr3_or_lpr4 = indivi['lpr'].isin([3, 4])
    enf_ee = (lpr3_or_lpr4) & (indivi.quelfic.isin(["EE", "EE_CAF"]))
    assert indivi.noindiv[enf_ee].notnull().all(), " Some noindiv are not set, which will ruin next stage"
    assert not(indivi.noindiv[enf_ee].duplicated().any()), "Some noindiv appear twice"

    enf_ee_avec_pere = (enf_ee & indivi.noiper != 0).copy()
    enf_ee_avec_mere = (enf_ee & indivi.noimer != 0).copy()

    pere = DataFrame({
        "noindiv_enf": indivi.noindiv.loc[enf_ee_avec_pere].copy(),
        "noindiv": 100 * indivi.idmen.loc[enf_ee_avec_pere] + indivi.noiper.loc[enf_ee_avec_pere]
        })
    mere = DataFrame({
        "noindiv_enf": indivi.noindiv.loc[enf_ee_avec_mere].copy(),
        "noindiv": 100 * indivi.idmen.loc[enf_ee_avec_mere] + indivi.noimer.loc[enf_ee_avec_mere]
        })

    foyer = data.get_values(variables = ["noindiv", "zimpof"], table = year_specific_by_generic["foyer"])
    pere_with_declar = pere.merge(foyer, how = "inner", on = "noindiv")
    mere_with_declar = mere.merge(foyer, how = "inner", on = "noindiv")
    df = pere_with_declar.merge(mere_with_declar, how = "outer", on = "noindiv_enf", suffixes=('_p', '_m'))
    # df has now columns noindiv_enf noindiv_p noindiv_m zimpof_p zimpof_m with nan when those values do not exist
    del lpr3_or_lpr4, pere, mere

    log.info(u"    4.1 : gestion des personnes dans 2 foyers")
    for col in ["noindiv_p", "noindiv_m", "noindiv_enf"]:
        df[col].fillna(0, inplace = True)  # beacause groupby drop groups with NA in index
    df = df.groupby(by = ["noindiv_p", "noindiv_m", "noindiv_enf"]).sum()
    df.reset_index(inplace = True)

    df["which"] = ""
    df.loc[df.zimpof_m.notnull() & df.zimpof_p.isnull(), 'which'] = "mere"
    df.loc[df.zimpof_m.isnull() & df.zimpof_p.notnull(), 'which'] = "pere"
    both = (df.zimpof_p.notnull()) & (df.zimpof_m.notnull())
    df.loc[both & (df.zimpof_p > df.zimpof_m), 'which'] = "pere"
    df.loc[both & (df.zimpof_m >= df.zimpof_p),'which'] = "mere"

    assert (df.which != "").all(), "Some enf_ee individuals are not matched with any pere or mere"

    df.rename(columns = {"noindiv_enf": "noindiv"}, inplace = True)
    df['idfoy'] = 0
    assert df.noindiv_p.notnull().all(), "If absent noindiv_p should be 0"
    assert df.noindiv_m.notnull().all(), "If absent noindiv_m should be 0"
    df.idfoy = (df.which == "pere") * df.noindiv_p
    df.idfoy = (df.which == "mere") * df.noindiv_m

    df['idfoy'] = where(df.which == "mere", df.noindiv_m, df.noindiv_p)
    assert df["idfoy"].notnull().all()
    dropped = [col for col in df.columns if col not in ["idfoy", "noindiv"]]
    df.drop(dropped, axis = 1, inplace = True)

    assert not(df.duplicated().any())

    df.set_index("noindiv", inplace = True, verify_integrity = True)
    indivi.set_index("noindiv", inplace = True, verify_integrity = True)
    indivi.update(df)
    indivi.reset_index(inplace = True)
    assert not(indivi.noindiv.duplicated().any())

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
            zsali = "sali",  # Inclu les salaires non imposables des agents d'assurance
            zchoi = "choi",
            zrsti = "rsti",
            zalri = "alr"),
        inplace = True)

    is_fip_19_25 = ((year - fip.naia - 1) >= 19) & ((year - fip.naia - 1) < 25)

    # TODO: BUT for the time being we keep them in thier vous menage so the following lines are commented
    # The idmen are of the form 60XXXX we use idmen 61XXXX, 62XXXX for the idmen of the kids over 18 and less than 25

    indivi = concat([indivi, fip.loc[is_fip_19_25].copy()])
    assert not(indivi.noindiv.duplicated().any())

    del is_fip_19_25
    indivi['age'] = year - indivi.naia - 1
    indivi['age_en_mois'] = 12 * indivi.age + 12 - indivi.naim

    indivi["quimen"] = 0
    indivi.loc[indivi.lpr == 1, 'quimen'] = 0
    indivi.loc[indivi.lpr == 2, 'quimen'] = 1
    indivi.loc[indivi.lpr == 3, 'quimen'] = 2
    indivi.loc[indivi.lpr == 4, 'quimen'] = 3
    indivi['not_pr_cpr'] = None  # Create a new row
    indivi.loc[indivi.lpr <= 2, 'not_pr_cpr'] = False
    indivi.loc[indivi.lpr > 2, 'not_pr_cpr'] = True

    assert indivi.not_pr_cpr.isin([True, False]).all()

    log.info(u"    4.3 : Creating non pr=0 and cpr=1 idmen's")

    indivi.set_index('noindiv', inplace = True, verify_integrity = True)
    test1 = indivi.loc[indivi.not_pr_cpr, ['quimen', 'idmen']].copy()
    test1['quimen'] = 2

    j = 2
    while any(test1.duplicated(['quimen', 'idmen'])):
        test1.loc[test1.duplicated(['quimen', 'idmen']), 'quimen'] = j + 1
        j += 1
    print_id(indivi)
    indivi.update(test1)
    indivi.reset_index(inplace = True)
    print_id(indivi)

    # TODO problème avec certains idfoy qui n'ont pas de vous
    log.info(u"Etape 5 : Gestion des idfoy qui n'ont pas de vous")
    with_ = indivi.loc[indivi.quifoy == 'vous', 'idfoy'].copy().drop_duplicates()
    without = indivi.loc[~(indivi.idfoy.isin(with_.values)), ['noindiv', 'idfoy']].copy()
    log.info(u"{} foyers n'ont pas de vous".format(len(without)))
    log.info(u"On cherche si le déclarant donné par la deuxième déclaration est bien un vous")

    # TODO: the following should be delt with at the import of the tables
    indivi.replace(
        to_replace = {
            'declar2': {'NA': np.nan, '': np.nan}
            },
        inplace = True
        )

    indivi_without_declarant_has_declar2 = (indivi.idfoy.isin(without.idfoy.values)) & (indivi.declar2.notnull())
    decl2_idfoy = (
        indivi.loc[indivi_without_declarant_has_declar2, "idmen"].astype('int') * 100 +
        indivi.loc[indivi_without_declarant_has_declar2, "declar2"].str[0:2].astype('int')
        )
    indivi.loc[indivi_without_declarant_has_declar2, 'idfoy'] = where(decl2_idfoy.isin(with_.values), decl2_idfoy, None)

    del with_, without, indivi_without_declarant_has_declar2

    log.info(u"    5.1 : Elimination idfoy restant")
    # Voiture balai
    # On a plein d'idfoy vides, on fait 1 ménage = 1 foyer fiscal
    idfoyList = indivi.loc[indivi.quifoy == "vous", 'idfoy'].unique()
    indivi_without_idfoy = ~indivi.idfoy.isin(idfoyList)

    indivi.loc[indivi_without_idfoy, 'idfoy'] = indivi.loc[indivi_without_idfoy, "idmen"].astype('int') * 100 + 51
    indivi.loc[indivi_without_idfoy, 'quifoy'] = "pac"
    indivi.loc[indivi_without_idfoy & (indivi.quimen == 0), 'quifoy'] = "vous"
    indivi.loc[indivi_without_idfoy & (indivi.quimen == 1), 'quifoy'] = "conj"

    del idfoyList
    print_id(indivi)

    # Sélectionne les variables à garder pour les steps suivants
    variables = [
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
        "sali",
        "rsti",
        "choi",
        "alr",
        "wprm",
        ]

    assert set(variables).issubset(set(indivi.columns)), \
        "Manquent les colonnes suivantes : {}".format(set(variables).difference(set(indivi.columns)))

    dropped_columns = [variable for variable in indivi.columns if variable not in variables]
    indivi.drop(dropped_columns, axis = 1, inplace = True)

    #  see http://stackoverflow.com/questions/11285613/selecting-columns
    indivi.reset_index(inplace = True)
    gc.collect()

    # TODO les actrec des fip ne sont pas codées (on le fera à la fin quand on aura rassemblé
    # les infos provenant des déclarations)
    log.info(u"Etape 6 : Création des variables descriptives")
    log.info(u"    6.1 : Variable activité")
    log.info(u"Variables présentes; \n {}".format(indivi.columns))

    indivi['activite'] = np.nan
    indivi.loc[indivi.actrec <= 3, 'activite'] = 0
    indivi.loc[indivi.actrec == 4, 'activite'] = 1
    indivi.loc[indivi.actrec == 5, 'activite'] = 2
    indivi.loc[indivi.actrec == 7, 'activite'] = 3
    indivi.loc[indivi.actrec == 8, 'activite'] = 4
    indivi.loc[indivi.age <= 13, 'activite'] = 2  # ce sont en fait les actrec=9
    log.info("Valeurs prises par la variable activité \n {}".format(indivi['activite'].value_counts(dropna = False)))
    # TODO: MBJ problem avec les actrec
    # TODO: FIX AND REMOVE
    indivi.loc[indivi.actrec.isnull(), 'activite'] = 5
    indivi.loc[indivi.titc.isnull(), 'titc'] = 0
    assert indivi.titc.notnull().all(), \
        u"Problème avec les titc"  # On a 420 NaN pour les varaibels statut, titc etc

    log.info(u"    6.2 : Variable statut")
    indivi.loc[indivi.statut.isnull(), 'statut'] = 0
    indivi.statut = indivi.statut.astype('int')
    indivi.loc[indivi.statut == 11, 'statut'] = 1
    indivi.loc[indivi.statut == 12, 'statut'] = 2
    indivi.loc[indivi.statut == 13, 'statut'] = 3
    indivi.loc[indivi.statut == 21, 'statut'] = 4
    indivi.loc[indivi.statut == 22, 'statut'] = 5
    indivi.loc[indivi.statut == 33, 'statut'] = 6
    indivi.loc[indivi.statut == 34, 'statut'] = 7
    indivi.loc[indivi.statut == 35, 'statut'] = 8
    indivi.loc[indivi.statut == 43, 'statut'] = 9
    indivi.loc[indivi.statut == 44, 'statut'] = 10
    indivi.loc[indivi.statut == 45, 'statut'] = 11
    assert indivi.statut.isin(range(12)).all(), u"statut value over range"
    log.info("Valeurs prises par la variable statut \n {}".format(
        indivi['statut'].value_counts(dropna = False)))

    log.info(u"    6.3 : variable txtppb")
    indivi.loc[indivi.txtppb.isnull(), 'txtppb'] = 0
    assert indivi.txtppb.notnull().all()
    indivi.loc[indivi.nbsala.isnull(), 'nbsala'] = 0
    indivi.nbsala = indivi.nbsala.astype('int')
    indivi.loc[indivi.nbsala == 99, 'nbsala'] = 10
    assert indivi.nbsala.isin(range(11)).all()
    log.info("Valeurs prises par la variable txtppb \n {}".format(
        indivi['txtppb'].value_counts(dropna = False)))

    log.info(u"    6.4 : variable chpub et CSP")
    indivi.loc[indivi.chpub.isnull(), 'chpub'] = 0
    indivi.chpub = indivi.chpub.astype('int')
    assert indivi.chpub.isin(range(11)).all()

    indivi['cadre'] = 0
    indivi.loc[indivi.prosa.isnull(), 'prosa'] = 0
    assert indivi.prosa.notnull().all()
    log.info("Valeurs prises par la variable encadr \n {}".format(indivi['encadr'].value_counts(dropna = False)))

    # encadr : 1=oui, 2=non
    indivi.loc[indivi.encadr.isnull(), 'encadr'] = 2
    indivi.loc[indivi.encadr == 0, 'encadr'] = 2
    assert indivi.encadr.notnull().all()
    assert indivi.encadr.isin([1, 2]).all()

    indivi.loc[indivi.prosa.isin([7, 8]), 'cadre'] = 1
    indivi.loc[(indivi.prosa == 9) & (indivi.encadr == 1), 'cadre'] = 1
    assert indivi.cadre.isin(range(2)).all()

    log.info(
        u"Etape 7: on vérifie qu'il ne manque pas d'info sur les liens avec la personne de référence"
        )
    log.info(
        u"nb de doublons idfoy/quifoy {}".format(len(indivi[indivi.duplicated(subset = ['idfoy', 'quifoy'])]))
        )

    log.info(u"On crée les n° de personnes à charge dans le foyer fiscal")
    assert indivi.idfoy.notnull().all()
    print_id(indivi)
    indivi['quifoy_bis'] = 2
    indivi.loc[indivi.quifoy == 'vous', 'quifoy_bis'] = 0
    indivi.loc[indivi.quifoy == 'conj', 'quifoy_bis'] = 1
    indivi.loc[indivi.quifoy == 'pac', 'quifoy_bis'] = 2
    del indivi['quifoy']
    indivi['quifoy'] = indivi.quifoy_bis.copy()
    del indivi['quifoy_bis']

    print_id(indivi)
    pac = indivi.loc[indivi['quifoy'] == 2, ['quifoy', 'idfoy', 'noindiv']].copy()
    print_id(pac)

    j = 2
    while pac.duplicated(['quifoy', 'idfoy']).any():
        pac.loc[pac.duplicated(['quifoy', 'idfoy']), 'quifoy'] = j
        j += 1

    print_id(pac)
    indivi = indivi.merge(pac, on = ['noindiv', 'idfoy'], how = "left")
    indivi['quifoy'] = indivi['quifoy_x']
    indivi['quifoy'] = where(indivi['quifoy_x'] == 2, indivi['quifoy_y'], indivi['quifoy_x'])
    del indivi['quifoy_x'], indivi['quifoy_y']
    print_id(indivi)

    del pac, fip
    assert len(indivi[indivi.duplicated(subset = ['idfoy', 'quifoy'])]) == 0, \
        u"Il y a {} doublons idfoy/quifoy".format(
            len(indivi[indivi.duplicated(subset = ['idfoy', 'quifoy'])])
            )
    print_id(indivi)

    log.info(u"Etape 8 : création des fichiers totaux")
    famille = temporary_store['famc_{}'.format(year)]

    log.info(u"    8.1 : création de tot2 & tot3")
    tot2 = indivi.merge(famille, on = 'noindiv', how = 'inner')
    # TODO: MBJ increase in number of menage/foyer when merging with family ...
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
    log.info("Avant élimination des doublons noindiv: {}".format(len(tot3)))

    tot3 = tot3.drop_duplicates(subset = 'noindiv')
    log.info("Après élimination des doublons noindiv: {}".format(len(tot3)))

    # Block to remove any unwanted duplicated pair

    control(tot3, debug = True, verbose = True)
    tot3 = tot3.drop_duplicates(subset = ['idfoy', 'quifoy'])
    log.info("Après élimination des doublons idfoy, quifoy: {}".format(len(tot3)))
    tot3 = tot3.drop_duplicates(subset = ['idfam', 'quifam'])
    log.info("Après élimination des doublons idfam, 'quifam: {}".format(len(tot3)))
    tot3 = tot3.drop_duplicates(subset = ['idmen', 'quimen'])
    log.info("Après élimination des doublons idmen, quimen: {}".format(len(tot3)))
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

    log.info(u"Stats on tot3")
    print_id(tot3)
    log.info(u"Stats on foy_ind")
    print_id(foy_ind)
    foy_ind.set_index(['idfoy', 'quifoy'], inplace = True, verify_integrity = True)
    tot3.set_index(['idfoy', 'quifoy'], inplace = True, verify_integrity = True)

    # tot3 = concat([tot3, foy_ind], join_axes=[tot3.index], axis=1, verify_integrity = True)

    # TODO improve this
    foy_ind.drop([u'alr', u'rsti', u'sali', u'choi'], axis = 1, inplace = True)
    tot3 = tot3.join(foy_ind)
    tot3.reset_index(inplace = True)
    foy_ind.reset_index(inplace = True)

    # tot3 = tot3.drop_duplicates(subset=['idfam', 'quifam'])
    control(tot3, verbose=True)
    final = tot3.loc[tot3.idmen.notnull(), :].copy()

    control(final, verbose=True)
    del tot3, foy_ind
    gc.collect()

    log.info("    loading fip")
    sif = temporary_store['sif_{}'.format(year)]
    log.info("Columns from sif dataframe: {}".format(sif.columns))
    log.info("    update final using fip")
    final.set_index('noindiv', inplace = True, verify_integrity = True)

    # TODO: IL FAUT UNE METHODE POUR GERER LES DOUBLES DECLARATIONS
    #  On ne garde que les sif.noindiv qui correspondent à des idfoy == "vous"
    #  Et on enlève les duplicates
    idfoys = final.loc[final.quifoy == 0, "idfoy"]
    sif = sif[sif.noindiv.isin(idfoys) & ~(sif.change.isin(['M', 'S', 'Z']))].copy()
    sif.drop_duplicates(subset = ['noindiv'], inplace = True)
    sif.set_index('noindiv', inplace = True, verify_integrity = True)
    final = final.join(sif)
    final.reset_index(inplace = True)

    control(final, debug=True)

    final['caseP'] = final.caseP.fillna(False)
    final['caseF'] = final.caseF.fillna(False)
    print_id(final)

    temporary_store['final_{}'.format(year)] = final
    log.info(u"final sauvegardé")
    del sif, final

if __name__ == '__main__':
    year = 2009
    logging.basicConfig(level = logging.INFO, filename = 'step_06.log', filemode = 'w')
    # create_totals(year = year)
    create_final(year = year)
    log.info(u"étape 06 remise en forme des données terminée")

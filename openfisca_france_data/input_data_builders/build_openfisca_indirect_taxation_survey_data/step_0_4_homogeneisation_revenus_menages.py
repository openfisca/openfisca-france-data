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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import logging
import pandas


from openfisca_survey_manager.survey_collections import SurveyCollection
from openfisca_france_data import default_config_files_directory as config_files_directory
from openfisca_france_data.temporary import TemporaryStore


log = logging.getLogger(__name__)
temporary_store = TemporaryStore.create(file_name = "indirect_taxation_tmp")


def build_homogeneisation_revenus_menages(year = None):
    """Build menage consumption by categorie fiscale dataframe """

    assert year is not None
    # Load data
    bdf_survey_collection = SurveyCollection.load(
        collection = 'budget_des_familles', config_files_directory = config_files_directory)
    survey = bdf_survey_collection.get_survey('budget_des_familles_{}'.format(year))

# **********************************************************************************************************************
# ********************************* HOMOGENEISATION DES DONNEES SUR LES REVENUS DES MENAGES ****************************
# ************************************ CALCUL D'UN PROXI DU REVENU DISPONIBLE DES MENAGES ******************************
# **********************************************************************************************************************
#
# ********************HOMOGENEISATION DES BASES DE RESSOURCES***************************
#    if ${yearrawdata} == 1995 {
# use "$rawdatadir\menrev.dta", clear
# /* La base 95 permet de distinguer taxe d'habitation et impôts fonciers. On calcule leur montant relatif pour l'appliquer à 00 et 05 */
# gen foncier_hab=IMPHAB+IMPFON
# gen part_IMPHAB=IMPHAB/ foncier_hab
# gen part_IMPFON=IMPFON/ foncier_hab
# su part_*
# keep REVTOT IR IRBIS IMPHAB IMPFON REVAID REVSAL REVIND REVSEC REVRET REVIND REVCHO REVFAM REVLOG REVINV REVRMI REVPAT MENA PONDERR
# gen revsoc= REVRET + REVCHO + REVFAM + REVLOG + REVINV + REVRMI
# drop REVCHO REVFAM REVINV REVLOG REVRET REVRMI
# gen revact = REVSAL + REVIND + REVSEC
# rename REVPAT revpat
# gen impot_revenu = IR + IRBIS

    if year == 1995:
        menrev = survey.get_values(
            table = "menrev",
            variables = [
                'revtot', 'ir', 'irbis', 'imphab', 'impfon', 'revaid', 'revsal', 'revind', 'revsec', 'revret',
                'revcho', 'revfam', 'revlog', 'revinv', 'revrmi', 'revpat', 'mena', 'ponderr'
                ],
            )

        menrev['foncier_hab'] = menrev.IMPHAB + menrev.IMPFON
        menrev['part_IMPHAB'] = menrev.IMPHAB / menrev.foncier_hab
        menrev['part_IMPFON'] = menrev.IMPFON / menrev.foncier_hab

        menrev['revsoc'] = (
            menrev.REVRET + menrev.REVCHO + menrev.REVFAM + menrev.REVLOG + menrev.REVINV + menrev.REVRMI
            )
        for variable in ['revcho', 'revfam', 'revinv', 'revlog', 'revret', 'revrmi']:
            del menrev[variable]

        menrev['revact'] = 'revsal' + 'revind' + 'revsec'
        menrev.rename(
            columns = dict(
                REVPAT = "revpat",
                IMPFON = "impfon",
                IMPHAB = "imphab",
                REVAID= "somme_obl_recue",
                ),
            inplace = True
            )
        menrev['impot_revenu'] = 'ir' + 'irbis'


        rev_disp = survey.get_values(
            table = "rev_disp",
            variables = ['revtot', 'revsoc', 'imphab', 'impfon', 'revaid', 'revsal', 'revind', 'revsec', 'revpat', 'mena', 'ponderr'],
            )
# drop IR IRBIS
# rename IMPFON impfon
# rename IMPHAB imphab
# rename REVAID somme_obl_recue
        rev_disp['somme_obl_recue'].replace('.',0)
# replace somme_obl_recue=0 if somme_obl_recue==.
        rev_disp['revtot'] = 'revact' + 'revpat' + 'revsoc' + 'somme_obl_recue'
# gen revtot = revact + revpat + revsoc + somme_obl_recue
# drop REVTOT
        rev_disp = survey.get_values(
            table = "rev_disp",
            variables = ['revtot', 'revsoc', 'imphab', 'impfon', 'revaid', 'revsal', 'revind', 'revsec', 'revpat', 'mena', 'ponderr'],
            )
# sort MENA
# merge MENA using "`ponder'"
        rev_disp = rev_disp.sort(columns = ['mena'], inplace=True)
        rev_disp.set_index('mena', inplace=True)
        rev_disp.merge('ponder', on = "mena")
# tab _merge
# keep if _m == 3
# codebook MENA
# drop _m
# sort MENA
        rev_disp.rename(
            columns = dict(
                PONDERR = "pondmen",
                MENA = "ident_men",
                REVIND = "act_indpt",
                REVSAL = "salaires",
                REVSEC = "autres_rev",
                ),
            inplace = True
            )
# rename PONDERRD pondmen
# erreur dans le code STATA d'origine la variable s'appelle bien PONDERR
# rename MENA ident_men
# rename REVIND act_indpt
# rename REVSAL salaires
# rename REVSEC autres_rev
        rev_disp['somme_libre_recue'] = '.'
        rev_disp['autoverses'] = '.'
        rev_disp['autres_ress'] = '.'
# gen somme_libre_recue=.
# gen autoverses=.
# gen autres_ress=.
# TODO: je ne comprends pas l'intérêt de la création de ces trois variables
#
# /* Le revenu disponible se calcule à partir de revtot à laquelle on retrancher la taxe d'habitation
# et l'impôt sur le revenu, plus éventuellement les CSG et CRDS.
# La variable revtot est la somme des revenus d'activité, sociaux, du patrimoine et d'aide. */
#
# label var ident_men "identifiant du ménage"
# label var somme_obl_recue "Pensions alimentaires, etc."
# label var act_indpt "Revenus d'activité indépendante"
# label var revpat "Revenus du patrimoine"
# label var salaires "Salaires"
# label var autres_rev "Autres revenus"
# label var impfon "Taxe foncière"
# label var imphab "Taxe d'habitation"
# label var pondmen "Pondération"
# label var revsoc "Revenus sociaux"
# label var revact "Revenus d'activité"
# label var impot_revenu "Impot sur le revenu"
# label var revtot "Revenu total"
# label var somme_libre_recue "Aides libres d'autres ménages"
# label var autoverses "Revenus auto-versés"
# label var autres_ress "Autres ressources"
        for var in ['somme_obl_recue', 'act_indpt', 'revpat salaires', 'autres_rev', 'impfon', 'imphab', 'revsoc', 'revact', 'impot_revenu', 'revtot', 'somme_libre_recue', 'autoverses', 'autres_ress'] :
            rev_disp[var] = rev_disp[var] / 6.55957
# * CONVERSION EN EUROS
# foreach var in   somme_obl_recue act_indpt revpat salaires autres_rev impfon imphab revsoc revact impot_revenu revtot somme_libre_recue autoverses autres_ress {
#     replace `var' = `var' / 6.55957
# }
# sort ident_men
# save "$datadir\revenus.dta", replace
#    }
        rev_disp = rev_disp.sort(columns = ['MENA'], inplace=True)

#
#    if ${yearrawdata} == 2000 {
    elif year == 2000:
    # TODO: récupérer plutôt les variables qui viennent de la table dépenses (dans temporary_store)
        consomen = survey.get_values(
            table = "consomen",
#            variables = ['C13141', 'C13111', 'C13121', 'C13131', 'PONDMEN', 'IDENT'],
            )
        rev_disp = consomen.sort(columns = ['ident'])
        del consomen

# tempfile rev_disp2
# use "$rawdatadir\consomen.dta",clear
#    *     use "$rawdatadir\consomen.dta", clear
# keep C13141 C13111 C13121 C13131 PONDMEN IDENT
# sort IDENT
# gen impot_autres_res= C13121 + C13131
# drop C13121 C13131
# save "`rev_disp2'"
        menage = survey.get_values(
            table = "menage",
# TODO: mettre en minuscules
#            variables = ['ie', 'REVTOT', 'REVACT', 'REVSOC', 'REVPAT', 'REV70', 'REV71', 'REVT_D', 'PODMEN', 'REV10', 'REV11', 'REV20', 'REV21'],
            ).sort(columns = ['ident'])

#        rev_disp.IDENT = rev_disp.IDENT.astype("int64")
#        menage.IDENT = menage.IDENT.astype("int64")
#        rev_disp.set_index('IDENT', inplace = True)
#        menage.set_index('IDENT', inplace = True)
        revenus = menage.join(rev_disp, how = "outer", rsuffix = "rev_disp")
#        revenus.rename(
#            columns = dict(
#                c13111 = "impot_res_ppal",
#                c13141 = "impot_revenu",
#                c13121 = "impot_autres_res",
#                C13111= "impot_res_ppal",
#                C13141= "impot_revenu",
#                REVTOT= "revtot",
#                REVACT= "revact",
#                REVSOC= "revsoc",
#                REVPAT= "revpat",
#                REV70= "somme_obl_recue",
#                REV71= "somme_libre_recue",
#                REVT_D= "autres_ress",
#                PONDMEN= "pondmen",
#                IDENT= "ident_men",
#                REV10= "act_indpt",
#                REV11= "autoverses",
#                REV20= "salaires",
#                REV21= "autres_rev",
#                ),
#            inplace = True
#            )


        revenus['imphab'] = 0.65 * (revenus.impot_res_ppal + revenus.impot_autres_res)
        revenus['impfon'] = 0.35 * (revenus.impot_res_ppal + revenus.impot_autres_res)

# label var ident_men "identifiant du ménage"
# label var somme_obl_recue "Pensions alimentaires, etc."
# label var act_indpt "Revenus d'activité indépendante"
# label var revpat "Revenus du patrimoine"
# label var salaires "Salaires"
# label var autres_rev "Autres revenus"
# label var impfon "Taxe foncière"
# label var imphab "Taxe d'habitation"
# label var pondmen "Pondération"
# label var revsoc "Revenus sociaux"
# label var revact "Revenus d'activité"
# label var impot_revenu "Impot sur le revenu"
# label var revtot "Revenu total"
# label var somme_libre_recue "Aides libres d'autres ménages"
# label var autoverses "Revenus auto-versés"
# label var autres_ress "Autres ressources"

        revenus = revenus.reset_index()
        del revenus
        temporary_store["revenus"] = revenus

# sort ident_men
# save "$datadir\revenus.dta", replace
#    }
#
#    if ${yearrawdata} == 2005 {
# tempfile rev_disp
# use "$rawdatadir\c05d.dta", clear
# keep c13111 c13121 c13141 pondmen ident_men
# sort ident_men
# save "`rev_disp'"

    elif year == 2005:
        c05d = survey.get_values(
            table = "c05d",
            variables = ['c13111', 'c13121', 'c13141', 'pondmen', 'ident_men'],
            )
        rev_disp = c05d.sort(columns = ['ident_men'])
        del c05d
        menage = survey.get_values(
            table = "menage",
            variables = ['ident_men', 'revtot', 'revact', 'revsoc', 'revpat', 'rev700_d', 'rev701_d',
                'rev999_d', 'rev100_d', 'rev101_d', 'rev200_d', 'rev201_d'],
            ).sort(columns = ['ident_men'])
        # TODO convertir ident_men qui est une string en entier et les utiliser comme index ?
        # rev_disp.ident_men = rev_disp.ident_men.astype("int64")  #
        # menage.ident_men = menage.ident_men.astype("int64")
        rev_disp.set_index('ident_men', inplace = True)
        menage.set_index('ident_men', inplace = True)
        revenus = pandas.concat([menage, rev_disp], axis = 1)
        revenus.rename(
            columns = dict(
                rev100_d = "act_indpt",
                rev101_d = "autoverses",
                rev200_d = "salaires",
                rev201_d = "autres_rev",
                rev700_d = "somme_obl_recue",
                rev701_d = "somme_libre_recue",
                rev999_d = "autres_ress",
                c13111 = "impot_res_ppal",
                c13141 = "impot_revenu",
                c13121 = "impot_autres_res",
                ),
            inplace = True
            )

        # * Ces pondérations (0.65 0.35) viennent de l'enquête BdF 1995 qui distingue taxe d'habitation et impôts fonciers. A partir de BdF 1995,
        # * on a calculé que la taxe d'habitation représente en moyenne 65% des impôts locaux, et que les impôts fonciers en représentenr 35%.
        # * On applique ces taux aux enquêtes 2000 et 2005.
        # gen imphab= 0.65*(impot_res_ppal + impot_autres_res)
        # gen impfon= 0.35*(impot_res_ppal + impot_autres_res)
        # drop impot_autres_res impot_res_ppal

        revenus['imphab'] = 0.65 * (revenus.impot_res_ppal + revenus.impot_autres_res)
        revenus['impfon'] = 0.35 * (revenus.impot_res_ppal + revenus.impot_autres_res)
        del revenus['impot_autres_res']
        del revenus['impot_res_ppal']
        #
        # label var ident_men "identifiant du ménage"
        # label var somme_obl_recue "Pensions alimentaires, etc."
        # label var act_indpt "Revenus d'activité indépendante"
        # label var revpat "Revenus du patrimoine"
        # label var salaires "Salaires"
        # label var autres_rev "Autres revenus"
        # label var impfon "Taxe foncière"
        # label var imphab "Taxe d'habitation"
        # label var pondmen "Pondération"
        # label var revsoc "Revenus sociaux"
        # label var revact "Revenus d'activité"
        # label var impot_revenu "Impot sur le revenu"
        # label var revtot "Revenu total"
        # label var somme_libre_recue "Aides libres d'autres ménages"
        # label var autoverses "Revenus auto-versés"
        # label var autres_ress "Autres ressources"
        # sort ident_men
        # save "$datadir\revenus.dta", replace
        #    }
        #
        #    * Calculer le revenu disponible avec et sans le loyer imputé
        #    tempfile revenus
        #    use "${datadir}\revenus.dta", clear
        #    sort ident_men
        #    save "`revenus'", replace
        #
        temporary_store["revenus_{}".format(year)] = revenus
        loyers_imputes = temporary_store["depenses_bdf_{}".format(year)]
        variables = ["0421"]
        loyers_imputes = loyers_imputes[variables]
        #    tempfile loyers_imp
        #    use "${datadir}\dépenses_BdF.dta", clear
        #    keep ident_men posteCOICOP depense
        #    keep if posteCOICOP=="0421"
        #    drop posteCOICOP
        #    rename depense loyer_impute
        loyers_imputes.rename(
            columns = {"0421": "loyer_impute"},
            inplace = True,
            )
        # label var loyer_impute "Loyer imputé fourni par l'INSEE (2000-2005) ou calculé par nous (1995)"
        # sort ident_men
        # save "`loyers_imp'", replace
        temporary_store["loyers_imputes_{}".format(year)] = loyers_imputes
        #    use "`revenus'", clear
        #    merge ident_men using "`loyers_imp'"
        #
        revenus = revenus.merge(loyers_imputes, left_index = True, right_index = True)
        # tab _m
        #    drop _m
        #    gen rev_disponible= revtot - impot_revenu - imphab
        #    replace rev_disponible = 0 if rev_disponible < 0
        #    gen rev_disp_loyerimput = rev_disponible + loyer_impute
        #    label var rev_disponible "Revenu disponible sans loyer imputé"
        #    label var rev_disp_loyerimput "Revenu disponible avec loyer imputé"
        revenus['rev_disponible'] = revenus.revtot - revenus.impot_revenu - revenus.imphab
        revenus['rev_disponible'] = revenus['rev_disponible'] * (revenus['rev_disponible'] >= 0)
        revenus['rev_disp_loyerimput'] = revenus.rev_disponible + revenus.loyer_impute
        #    sort ident_men
        #    save "${datadir}\revenus.dta", replace
        #
        temporary_store["revenus_{}".format(year)] = revenus


    elif year == 2010:
        c05 = survey.get_values(
            table = "c05",
            variables = ['c13111', 'c13121', 'c13141', 'pondmen', 'ident_me'],
            )
        rev_disp = c05.sort(columns = ['ident_me'])
        del c05
        menage = survey.get_values(
            table = "menage",
            variables = ['ident_me', 'revtot', 'revact', 'revsoc', 'revpat', 'rev700_d', 'rev701_d', 'rev999_d', 'rev100_d', 'rev101_d', 'rev200_d', 'rev201_d'],
            ).sort(columns = ['ident_me'])
        rev_disp.set_index('ident_me', inplace = True)
        menage.set_index('ident_me', inplace = True)
        revenus = pandas.concat([menage, rev_disp], axis = 1)
        revenus.rename(
            columns = dict(
                rev100_d = "act_indpt",
                rev101_d = "autoverses",
                rev200_d = "salaires",
                rev201_d = "autres_rev",
                rev700_d = "somme_obl_recue",
                rev701_d = "somme_libre_recue",
                rev999_d = "autres_ress",
                c13111 = "impot_res_ppal",
                c13141 = "impot_revenu",
                c13121 = "impot_autres_res",
                ),
            inplace = True
            )
        revenus['imphab'] = 0.65 * (revenus.impot_res_ppal + revenus.impot_autres_res)
        revenus['impfon'] = 0.35 * (revenus.impot_res_ppal + revenus.impot_autres_res)
        del revenus['impot_autres_res']
        del revenus['impot_res_ppal']
        temporary_store["revenus_{}".format(year)] = revenus
        loyers_imputes = temporary_store["depenses_bdf_{}".format(year)]
        variables = ["0421"]
        loyers_imputes = loyers_imputes[variables]
        loyers_imputes.rename(
            columns = {"0421": "loyer_impute"},
            inplace = True,
            )
        temporary_store["loyers_imputes_{}".format(year)] = loyers_imputes
        revenus = revenus.merge(loyers_imputes, left_index = True, right_index = True)
        revenus['rev_disponible'] = revenus.revtot - revenus.impot_revenu - revenus.imphab
        revenus['rev_disponible'] = revenus['rev_disponible'] * (revenus['rev_disponible'] >= 0)
        revenus['rev_disp_loyerimput'] = revenus.rev_disponible + revenus.loyer_impute
        temporary_store["revenus_{}".format(year)] = revenus


if __name__ == '__main__':
    import sys
    import time
    logging.basicConfig(level = logging.INFO, stream = sys.stdout)
    deb = time.clock()
    year = 2005
    build_homogeneisation_revenus_menages(year = year)

    log.info("step_0_4_homogeneisation_revenus_menages duration is {}".format(time.clock() - deb))

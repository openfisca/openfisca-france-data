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

# /* La base 95 permet de distinguer taxe d'habitation et impôts fonciers. On calcule leur montant relatif pour l'appliquer à 00 et 05 */


    if year == 1995:
        menrev = survey.get_values(
            table = "menrev",
            variables = [
                'revtot', 'ir', 'irbis', 'imphab', 'impfon', 'revaid', 'revsal', 'revind', 'revsec', 'revret',
                'revcho', 'revfam', 'revlog', 'revinv', 'revrmi', 'revpat', 'mena', 'ponderr'
                ],
            )
        menage = survey.get_values(
            table = "socioscm",
            variables = ['exdep', 'exrev', 'mena']
            )

        menage.set_index('mena')
        menrev = menrev.merge(menage, left_index = True, right_index = True)
        # cette étape de ne garder que les données dont on est sûr de la qualité et de la véracité
        # exdep = 1 si les données sont bien remplies pour les dépenses du ménage
        # exrev = 1 si les données sont bien remplies pour les revenus du ménage

        menrev = menrev[(menrev.exdep == 1) & (menrev.exrev == 1)]


        menrev['foncier_hab'] = menrev.imphab + menrev.impfon
        menrev['part_IMPHAB'] = menrev.imphab / menrev.foncier_hab
        menrev['part_IMPFON'] = menrev.impfon / menrev.foncier_hab

        menrev['revsoc'] = (
            menrev.revret + menrev.revcho + menrev.revfam + menrev.revlog + menrev.revinv + menrev.revrmi
            )
        for variable in ['revcho', 'revfam', 'revinv', 'revlog', 'revret', 'revrmi']:
            del menrev[variable]

        menrev['revact'] = menrev['revsal'] + menrev['revind'] + menrev['revsec']
        menrev.rename(
            columns = dict(
                revpat = "revpat",
                impfon = "impfon",
                imphab = "imphab",
                revaid = "somme_obl_recue",
                ),
            inplace = True
            )
        menrev['impot_revenu'] = menrev['ir'] + menrev['irbis']


        rev_disp = survey.get_values(
            table = "menrev",
            variables = ['revtot', 'revret', 'revcho', 'revfam', 'revlog', 'revinv', 'revrmi', 'imphab', 'impfon', 'revaid', 'revsal', 'revind', 'revsec', 'revpat', 'mena', 'ponderr', 'ir','irbis' ],
            )
        rev_disp.set_index('mena', inplace=True)

        menage2 = survey.get_values(
            table = "socioscm",
            variables = ['exdep', 'exrev', 'mena']
            )

        menage2.set_index('mena', inplace = True)
        rev_disp = menage2.merge(rev_disp, left_index = True, right_index = True)

        rev_disp = rev_disp[(rev_disp.exrev == 1) & (rev_disp.exdep == 1)]

        rev_disp['revsoc'] = rev_disp['revret'] + rev_disp['revcho'] + rev_disp['revfam'] + rev_disp['revlog'] + rev_disp['revinv'] + rev_disp['revrmi']
        rev_disp['impot_revenu'] = rev_disp['ir'] + rev_disp['irbis']

        rev_disp.rename(
            columns = dict(
                revaid = 'somme_obl_recue',
                ),
            inplace = True
            )
        rev_disp.somme_obl_recue = rev_disp.somme_obl_recue.fillna(0)

        rev_disp['revact'] = rev_disp['revsal'] + rev_disp['revind'] + rev_disp['revsec']

        rev_disp['revtot'] = rev_disp['revact'] + rev_disp['revpat'] + rev_disp['revsoc'] + rev_disp['somme_obl_recue']

        rev_disp['revact'] = rev_disp['revsal'] + rev_disp['revind'] + rev_disp['revsec']

        rev_disp.rename(
            columns = dict(
                ponderr = "pondmen",
                mena = "ident_men",
                revind = "act_indpt",
                revsal = "salaires",
                revsec = "autres_rev",
                ),
            inplace = True
            )

        rev_disp['autoverses'] = '0'
        rev_disp['somme_libre_recue'] = '0'
        rev_disp['autres_ress'] = '0'


#
# /* Le revenu disponible se calcule à partir de revtot à laquelle on retrancher la taxe d'habitation
# et l'impôt sur le revenu, plus éventuellement les CSG et CRDS.
# La variable revtot est la somme des revenus d'activité, sociaux, du patrimoine et d'aide. */
#
        rev_disp['rev_disponible'] = rev_disp.revtot - rev_disp.impot_revenu - rev_disp.imphab
        loyers_imputes = temporary_store['depenses_bdf_{}'.format(year)]
        loyers_imputes.rename(
            columns = {"0411": "loyer_impute"},
            inplace = True,
            )

        rev_dispbis = loyers_imputes.merge(rev_disp, left_index = True, right_index = True)
        rev_disp['rev_disp_loyerimput'] = rev_disp['rev_disponible'] - rev_dispbis['loyer_impute']

        for var in ['somme_obl_recue', 'act_indpt', 'revpat', 'salaires', 'autres_rev', 'rev_disponible', 'impfon', 'imphab', 'revsoc', 'revact', 'impot_revenu', 'revtot', 'rev_disp_loyerimput'] :
            rev_disp[var] = rev_disp[var] / 6.55957
# * CONVERSION EN EUROS

        temporary_store["revenus_{}".format(year)] = rev_disp

    elif year == 2000:
    # TODO: récupérer plutôt les variables qui viennent de la table dépenses (dans temporary_store)
        consomen = survey.get_values(
            table = "consomen",
            variables = ['c13141', 'c13111', 'c13121', 'c13131', 'pondmen', 'ident'],
            )
        rev_disp = consomen.sort(columns = ['ident'])
        del consomen


        menage = survey.get_values(
            table = "menage",
            variables = ['ident', 'revtot', 'revact', 'revsoc', 'revpat', 'rev70', 'rev71', 'revt_d', 'pondmen', 'rev10', 'rev11', 'rev20', 'rev21'],
            ).sort(columns = ['ident'])


        revenus = menage.join(rev_disp, how = "outer", rsuffix = "rev_disp")
        revenus.rename(
            columns = dict(
                c13111 = "impot_res_ppal",
                c13141 = "impot_revenu",
                c13121 = "impot_autres_res",
                rev70 = "somme_obl_recue",
                rev71 = "somme_libre_recue",
                revt_d= "autres_ress",
                ident = "ident_men",
                rev10 = "act_indpt",
                rev11 = "autoverses",
                rev20 = "salaires",
                rev21 = "autres_rev",
                ),
            inplace = True
            )

        var_to_ints = ['pondmen','impot_autres_res','impot_res_ppal','pondmenrev_disp','c13131']
        for var_to_int in var_to_ints:
            revenus[var_to_int] = revenus[var_to_int].astype(int)

        revenus['imphab'] = 0.65 * (revenus.impot_res_ppal + revenus.impot_autres_res)
        revenus['impfon'] = 0.35 * (revenus.impot_res_ppal + revenus.impot_autres_res)


        loyers_imputes = temporary_store["depenses_bdf_{}".format(year)]
        variables = ["0421"]
        loyers_imputes = loyers_imputes[variables]

        loyers_imputes.rename(
            columns = {"0421": "loyer_impute"},
            inplace = True,
            )

        temporary_store["loyers_imputes_{}".format(year)] = loyers_imputes

        loyers_imputes.index = loyers_imputes.index.astype('int')
        revenus = revenus.set_index('ident_men')
        revenus.index = revenus.index.astype('int')

        revenus = revenus.merge(loyers_imputes, left_index = True, right_index = True)

        revenus['rev_disponible'] = revenus.revtot - revenus.impot_revenu - revenus.imphab
        revenus['rev_disponible'] = revenus['rev_disponible'] * (revenus['rev_disponible'] >= 0)
        revenus['rev_disp_loyerimput'] = revenus.rev_disponible + revenus.loyer_impute

        var_to_ints = ['loyer_impute']
        for var_to_int in var_to_ints:
            revenus[var_to_int] = revenus[var_to_int].astype(int)


        temporary_store["revenus_{}".format(year)] = revenus



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

        #    * Calculer le revenu disponible avec et sans le loyer imputé

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

    elif year == 2011:
       try:
          c05 = survey.get_values(
            table = "C05",
            variables = ['c13111', 'c13121', 'c13141', 'pondmen', 'ident_me'],
            )
       except:
          c05 = survey.get_values(
            table = "c05",
            variables = ['c13111', 'c13121', 'c13141', 'pondmen', 'ident_me'],
            )
       rev_disp = c05.sort(columns = ['ident_me'])
       del c05
       try:
          menage = survey.get_values(
            table = "MENAGE",
            variables = ['ident_me', 'revtot', 'revact', 'revsoc', 'revpat', 'rev700', 'rev701', 'rev999', 'revindep', 'salaires'],
            ).sort(columns = ['ident_me'])
       except:
          menage = survey.get_values(
            table = "menage",
            variables = ['ident_me', 'revtot', 'revact', 'revsoc', 'revpat', 'rev700', 'rev701', 'rev999', 'revindep', 'salaires'],
            ).sort(columns = ['ident_me'])

#      variables = ['ident_me', 'revtot', 'revact', 'revsoc', 'revpat', 'rev700', 'rev701', 'rev999', 'revindep', 'rev101_d', 'salaires', 'rev201'],

       rev_disp.set_index('ident_me', inplace = True)
       menage.set_index('ident_me', inplace = True)
       revenus = pandas.concat([menage, rev_disp], axis = 1)
       revenus.rename(
            columns = dict(
                revindep = "act_indpt",
#TODO: trouver ces revenus commentés dans bdf 2011
#                rev101_d = "autoverses",
                salaires = "salaires",
#                rev201_d = "autres_rev",
                rev700 = "somme_obl_recue",
                rev701 = "somme_libre_recue",
                rev999 = "autres_ress",
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
    year = 2000
    build_homogeneisation_revenus_menages(year = year)

    log.info("step_0_4_homogeneisation_revenus_menages duration is {}".format(time.clock() - deb))

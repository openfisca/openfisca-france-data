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



log = logging.getLogger(__name__)

from openfisca_france_data import default_config_files_directory as config_files_directory
from openfisca_france_data.temporary import TemporaryStore
from openfisca_survey_manager.survey_collections import SurveyCollection

temporary_store = TemporaryStore.create(file_name = "indirect_taxation_tmp")


# **************************************************************************************************************************
# * Etape n° 0-1-2 : IMPUTATION DE LOYERS POUR LES MENAGES PROPRIETAIRES
# **************************************************************************************************************************
def build_imputation_loyers_proprietaires(year = None):
    """Build menage consumption by categorie fiscale dataframe """

    assert year is not None
    # Load data
    bdf_survey_collection = SurveyCollection.load(collection = 'budget_des_familles',
        config_files_directory = config_files_directory)
    survey = bdf_survey_collection.get_survey('budget_des_familles_{}'.format(year))

    if year == 1995:
        imput00 = survey.get_values(table = "socioscm")

        imput00 = imput00[(imput00.exdep == 1) & (imput00.exrev == 1)]
        kept_variables = ['mena', 'stalog', 'surfhab', 'confort1', 'confort2', 'confort3', 'confort4', 'ancons', 'sitlog', 'nbphab', 'rg', 'cc']
        imput00 = imput00[kept_variables]
        imput00.rename(columns = {'mena' : 'ident_men'}, inplace = True)

        #TODO: continue variable cleaning
        var_to_filnas = ['surfhab']
        for var_to_filna in var_to_filnas:
            imput00[var_to_filna] = imput00[var_to_filna].fillna(0)
        var_to_ints = ['sitlog', 'confort1', 'stalog', 'surfhab','ident_men','ancons','nbphab']
        for var_to_int in var_to_ints:
            imput00[var_to_int] = imput00[var_to_int].astype(int)

        depenses = temporary_store['depenses_{}'.format(year)]
        depenses.reset_index(inplace = True)
        depenses_small = depenses[['ident_men', '04110', 'pondmen']]
        imput00 = depenses_small.merge(imput00, on = 'ident_men').set_index('ident_men')
        imput00.rename(columns = {'04110' : 'loyer_reel'}, inplace = True)

#		* une indicatrice pour savoir si le loyer est connu et l'occupant est locataire
#		gen observe = (loyer_reel != . & inlist(STALOG,"3","4"))
#		gen loyer_impute = loyer_reel
#		gen maison_appart = (SITLOG == "1")
#		gen catsurf = 1 if SURF < 16
#		replace catsurf = 1 if SURF > 15 & SURF < 31
#		replace catsurf = 3 if SURF > 30 & SURF < 41
#		replace catsurf = 4 if SURF > 40 & SURF < 61
#		replace catsurf = 5 if SURF > 60 & SURF < 81
#		replace catsurf = 6 if SURF > 80 & SURF < 101
#		replace catsurf = 7 if SURF > 100 & SURF < 151
#		replace catsurf = 8 if SURF > 150
#		replace maison  = 0 if CC == "5" & catsurf == 1 & maison == 1
#		replace maison  = 0 if CC == "5" & catsurf == 3 & maison == 1
#		replace maison  = 0 if CC == "5" & catsurf == 8 & maison == 1
#		replace maison  = 0 if CC == "4" & catsurf == 1 & maison == 1
# 		sort ident_men
        imput00['observe'] = (imput00.loyer_reel > 0) & (imput00.stalog.isin([3, 4]))
#        imput00['loyer_impute'] = imput00['loyer_reel']
        imput00['maison_appart'] = imput00.sitlog == 1
        imput00['catsurf'] = imput00.surfhab < 16
        imput00.catsurf = 1 * ((imput00.surfhab > 15) & (imput00.surfhab < 31))
        imput00.catsurf = 3 * ((imput00.surfhab > 30) & (imput00.surfhab < 41))
        imput00.catsurf = 4 * ((imput00.surfhab > 40) & (imput00.surfhab < 61))
        imput00.catsurf = 5 * ((imput00.surfhab > 60) & (imput00.surfhab < 81))
        imput00.catsurf = 6 * ((imput00.surfhab > 80) & (imput00.surfhab < 101))
        imput00.catsurf = 7 * ((imput00.surfhab > 100) & (imput00.surfhab < 151))
        imput00.catsurf = 8 * (imput00.surfhab > 150)
        imput00.maison = 1 - ((imput00.cc == 5) & (imput00.catsurf == 1) & (imput00.maison_appart == 1))
        imput00.maison = 1 - ((imput00.cc == 5) & (imput00.catsurf == 3) & (imput00.maison_appart == 1))
        imput00.maison = 1 - ((imput00.cc == 5) & (imput00.catsurf == 8) & (imput00.maison_appart == 1))
        imput00.maison = 1 - ((imput00.cc == 4) & (imput00.catsurf == 1) & (imput00.maison_appart == 1))
#
#
#        TODO: continuer sur le modèle des lignes précédentes
#        imput00.catsurf[imput00.surfhab > 40 & imput00.surfhab < 61] = 4
#        imput00.catsurf[imput00.surfhab > 60 & imput00.surfhab < 81] = 5
#        imput00.catsurf[imput00.surfhab > 80 & imput00.surfhab < 101] = 6
#        imput00.catsurf[imput00.surfhab > 100 & imput00.surfhab < 151] = 7
#        imput00.catsurf[imput00.surfhab > 150] = 8
#        imput00.maison[imput00.CC == 5 & imput00.catsurf == 3 & imput00.maison == 1] = 0
#        imput00.maison[imput00.CC == 5 & imput00.catsurf == 8 & imput00.maison == 1] = 0
#        imput00.maison[imput00.CC == 4 & imput00.catsurf == 1 & imput00.maison == 1] = 0

#
#		save "`loyers'", replace
#
#		hotdeck loyer_imput using "$rawdatadir\hotdeck", store by(catsurf CC maison_appart) keep(ident_men loyer_imput observe)
#		replace loyer_imput = . if observe == 1
#        loyers.loyer_imput[loyers.observe == 1] = '.'
        # TODO:

#		use "$rawdatadir\hotdeck1.dta", clear
#		keep ident_men loyer_imput
#		sort ident_men
#		save "$rawdatadir\hotdeck1.dta", replace
#
#		use "`loyers'", clear
#		merge ident_men using "$rawdatadir\hotdeck1.dta", update
#		tab _m observe
#		drop _m

        hotdeck = survey.get_values(table = 'hotdeck_result')
        kept_variables = ['ident_men', 'loyer_impute']
        hotdeck = hotdeck[kept_variables]
        imput00.reset_index(inplace = True)
        imput00 = imput00.merge(hotdeck, on = 'ident_men').set_index('ident_men')

#        replace loyer_impute = 0 if observe == 1
#		gen imputation = (observe == 0)
#		label var imputation "Un loyer a été imputé (oui = 1, non = 0)"
#		rename STALOG stalog
#		keep ident_men loyer_imp imputation observe stalog
#		sort ident_men
#		save "`loyers'", replace
#		use "`depenses'", clear
#		sort ident_men posteCOICOP
#		merge m:1 ident_men using "`loyers'"

        imput00.loyer_impute[imput00.observe == 1] = 0
        imput00['imputation'] = imput00.observe == 0
        imput00.reset_index(inplace = True)
        loyers_imputes = imput00[['ident_men', 'loyer_impute']]
        loyers_imputes.set_index('ident_men', inplace = True)
        depenses = coicop_data_frame.merge(poids, left_index = True, right_index = True)
        # TODO:

#		noisily: replace depense = 0 if posteCOICOP == "0411" & inlist(stalog,"1","2","5") & depense > 0 & depense != .
#		noisily: replace depense = 0 if posteCOICOP == "0411" & inlist(stalog,"1","2","5") & depense == .
        depenses.depense[depense.posteCOICOP == "0411" & depenses.stalog.isin([1,2,5])& depenses.depense > 0 & depenses.depense != '.'] = 0
        depenses.depense[depenses.posteCOICOP == "0421"  & depenses.observe == 0] = depenses['loyer_impute']
        depenses.depense[depenses.posteCOICOP == "0421"  & depenses.observe == 1 & depenses.depense == '.'] = 0
#
#		replace depense = loyer_imp if posteCOICOP == "0421"  & observe == 0
#		replace depense = 0 		if posteCOICOP == "0421"  & observe == 1 & depense == .
#		drop observe stalog loyer_impute
#		tab  _m
#		drop _m
#	}
#
#
#
#			* POUR BdF 2000 ET 2005, ON UTILISE LES LOYERS IMPUTES CALCULES PAR L'INSEE
#
#
#	if ${yearrawdata} == 2000 {
#		tempfile loyers_imputes
#		* Garder les loyers imputés (disponibles dans la table sur les ménages)
#		use "$rawdatadir\menage.dta", clear
#		keep IDENT REV81
#		rename IDENT ident_men
#		gen posteCOICOP = "0421"
#		rename REV81 depense
#		sort ident_men posteCOICOP
#		save "`loyers_imputes'", replace
#		use "`depenses'", clear
#		sort ident_men posteCOICOP
#		merge 1:1 ident_men posteCOICOP using "`loyers_imputes'", update
#		tab _m
#		tab _m if posteCOICOP == "0421"
#		drop _m
#	}
#
#	if ${yearrawdata} == 2005 {
#		* Garder les loyers imputés (disponibles dans la table sur les ménages)
#		tempfile loyers_imputes
#		use "$rawdatadir\menage.dta", clear
#		keep ident_men rev801_d
#		gen posteCOICOP = "0421"
#		rename rev801_d depense
#		sort ident_men poste
#		save "`loyers_imputes'", replace
#		use "`depenses'", clear
#		sort ident_men posteCOICOP
#		merge 1:1 ident_men posteCOICOP using "`loyers_imputes'", update keepusing(depense)
#		tab _m
#		tab _m if posteCOICOP == "0421"
#		drop _m
#	}


    if year == 2000:
        loyers_imputes = survey.get_values(table = "menage", variables = ['ident', 'rev81'])
        loyers_imputes.rename(
            columns = {
                'ident': 'ident_men',
                'rev81': '0421',
                },
            inplace = True,
            )
        depenses = survey.get_values(table = 'depmen')

    if year == 2005:
        loyers_imputes = survey.get_values(table = "menage")
        kept_variables = ['ident_men', 'rev801_d']
        loyers_imputes = loyers_imputes[kept_variables]
        loyers_imputes.rename(columns = {'rev801_d': '0421'}, inplace = True)


    if year == 2011:
        loyers_imputes = survey.get_values(table = "menage")
        kept_variables = ['ident_me', 'rev801']
        loyers_imputes = loyers_imputes[kept_variables]
        loyers_imputes.rename(columns = {'rev801': '0421', 'ident_me': 'ident_men'},
                              inplace = True)

    # Joindre à la table des dépenses par COICOP
    loyers_imputes.set_index('ident_men', inplace = True)
    temporary_store['loyers_imputes_{}'.format(year)] = loyers_imputes
    depenses = temporary_store['depenses_{}'.format(year)]
    depenses = depenses.merge(loyers_imputes, left_index = True, right_index = True)

    # Sauvegarde de la base depenses mise à jour


#**************************************************************************************************************************
#* Etape n° 0-1-3 : SAUVER LES BASES DE DEPENSES HOMOGENEISEES DANS LE BON DOSSIER
#**************************************************************************************************************************
#
#
#	sort posteCOICOP
#	save "`depenses'", replace
#
#	keep  ident_men pondmen posteCOICOP poste13 grosposte depense description supplementaire nondurable semidurable durable servicenondurable servicedurable loyer depensenonconso
#	order ident_men pondmen posteCOICOP poste13 grosposte depense description supplementaire nondurable semidurable durable servicenondurable servicedurable loyer depensenonconso
#	save "${datadir}\dépenses_BdF.dta", replace



    # Save in temporary store
    temporary_store['depenses_bdf_{}'.format(year)] = depenses


if __name__ == '__main__':
    import sys
    import time
    logging.basicConfig(level = logging.INFO, stream = sys.stdout)
    deb = time.clock()
    year = 2011
    build_imputation_loyers_proprietaires(year = year)
    log.info("step 0_1_2_build_imputation_loyers_proprietaires duration is {}".format(time.clock() - deb))

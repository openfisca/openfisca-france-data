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


from openfisca_survey_manager.surveys import SurveyCollection

log = logging.getLogger(__name__)

from openfisca_france_data.temporary import TemporaryStore

temporary_store = TemporaryStore.create(file_name = "indirect_taxation_tmp")


#**************************************************************************************************************************
#* Etape n° 0-1-2 : IMPUTATION DE LOYERS POUR LES MENAGES PROPRIETAIRES
#**************************************************************************************************************************
#
#	if ${yearrawdata} == 1995 {
#		* L'enquête BdF 1995 ne contient pas de loyer imputés, donc Super-Roy les calcule!
#
#		use "$rawdatadir\socioscm.dta", clear
#		tempfile imput00
#
#		* On sélectionne les variables sur les ménages nécessaires au calcul des loyers imputés.
#		keep MENA STALOG SURFHAB CONFORT1 CONFORT2 CONFORT3 CONFORT4 ANCONS SITLOG PONDERRD NBPHAB RG CC
#		rename MENA ident_men
#		keep if PONDERRD != .
#		sort ident_men
#		des ident_men
#		save "`imput00'", replace
#
#		* On récupère les loyers réels dans la base de consommation.
#		tempfile loyers
#		use "`depenses'", clear
#		keep if posteCOICOP=="0411"
#		keep ident_men posteCOICOP depense
#		sort ident_men
#		merge 1:1 ident_men using "`imput00'"
#		tab _m
#		drop _m
#		rename depense loyer_reel
#		rename PONDERRD PONDMEN
#
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
#
#		save "`loyers'", replace
#
#		hotdeck loyer_imput using "$rawdatadir\hotdeck", store by(catsurf CC maison_appart) keep(ident_men loyer_imput observe)
#		replace loyer_imput = . if observe == 1
#		use "$rawdatadir\hotdeck1.dta", clear
#		keep ident_men loyer_imput
#		sort ident_men
#		save "$rawdatadir\hotdeck1.dta", replace
#
#		use "`loyers'", clear
#		merge ident_men using "$rawdatadir\hotdeck1.dta", update
#		tab _m observe
#		drop _m
#
#		replace loyer_impute = 0 if observe == 1
#		gen imputation = (observe == 0)
#		label var imputation "Un loyer a été imputé (oui = 1, non = 0)"
#		rename STALOG stalog
#		keep ident_men loyer_imp imputation observe stalog
#		sort ident_men
#		save "`loyers'", replace
#		use "`depenses'", clear
#		sort ident_men posteCOICOP
#		merge m:1 ident_men using "`loyers'"
#		noisily: replace depense = 0 if posteCOICOP == "0411" & inlist(stalog,"1","2","5") & depense > 0 & depense != .
#		noisily: replace depense = 0 if posteCOICOP == "0411" & inlist(stalog,"1","2","5") & depense == .
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


def build_imputation_loyers_proprietaires(year = None):
    """Build menage consumption by categorie fiscale dataframe """

    assert year is not None
    # Load data
    bdf_survey_collection = SurveyCollection.load(collection = 'budget_des_familles')
    survey = bdf_survey_collection.surveys['budget_des_familles_{}'.format(year)]

    if year == 2000:
        loyers_imputes = survey.get_values(table = "menage", variables = ['ident', 'rev81'])
        loyers_imputes.rename(
            columns = {
                'ident': 'ident_men',
                'rev81': '0421',
                },
            inplace = True,
            )
        

    if year == 2005:
        loyers_imputes = survey.get_values(table = "menage")
        kept_variables = ['ident_men', 'rev801_d']
        loyers_imputes = loyers_imputes[kept_variables]
        loyers_imputes.rename(columns = {'rev801_d': '0421'}, inplace = True)

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
    year = 2005
    build_imputation_loyers_proprietaires(year = year)
    log.info("step 0_1_2_build_imputation_loyers_proprietaires duration is {}".format(time.clock() - deb))

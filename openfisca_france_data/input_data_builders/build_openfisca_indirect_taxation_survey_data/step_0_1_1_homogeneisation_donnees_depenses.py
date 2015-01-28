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



#
#		* CE CODE APPELLE LE TABLEAU DE PASSAGE DE LA NOMENCLATURE BDF A LA NOMENCLATURE COICOP MODIFIEE
#		tempfile nomen
#		import excel using "$paramdir\Matrice passage ${yearrawdata}-COICOP.xls", first clear
#		sort poste${yearrawdata}
#		save "`nomen'"
#
#		* HOMOGENEISATION DES BASES DE DONNEES DE DEPENSES
#		if ${yearrawdata} == 1995 {
#			tempfile ponder
#			use "$rawdatadir\socioscm.dta", clear
#			keep if EXDEP == 1 & EXREV == 1
#			keep MENA PONDERRD
#			sort MENA
#			codebook MENA
#			save "`ponder'"
#
#			use "$rawdatadir\depnom.dta", clear
#			collapse (sum) VALEUR MONTANT, by(MENA NOMEN5)
#			rename NOMEN5 poste${yearrawdata}
#			rename VALEUR  depense
#			rename MONTANT depense_avt_imput
#			* PASSAGE A l'EURO!!!
#			replace depense 			= depense / 6.55957
#			replace depense_avt_imput 	= depense / 6.55957
#			sort MENA
#			merge m:1 MENA using "`ponder'"
#			codebook MENA if _merge == 3
#			drop if _merge != 3
#			drop _merge
#			rename MENA ident_men
#			rename PONDERRD pondmen
#
#			}
#
#		if ${yearrawdata} == 2000 {
#			use "$rawdatadir\consomen.dta", clear
#			order IDENT PONDMEN CTOTALE  C01 C02 C03 C04 C05 C06 C07 C08 C09 C10 C11 C12 C13, first
#			drop CTOTALE C01-C13 C99 C99999
#			*keep if _n < 300
#			reshape long C, i(IDENT) j(poste${yearrawdata}, s)
#			rename C depense
#			rename IDENT ident_men
#			rename PONDMEN pondmen
#		}
#
#		if ${yearrawdata} == 2005 {
#			use "$rawdatadir\c05d.dta", clear
#			order _all, alpha
#			*keep if _n < 100
#			order ident pondmen, first
#			reshape long c, i(ident) j(poste${yearrawdata}, s)
#			rename c depense
#			sort ident_men poste
#		}
#
#	order ident pondmen poste depense
#	sort poste
#	* Fusionner le tableau de passage sur les données de consommation
#	merge m:1 poste${datayear} using "`nomen'"
#	quietly tab _merge
#	local test `= r(min)'
#	if `test' == 1 {
#		dis "Il y a un problème dans le tableau de passage: certains postes de dépenses de la base BdF " ///
#		"${yearrawdata} n'ont pas de poste correspondant dans la nomenclature COICOP modifiée." ///
#		" Type q to continue, type BREAK to stop."
#		pause
#	}
#	tab posteCOICOP if _m == 2
#	drop if _merge == 2
#	drop _merge
#
#	* OBTENIR LES DEPENSES PAR MENAGE ET PAR POSTE DE LA NOMENCLATURE COMMUNE
#	collapse (sum) depense (mean) pondmen, by(ident_men posteCOICOP)
#	sort posteCOICOP
#	preserve
#	tempfile poids
#	keep ident_men pondmen
#	duplicates drop ident_men, force
#	sort ident_men
#	save "`poids'"
#	restore
#
#	preserve
#	tempfile coicop
#	import excel "$paramdir\Nomenclature commune.xls", clear first sheet("nomenclature")
#	sort posteCOICOP
#	*keep codeCOICOP description
#	save "`coicop'"
#	restore
#
#	merge posteCOICOP using "`coicop'"
#	quietly tab _merge
#	local test2 `= r(min)'
#	if `test2' == 1 {
#		dis "Il y a un problème: certains postes de dépenses n'ont pas de poste correspondant dans la nomenclature COICOP modifiée." ///
#		" Type q to continue, type BREAK to stop."
#		pause
#	}
#	drop _merge
#	fillin posteCOICOP ident_men
#	drop _fillin
#	drop if ident_men == ""
#	merge m:1 posteCOICOP using "`coicop'", update
#	tab _m
#	drop _m
#	merge m:1 ident_men using "`poids'", update keepusing(pondmen)
#	tab _m
#	drop _m
#	sort ident posteCOICOP
#	tempfile depenses
#	save "`depenses'"




def build_depenses_homogenisees(year = None):
    """Build menage consumption by categorie fiscale dataframe """

    assert year is not None
    # Load data
    bdf_survey_collection = SurveyCollection.load(collection = 'budget_des_familles')

    if year == 2005:
        survey = bdf_survey_collection.surveys['budget_des_familles_{}'.format(year)]
        c05d = survey.get_values(table = "c05d")
        c05d.rename(columns = {'c' : 'depense'}, inplace = True)
        nomen = temporary_store['nomen_{}'.format(year)]
        c05d.merge(nomen, on = ['poste_{}'.format(year)], )


    return None



if __name__ == '__main__':
    import sys
    import time
    logging.basicConfig(level = logging.INFO, stream = sys.stdout)
    deb = time.clock()
    year = 2005
    build_depenses_homogenisees(year = year)

    log.info("duration is {}".format(time.clock() - deb))

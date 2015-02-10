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
#**************************************************************************************************************************
#* Etape n° 0-3 : HOMOGENEISATION DES CARACTERISTIQUES SOCIALES DES MENAGES
#**************************************************************************************************************************
#**************************************************************************************************************************

#tempfile carac_sociales
#	if ${yearrawdata} == 1995 {
#
#		tempfile vague
#		use "$rawdatadir\sociodem.dta", clear
#		keep if ponderrd != .
#		keep mena v
#		rename v vag
#		rename mena ident_men
#		save `vague', replace
#
#		use "$rawdatadir\socioscm.dta", clear
#		* Remettre en minuscule le nom et les labels de toutes les variables
#		foreach v of var * {
#			local L`v' : variable label `v'
#			local l`v' = lower(`"`L`v''"')
#			label var `v' "`l`v''"
#			local w = lower("`v'")
#			rename `v' `w'
#		}
#
#		tempfile menages
#		keep ponderrd nbpers nbenf typmen1 cohabpr sexepr agepr agecj matripr ///
#		occuppr occupcj nbact sitlog stalog mena nm14a
#		rename mena ident_men
#		rename ponderrd pondmen
#		* On ne garde que les ménages pour lesquelles les dépenses ET les revenus sont bien renseignés.
#		* C'est ce qui a été fait pour BdF 2000 et 2005, donc on fait pareil par souci de cohérence.
#		keep if pondmen != .
#		merge 1:1 ident_men using `vague'
#		tab _m
#		drop _m
#
#		rename nbpers npers
#		rename nm14a  nenfants
#		rename nbenf  nenfhors
#		gen nadultes = npers - nenfants
#		rename nbact nactifs
#		gen ocde10 = 1 + 0.5 * max(0, nadultes - 1) + 0.3 * nenfants
#		gen typmen5 = 0
#		replace typmen5 = 1 if typmen1 == "1"
#		replace typmen5 = 2 if typmen1 == "6"
#		replace typmen5 = 3 if typmen1 == "2"
#		replace typmen5 = 4 if inlist(typmen1,"3","4","5")
#		replace typmen5 = 5 if typmen1 == "7"
#		drop typmen1
#		rename cohab couplepr
#		destring couplepr, replace
#		rename matripr etamatri
#		destring etamatri, replace
#		foreach x in "cj" "pr" {
#			gen situa`x' = 0
#			replace situa`x' = 1 if occup`x' == "1"
#			* On ne peut pas distinguer les apprentis des étudiants
#			*replace situa`x' = 2 if occupa`x' == "1"
#			replace situa`x' = 3 if occup`x' == "3"
#			replace situa`x' = 4 if occup`x' == "2"
#			replace situa`x' = 5 if inlist(occup`x',"5","6")
#			replace situa`x' = 6 if occup`x' == "7"
#			replace situa`x' = 7 if occup`x' == "8"
#			replace situa`x' = 8 if occup`x' == "4"
#			drop occup`x'
#		}
#
#		gen typlog = 0
#		replace typlog = 1 if sitlog == "1"
#		replace typlog = 2 if typlog == 0
#		drop sitlog
#
#		destring stalog, replace
#
#		sort ident_men
#		save "`menages'", replace
#
#
#		use "$rawdatadir\individu.dta", clear
#			foreach v of var * {
#			local L`v' : variable label `v'
#			local l`v' = lower(`"`L`v''"')
#			label var `v' "`l`v''"
#			local w = lower("`v'")
#			rename `v' `w'
#		}
#		tempfile individus
#		rename mena ident_men
#		keep if lien == "1" | lien == "2"
#		gen lettre = "pr" if lien == "1"
#		replace lettre = "cj" if lien == "2"
#		rename natio nationalite
#		gen natio = 1 if inlist(nationalite,"01","02")
#		replace natio = 2 if natio != 1
#		destring dieg diep dies, replace
#		replace dies = 0 if dies == 99
#		replace diep = 0 if diep == 99
#		replace dieg = 0 if dieg == 99
#		egen dipmax = rowmax(dieg diep dies)
#		gen dip14 = 0
#		replace dip14 = 10 if dipmax == 47
#		replace dip14 = 12 if dipmax == 48
#		replace dip14 = 20 if dipmax == 46
#		replace dip14 = 30 if inlist(dipmax,41,45)
#		replace dip14 = 31 if inlist(dipmax,42,43)
#		replace dip14 = 33 if dipmax == 44
#		replace dip14 = 41 if inlist(dipmax,16,17,18,19)
#		replace dip14 = 42 if inlist(dipmax,32,36)
#		replace dip14 = 43 if dipmax == 34
#		replace dip14 = 44 if dipmax == 39
#		replace dip14 = 50 if inlist(dipmax,21,23,25,27,29)
#		replace dip14 = 60 if inlist(dipmax,15)
#		replace dip14 = 70 if dipmax == 2
#		replace dip14 = 71 if inlist(dipmax,0,.)
#		keep ident_men natio dip14 lettre pcs sexe
#		rename pcs cs42
#		reshape wide natio dip14 cs42 sexe, i(ident_men) j(lettre) string
#		sort ident_men
#		save "`individus'", replace
#
#		use "`menages'", clear
#		merge ident_men using "`individus'", update
#		tab _m
#		drop if _m == 2
#		drop _m
#		dis _N
#		sort ident_men
#		save "`menages'", replace
#
#		use "$rawdatadir\individu.dta", clear
#			foreach v of var * {
#			local L`v' : variable label `v'
#			local l`v' = lower(`"`L`v''"')
#			label var `v' "`l`v''"
#			local w = lower("`v'")
#			rename `v' `w'
#		}
#		drop if lien == "1" | lien == "2"
#		keep mena anais
#		rename mena ident_men
#		destring anais, replace
#		gen age = ${yearrawdata} - anais
#		gsort + ident_men - age
#		sort ident_men
#		gen numero = 3 if ident_men != ident_men[_n-1]
#		replace numero = numero[_n-1] + 1 if ident_men == ident_men[_n-1]
#		keep ident_men numero age
#		tempname mean var
#		sum numero
#		local max = `r(max)'
#		reshape wide age, i(ident_men) j(numero)
#		forvalues i = 3(1)`max' {
#			label var age`i' "Age de la `i'ème personne du ménage au 31/12/${yearrawdata}"
#		}
#		sort ident_men
#		save "`individus'", replace
#		use "`menages'", clear
#		merge 1:1 ident_men using "`individus'"
#		tab npers _m
#		drop if _m == 2
#		drop _m
#		sort ident_men
#
#
#
#	}
#
#
#
#	if ${yearrawdata} == 2000 {
#
#		use "$rawdatadir\menage.dta", clear
#		foreach v of var * {
#			local L`v' : variable label `v'
#			local l`v' = lower(`"`L`v''"')
#			label var `v' "`l`v''"
#			local w = lower("`v'")
#			rename `v' `w'
#		}
#		tempfile menages
#		keep ident pondmen nbact nbenf1 nbpers ocde10 sitlog stalog strate typmen1 zeat stalog vag ///
#		/*infos sur la personne de référence et conjoint*/ ///
#		sexepr sexecj agepr agecj napr nacj cs2pr cs2cj diegpr dieppr diespr diegcj diepcj diescj ///
#		hod_nb matripr cohabpr occupapr occupacj occupbpr occupbcj occupcpr occupccj
#
#		replace ocde10 = ocde10 / 10
#		rename cs2pr cs42pr
#		rename cs2cj cs42cj
#		rename ident ident_men
#		rename nbact nactifs
#		rename nbenf1 nenfants
#		rename nbpers npers
#		rename hod_nb nenfhors
#		rename matripr etamatri
#		rename cohabpr couplepr
#		destring couplepr, replace
#		destring etamatri, replace
#		gen nadultes = npers - nenfants
#		gen typmen5 = 0
#		label var typmen5  "Type de ménage"
#		replace typmen5 = 1 if typmen1 == "1"
#		replace typmen5 = 2 if typmen1 == "6"
#		replace typmen5 = 3 if typmen1 == "2"
#		replace typmen5 = 4 if inlist(typmen1,"3","4","5")
#		replace typmen5 = 5 if typmen1 == "7"
#		drop typmen1
#		foreach x in "cj" "pr" {
#			gen situa`x' = 0
#			replace situa`x' = 1 if occupa`x' == "1"
#			* On ne peut pas distinguer les apprentis des étudiants
#			*replace situa`x' = 2 if occupa`x' == "1"
#			replace situa`x' = 3 if occupc`x' == "3"
#			replace situa`x' = 4 if occupc`x' == "2"
#			replace situa`x' = 5 if inlist(occupc`x',"5","6")
#			replace situa`x' = 6 if occupc`x' == "7"
#			replace situa`x' = 7 if occupc`x' == "8"
#			replace situa`x' = 8 if occupc`x' == "4"
#			drop occupa`x' occupb`x' occupc`x'
#		}
#
#		foreach x in "cj" "pr" {
#			destring dieg`x' diep`x' dies`x', replace
#			egen dipmax`x' = rowmax(dieg`x' diep`x' dies`x')
#			gen dip14`x' = 0
#			replace dip14`x' = 10 if dipmax`x' == 47
#			replace dip14`x' = 12 if dipmax`x' == 48
#			replace dip14`x' = 20 if dipmax`x' == 46
#			replace dip14`x' = 30 if inlist(dipmax`x',41,45)
#			replace dip14`x' = 31 if inlist(dipmax`x',42,43)
#			replace dip14`x' = 33 if dipmax`x' == 44
#			replace dip14`x' = 41 if inlist(dipmax`x',16,17,18,19)
#			replace dip14`x' = 42 if inlist(dipmax`x',32,36)
#			replace dip14`x' = 43 if dipmax`x' == 34
#			replace dip14`x' = 44 if dipmax`x' == 39
#			replace dip14`x' = 50 if inlist(dipmax`x',21,23,25,27,29)
#			replace dip14`x' = 60 if inlist(dipmax`x',15)
#			replace dip14`x' = 70 if dipmax`x' == 2
#			replace dip14`x' = 71 if inlist(dipmax`x',0,.)
#			drop dieg`x' diep`x' dies`x' dipmax`x'
#		}
#
#		foreach x in "cj" "pr" {
#			destring na`x', replace
#			gen natio`x' = 0
#			replace natio`x' = 1 if inlist(na`x',1,2)
#			replace natio`x' = 2 if inlist(na`x',3)
#			drop na`x'
#		}
#
#		gen typlog = 0
#		replace typlog = 1 if sitlog == "1"
#		replace typlog = 2 if typlog == 0
#		drop sitlog
#
#		destring stalog, replace
#
#		sort ident_men
#		save "`menages'", replace
#
#		use "$rawdatadir\individus.dta", clear
#		foreach v of var * {
#			local L`v' : variable label `v'
#			local l`v' = lower(`"`L`v''"')
#			label var `v' "`l`v''"
#			local w = lower("`v'")
#			rename `v' `w'
#		}
#		tempfile individus
#		keep if lien == "1"
#		keep ident matri
#		rename ident ident_men
#		rename matri etamatri
#		sort ident_men
#		save "`individus'", replace
#		use "`menages'", clear
#		merge ident_men using "`individus'"
#		drop _m
#		sort ident_men
#		save "`menages'", replace
#
#		use "$rawdatadir\individus.dta", clear
#		foreach v of var * {
#			local L`v' : variable label `v'
#			local l`v' = lower(`"`L`v''"')
#			label var `v' "`l`v''"
#			local w = lower("`v'")
#			rename `v' `w'
#		}
#		rename ident ident_men
#		* Garder toutes les personnes du ménage qui ne sont pas la personne de référence et le conjoint
#		keep if lien != "1" & lien != "2"
#		* On va recalculer l'âge pour l'avoir au 31/12 de l'année des données
#		drop age
#		destring anais, replace
#		gen age = ${yearrawdata} - anais
#		gsort + ident_men - age
#		sort ident_men
#		gen numero = 3 if ident_men != ident_men[_n-1]
#		replace numero = numero[_n-1] + 1 if ident_men == ident_men[_n-1]
#		keep ident_men numero age
#		tempname mean var
#		sum numero
#		local max = `r(max)'
#		reshape wide age, i(ident_men) j(numero)
#		forvalues i = 3(1)`max' {
#			label var age`i' "Age de la `i'ème personne du ménage au 31/12/${yearrawdata}"
#		}
#		sort ident_men
#		save "`individus'", replace
#		use "`menages'", clear
#		merge 1:1 ident_men using "`individus'"
#		tab npers _m
#		drop _m
#		sort ident_men
#
#	}
#
#	if ${yearrawdata} == 2005 {
#
#		use "$rawdatadir\menage.dta", clear
#		quietly foreach v of var * {
#			local L`v' : variable label `v'
#			local l`v' = lower(`"`L`v''"')
#			label var `v' "`l`v''"
#			local w = lower("`v'")
#			rename `v' `w'
#		}
#		tempfile menages
#		keep ///
#		/* données socio-démographiques */ ///
#		agpr agcj couplepr dip14* ident_men nactifs natio7* ///
#		nenfants nenfhors npers ocde10 pondmen sexecj sexepr typmen5 vag zeat ///
#		/* Activité professionnelle */ ///
#		cs42* situacj situapr ///
#		/* Logement */ ///
#		htl strate
#		*rename agpr agepr
#		drop agpr
#		rename agcj agecj
#		gen nadultes = npers - nenfants
#		foreach x in "cj" "pr" {
#			destring natio7`x', replace
#			gen natio`x' = 0
#			replace natio`x' = 1 if inlist(natio7`x',1,2)
#			replace natio`x' = 2 if inlist(natio7`x',3,4,5,6,7)
#			drop natio7`x'
#		}
#		destring couplepr, replace
#		replace couplepr = 1 if couplepr == 2
#		replace couplepr = 2 if couplepr == 3
#		replace ocde10 = ocde10 / 10
#		sort ident_men
#		save "`menages'", replace
#		use "$rawdatadir\depmen.dta", clear
#		tempfile stalog
#		keep ident_men stalog
#		rename stalog stalogint
#		gen stalog = 0
#		replace stalog = 1 if stalogint == "2"
#		replace stalog = 2 if stalogint == "1"
#		replace stalog = 3 if stalogint == "4"
#		replace stalog = 4 if stalogint == "5"
#		replace stalog = 5 if inlist(stalogint,"3","6")
#		drop stalogint
#		sort ident_men
#		save "`stalog'", replace
#		use "`menages'", clear
#		merge ident_men using "`stalog'"
#		tab _m
#		drop _m
#		gen typlog = 0
#		replace typlog = 1 if inlist(htl,"1","5")
#		replace typlog = 2 if typlog == 0
#		drop htl
#		destring typmen5, replace
#		destring situapr situacj, replace
#		destring dip14pr dip14cj, replace
#		label var agecj    "Age du conjoint au 31/12/${yearrawdata}"
#		sort ident_men
#		save "`menages'", replace
#		use "$rawdatadir\individu.dta", clear
#		tempfile individus
#		* Il y a un problème sur l'année de naissance, donc on le recalcule avec l'année de naissance et la vague d'enquête
#		gen agepr = 2005 - anais
#		replace agepr = 2006 - anais if vag == "6"
#		label var agepr "Age de la personne de référence au 31/12/${yearrawdata}"
#		keep if lienpref == "00"
#		keep ident_men etamatri agepr
#		destring etamatri, replace
#		sort ident_men
#		save "`individus'", replace
#		use "`menages'", clear
#		merge ident_men using "`individus'"
#		drop _m
#		sort ident_men
#		save "`menages'", replace
#		use "$rawdatadir\individu.dta", clear
#		drop age
#		gen age = 2005 - anais
#		replace age = 2006 - anais if vag == "6"
#		* Garder toutes les personnes du ménage qui ne sont pas la personne de référence et le conjoint
#		keep if lienpref != "00" & lienpref != "01"
#		sort ident_men ident_ind
#		gen numero = 3 if ident_men != ident_men[_n-1]
#		replace numero = numero[_n-1] + 1 if ident_men == ident_men[_n-1]
#		keep ident_men numero age
#		sum numero
#		dis `r(max)'
#		local max = `r(max)'
#		reshape wide age, i(ident_men) j(numero)
#		forvalues i = 3(1)`max' {
#			label var age`i' "Age de la `i'ème personne du ménage au 31/12/${yearrawdata}"
#		}
#		sort ident_men
#		save "`individus'", replace
#		use "`menages'", clear
#		merge ident_men using "`individus'"
#		drop _m
#		sort ident_men
#		save "`menages'", replace
#
#		use $rawdatadir\individu.dta, clear
#		keep ident_men ident_ind agfinetu lienpref
#		destring lienpref, replace
#		gen agfinetu_cj= agfinetu if lienpref==1
#		replace agfinetu=. if lienpref!=0
#		drop if lienpref>1
#		collapse (sum) agfinetu_pr = agfinetu agfinetu_cj=agfinetu_cj, by (ident_men)
#		replace agfinetu_pr=. if agfinetu_pr==0
#		replace agfinetu_cj=. if agfinetu_cj==0
#		joinby ident_men using "`menages'"
#		label var agfinetu_pr "Age de fin d'études de la PR"
#		label var agfinetu_cj "Age de fin d'études du conjoint de la PR"
#		save "$datadir\données_socio_demog.dta", replace
#
#	}
#
#	label var agepr "Age de la personne de référence au 31/12/${yearrawdata}"
#	label var agecj "Age du conjoint de la PR au 31/12/${yearrawdata}"
#	label var sexepr "Sexe de la personne de référence"
#	label var sexecj "Sexe du conjoint de la PR"
#	label var cs42pr "Catégorie socio-professionnelle de la PR"
#	label var cs42cj "Catégorie socio-professionnelle du conjoint de la PR"
#	label var ocde10 "Nombre d'unités de consommation (échelle OCDE)"
#	label var ident_men "Identifiant du ménage"
#	label var pondmen "Ponderation du ménage"
#	label var npers "Nombre total de personnes dans le ménage"
#	label var nadultes "Nombre d'adultes dans le ménage"
#	label var nenfants "Nombre d'enfants dans le ménage"
#	label var nenfhors "Nombre d'enfants vivant hors domicile"
#	label var nactifs  "Nombre d'actifs dans le ménage"
#	label var couplepr "Vie en couple de la personne de référence"
#	label define typmen5 1 "Personne seule" 2 "Famille monoparentale" 3 "Couple sans enfant" 4 "Couple avec enfants" 5 "Autre type de ménage (complexe)"
#	label values typmen5 typmen5
#	label var typmen5 "Type de ménage (5 modalités)"
#	label var etamatri "Situation matrimoniale de la personne de référence"
#	label define matripr 1 "Célibataire" 2 "Marié(e)" 3 "Veuf(ve)" 4 "Divorcé(e)"
#	label values etamatri matripr
#	label define occupation 1 "Occupe un emploi" ///
#	2 "Apprenti" ///
#	3 "Etudiant, élève, en formation"  ///
#	4 "Chômeur (inscrit ou non à l'ANPE)" ///
#	5 "Retraité, préretraité ou retiré des affaires" ///
#	6 "Au foyer"  ///
#	7 "Autre situation (handicapé)"  ///
#	8 "Militaire du contingent"
#	label values situapr occupation
#	label values situacj occupation
#	label var situapr "Situation d'activité de la personne de référence"
#	label var situacj "Situation d'activité du conjoint de la PR"
#	label define diplome 10 "Diplôme de 3ème cycle universitaire, doctorat" ///
#	12 "Diplôme d'ingénieur, grande école" ///
#	20 "Diplôme de 2nd cycle universitaire" ///
#	30 "Diplôme de 1er cycle universitaire" ///
#	31 "BTS, DUT ou équivalent" ///
#	33 "Diplôme des professions sociales et de la santé niveau Bac +2" ///
#	41 "Baccalauréat général, brevet supérieur, capacité en droit" ///
#	42 "Baccalauréat technologique" ///
#	43 "Baccalauréat professionnel" ///
#	44 "Brevet professionnel ou de technicien" ///
#	50 "CAP, BEP ou diplôme de même niveau" ///
#	60 "Brevet des collèges, BEPC" ///
#	70 "Certificat d'études primaires" ///
#	71 "Aucun diplôme"
#	label values dip14pr diplome
#	label values dip14cj diplome
#	label var dip14pr "Diplôme le plus élevé de la PR"
#	label var dip14cj "Diplôme le plus élevé du conjoint de la PR"
#	label define nationalite 1 "Français, par naissance ou naturalisation" 2 "Etranger"
#	label values natiopr nationalite
#	label values natiocj nationalite
#	label var natiopr "Nationalité de la personne de référence"
#	label var natiocj "Nationalité du conjoint de la PR"
#	label define logement 1 "Maison" 2 "Appartement"
#	label values typlog logement
#	label var typlog "Type de logement"
#	label define statutlogement 1 "Propriétaire ou copropriétaire" ///
#	2 "Accédant à la propriété (rembourse un prêt)" ///
#	3 "Locataire" ///
#	4 "Sous-locataire" ///
#	5 "Logé gratuitement"
#	label values stalog statutlogement
#	label var stalog "Statut d'occupation du logement"
#	label define viecouple 1 "Vit en couple" 2 "Ne vit pas en couple"
#	label values couplepr viecouple
#
#	/* Recodage des CSP en 12 et 8 postes à partir de classification de l'INSEE (2003, PCS niveaux 1 et 2) */
#	gen cs24pr=00
#	replace cs24pr=10 if cs42pr=="11"
#	replace cs24pr=10 if cs42pr=="12"
#	replace cs24pr=10 if cs42pr=="13"
#	replace cs24pr=21 if cs42pr=="21"
#	replace cs24pr=22 if cs42pr=="22"
#	replace cs24pr=23 if cs42pr=="23"
#	replace cs24pr=31 if cs42pr=="31"
#	replace cs24pr=32 if cs42pr=="33"
#	replace cs24pr=32 if cs42pr=="34"
#	replace cs24pr=32 if cs42pr=="35"
#	replace cs24pr=36 if cs42pr=="37"
#	replace cs24pr=36 if cs42pr=="38"
#	replace cs24pr=41 if cs42pr=="42"
#	replace cs24pr=41 if cs42pr=="43"
#	replace cs24pr=41 if cs42pr=="44"
#	replace cs24pr=41 if cs42pr=="45"
#	replace cs24pr=46 if cs42pr=="46"
#	replace cs24pr=47 if cs42pr=="47"
#	replace cs24pr=48 if cs42pr=="48"
#	replace cs24pr=51 if cs42pr=="52"
#	replace cs24pr=51 if cs42pr=="53"
#	replace cs24pr=54 if cs42pr=="54"
#	replace cs24pr=55 if cs42pr=="55"
#	replace cs24pr=56 if cs42pr=="56"
#	replace cs24pr=61 if cs42pr=="62"
#	replace cs24pr=61 if cs42pr=="63"
#	replace cs24pr=61 if cs42pr=="64"
#	replace cs24pr=61 if cs42pr=="65"
#	replace cs24pr=66 if cs42pr=="67"
#	replace cs24pr=66 if cs42pr=="68"
#	replace cs24pr=69 if cs42pr=="69"
#	replace cs24pr=71 if cs42pr=="71"
#	replace cs24pr=72 if cs42pr=="72"
#	replace cs24pr=73 if cs42pr=="74"
#	replace cs24pr=73 if cs42pr=="75"
#	replace cs24pr=76 if cs42pr=="77"
#	replace cs24pr=76 if cs42pr=="78"
#	replace cs24pr=81 if cs42pr=="81"
#	replace cs24pr=82 if cs42pr=="83"
#	replace cs24pr=82 if cs42pr=="84"
#	replace cs24pr=82 if cs42pr=="85"
#	replace cs24pr=82 if cs42pr=="86"
#	replace cs24pr=82 if cs42pr=="**"
#	replace cs24pr=82 if cs42pr=="00"
#
#
#	gen cs8pr=0
#	replace cs8pr=1 if cs24pr==10
#	replace cs8pr=2 if cs24pr==21
#	replace cs8pr=2 if cs24pr==22
#	replace cs8pr=2 if cs24pr==23
#	replace cs8pr=3 if cs24pr==31
#	replace cs8pr=3 if cs24pr==32
#	replace cs8pr=3 if cs24pr==36
#	replace cs8pr=4 if cs24pr==41
#	replace cs8pr=4 if cs24pr==46
#	replace cs8pr=4 if cs24pr==47
#	replace cs8pr=4 if cs24pr==48
#	replace cs8pr=5 if cs24pr==51
#	replace cs8pr=5 if cs24pr==54
#	replace cs8pr=5 if cs24pr==55
#	replace cs8pr=5 if cs24pr==56
#	replace cs8pr=6 if cs24pr==61
#	replace cs8pr=6 if cs24pr==66
#	replace cs8pr=6 if cs24pr==69
#	replace cs8pr=7 if cs24pr==71
#	replace cs8pr=7 if cs24pr==72
#	replace cs8pr=7 if cs24pr==73
#	replace cs8pr=7 if cs24pr==76
#	replace cs8pr=8 if cs24pr==81
#	replace cs8pr=8 if cs24pr==82
#	replace cs8pr=. if cs24pr==.
#
#	order ident_men pondmen npers nenfants nenfhors nadultes nactifs ocde typmen5 ///
#	sexepr agepr etamatri couplepr situapr dip14pr cs42pr cs24pr cs8pr natiopr ///
#	sexecj agecj situacj dip14cj cs42cj natiocj ///
#	age* typlog stalog
#	label var cs24pr "Catégorie socioprofessionnelle à 24 postes de la PR"
#	label var cs8pr "Catégorie socioprofessionnelle à 8 postes de la PR"
#	label define cs8pr 1 "Agriculteurs" 2 "Artisans commerçants chefs d'entreprise" 3 "Professions libérales et cadres" 4 "Professions intermédiaires" ///
#	5 "Employés" 6 "Ouvriers" 7 "Retraités" 8 "Inactifs"
#	label values cs8pr cs8pr
#	sort ident_men
#	save "$datadir\données_socio_demog.dta", replace
#



def build_homogeneisation_vehicule(year = None):
    """Build menage consumption by categorie fiscale dataframe """

    assert year is not None
    # Load data
    bdf_survey_collection = SurveyCollection.load(collection = 'budget_des_familles')

    if year == 2005:
        survey = bdf_survey_collection.surveys['budget_des_familles_{}'.format(year)]
        # TODO


if __name__ == '__main__':
    import sys
    import time
    logging.basicConfig(level = logging.INFO, stream = sys.stdout)
    deb = time.clock()
    year = 2005
    build_other_menage_variables(year = year)

    log.info("step 01 demo duration is {}".format(time.clock() - deb))

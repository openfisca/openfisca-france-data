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

import os
import logging
import numpy
import pandas
from ConfigParser import SafeConfigParser


from openfisca_france_data.temporary import TemporaryStore
from openfisca_survey_manager.surveys import SurveyCollection


log = logging.getLogger(__name__)
temporary_store = TemporaryStore.create(file_name = "indirect_taxation_tmp")


from openfisca_france_data import default_config_files_directory as config_files_directory


def build_depenses_homogenisees(year = None):
    """Build menage consumption by categorie fiscale dataframe """

    assert year is not None
    # Load data
    bdf_survey_collection = SurveyCollection.load(collection = 'budget_des_familles')
    survey = bdf_survey_collection.surveys['budget_des_familles_{}'.format(year)]

#
#		* CE CODE APPELLE LE TABLEAU DE PASSAGE DE LA NOMENCLATURE BDF A LA NOMENCLATURE COICOP MODIFIEE
#		tempfile nomen
#		import excel using "$paramdir\Matrice passage ${yearrawdata}-COICOP.xls", first clear
#		sort poste${yearrawdata}
#		save "`nomen'"
#

            # On utilise les matrice de passages directement plus bas


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

    if year == 1995:
        socioscm = survey.get_values(table = "socioscm")
        socioscm = socioscm.iloc(socioscm.EXDEP == 1 & socioscm.EXREV == 1, ["MENA", "PONDERD"]).copy()
        temporary_store['ponder_{}'.format(year)] = socioscm

        conso = survey.get_values(tabe = "depnom")
        conso = conso(["VALEUR", "MONTANT", "MENA", "NOMEN5"])
        conso = conso.groupby(["MENA", "NOMEN5"]).sum()
        conso.rename({
            "NOMEN5": "poste{}".format(year),
            "VALEUR": "depense".format(year),
            "MONTANT": "depense_avt_imput".format(year),
            })
        # Passage à l'euro
        conso.depense = conso.depense / 6.55957
        conso.depense_avt_imput = conso.depense_avt_imput / 6.55957
        ponder = temporary_store['ponder_{}'.format(year)]
        conso.merge(ponder) # TODO: finish
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
    if year == 2000:
        conso = survey.get_values(table = "consomen")
        conso.rename(
            columns = {
                'ident': 'ident_men',
                'pondmen': 'pondmen',
                },
            inplace = True,
            )
        for variable in ['ctotale', 'c99', 'c99999'] + \
                        ["c0{}".format(i) for i in range(1, 10)] + \
                        ["c{}".format(i) for i in range(10, 14)]:
            del conso[variable]

        #		if ${yearrawdata} == 2005 {
        #			use "$rawdatadir\c05d.dta", clear
        #			order _all, alpha
        #			*keep if _n < 100
        #			order ident pondmen, first
        #			reshape long c, i(ident) j(poste${yearrawdata}, s)
        #			rename c depense
        #			sort ident_men poste
        #		}

    if year == 2005:
        conso = survey.get_values(table = "c05d")


    if year == 2011:
        conso = survey.get_values(table = "c05")
        conso.rename(
            columns = {
                'ident_me': 'ident_men',
                },
            inplace = True,
            )

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

    # Grouping by coicop
    #
    poids = conso[['ident_men', 'pondmen']].copy()
    poids.set_index('ident_men', inplace = True)

    conso.drop('pondmen', axis = 1, inplace = True)
    conso.set_index('ident_men', inplace = True)

    matrice_passage_data_frame, selected_parametres_fiscalite_data_frame = get_transfert_data_frames(year)

    coicop_poste_bdf = matrice_passage_data_frame[['poste{}'.format(year), 'posteCOICOP']]
    coicop_poste_bdf.set_index('poste{}'.format(year), inplace = True)
    coicop_by_poste_bdf = coicop_poste_bdf.to_dict()['posteCOICOP']
    del coicop_poste_bdf

    def reformat_consumption_column_coicop(coicop):
        try:
            return int(coicop.replace('c', '').lstrip('0'))
        except:
            return numpy.NaN

    coicop_labels = [
        normalize_coicop(coicop_by_poste_bdf.get(reformat_consumption_column_coicop(poste_bdf)))
        for poste_bdf in conso.columns
        ]
    tuples = zip(coicop_labels, conso.columns)
    conso.columns = pandas.MultiIndex.from_tuples(tuples, names=['coicop', 'poste{}'.format(year)])
    coicop_data_frame = conso.groupby(level = 0, axis = 1).sum()

    depenses = coicop_data_frame.merge(poids, left_index = True, right_index = True)
    temporary_store['depenses_{}'.format(year)] = depenses

    # Création de gros postes, les 12 postes sur lesquels le calage se fera
    def select_gros_postes(coicop):
        try:
            coicop = unicode(coicop)
        except:
            coicop = coicop
        normalized_coicop = normalize_coicop(coicop)
        grosposte = normalized_coicop[0:2]
        return int(grosposte)
        
    grospostes = [
        select_gros_postes(coicop)
        for coicop in coicop_data_frame.columns
        ]
    tuples_gros_poste = zip(coicop_data_frame.columns, grospostes)
    coicop_data_frame.columns = pandas.MultiIndex.from_tuples(tuples_gros_poste, names=['coicop', 'grosposte'])

    depenses_by_grosposte = coicop_data_frame.groupby(level = 1, axis = 1).sum()
    depenses_by_grosposte = depenses_by_grosposte.merge(poids, left_index = True, right_index = True)

    temporary_store['depenses_by_grosposte_{}'.format(year)] = depenses_by_grosposte
    temporary_store.close()


def normalize_coicop(code):
    '''Normalize_coicop est function d'harmonisation de la colonne d'entiers posteCOICOP de la table
matrice_passage_data_frame en la transformant en une chaine de 5 caractères
    '''
    # TODO il faut préciser ce que veut dire harmoniser
    # Cf. Nomenclature_commune.xls
    try:
        code = unicode(code)
    except:
        code = code
    if len(code) == 3:
        normalized_code = "0" + code + "0"  # "{0}{1}{0}".format(0, code)
    elif len(code) == 4:
        if not code.startswith("0") and not code.startswith("1") and not code.startswith("45") and not code.startswith("9"):
            normalized_code = "0" + code
            # 022.. = cigarettes et tabacs => on les range avec l'alcool (021.0)
        elif code.startswith("0"):
            normalized_code = code + "0"
        elif code in ["1151", "1181", "4522", "4511"]:
            # 1151 = Margarines et autres graisses végétales
            # 1181 = Confiserie
            # 04522 = Achat de butane, propane
            # 04511 = Facture EDF GDF non dissociables
            normalized_code = "0" + code
        else:
            # 99 = loyer, impots et taxes, cadeaux...
            normalized_code = code + "0"
    elif len(code) == 5:
        normalized_code = code
    else:
        raise()
    return normalized_code


def get_transfert_data_frames(year = None):
    assert year is not None
    parser = SafeConfigParser()
    config_local_ini = os.path.join(config_files_directory, 'config_local.ini')
    config_ini = os.path.join(config_files_directory, 'config.ini')
    parser.read([config_ini, config_local_ini])
    directory_path = os.path.normpath(
        parser.get("openfisca_france_indirect_taxation", "assets")
        )
    matrice_passage_file_path = os.path.join(directory_path, "Matrice passage {}-COICOP.xls".format(year))
    parametres_fiscalite_file_path = os.path.join(directory_path, "Parametres fiscalite indirecte.xls")
    matrice_passage_data_frame = pandas.read_excel(matrice_passage_file_path)
    parametres_fiscalite_data_frame = pandas.read_excel(parametres_fiscalite_file_path, sheetname = "categoriefiscale")
    # print parametres_fiscalite_data_frame
    selected_parametres_fiscalite_data_frame = \
        parametres_fiscalite_data_frame[parametres_fiscalite_data_frame.annee == year]
    return matrice_passage_data_frame, selected_parametres_fiscalite_data_frame


if __name__ == '__main__':
    import sys
    import time
    logging.basicConfig(level = logging.INFO, stream = sys.stdout)
    deb = time.clock()
    year = 2000
    build_depenses_homogenisees(year = year)
    log.info("duration is {}".format(time.clock() - deb))

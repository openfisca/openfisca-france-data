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
#* Etape n° 0-2 : HOMOGENEISATION DES DONNEES SUR LES VEHICULES
#**************************************************************************************************************************
#**************************************************************************************************************************
#
#
#	* DONNEES SUR LES TYPES DE CARBURANTS
#
#	if ${yearrawdata} == 1995 {
#	* L'enquête BdF 1995 ne contient pas d'information sur le type de carburant utilisé par les véhicules.
#	}
#
#	if ${yearrawdata} == 2000 {
#		use "$rawdatadir\depmen.dta", clear
#		keep IDENT CARBU*
#		rename IDENT ident_men
#		rename CARBU01 carbu1
#		rename CARBU02 carbu2
#		replace carbu1 = "0" if carbu1 == ""
#		replace carbu2 = "0" if carbu2 == ""
#		reshape long carbu, i(ident) j(num_veh)
#		keep if inlist(carbu,"1","2")
#		gen veh_tot = 1
#		gen veh_essence = (carbu == "1")
#		gen veh_diesel = (carbu == "2")
#		collapse (sum) veh_tot veh_essence veh_diesel, by(ident)
#		label var veh_tot     "Nombre total de vehicules dans le ménage"
#		label var veh_essence "Nombre de vehicules à essence dans le ménage"
#		label var veh_diesel  "Nombre total de vehicules diesel dans le ménage"
#		sort ident
#		tempfile automobile
#		save "`automobile'"
#		save "$datadir\automobile.dta", replace
#
#	}
#
#	if ${yearrawdata} == 2005 {
#		use "$rawdatadir\automobile.dta", clear
#		keep ident_men carbu vag
#		keep if inlist(carbu,"1","2")
#		gen veh_tot = 1
#		gen veh_essence = (carbu == "1")
#		gen veh_diesel = (carbu == "2")
#		keep if inlist(carbu,"1","2")
#		collapse (sum) veh_tot veh_essence veh_diesel, by(ident)
#		label var veh_tot     "Nombre total de vehicules dans le ménage"
#		label var veh_essence "Nombre de vehicules à essence dans le ménage"
#		label var veh_diesel  "Nombre total de vehicules diesel dans le ménage"
#		sort ident
#		tempfile automobile
#		save "`automobile'"
#		save "$datadir\automobile.dta", replace
#	}

def build_homogeneisation_vehicules(year = None):
    """Compute vehicule numbers by type"""

    assert year is not None
    # Load data
    bdf_survey_collection = SurveyCollection.load(collection = 'budget_des_familles')
    survey = bdf_survey_collection.surveys['budget_des_familles_{}'.format(year)]

    if year == 2000:
        vehicule = survey.get_values(table = "depmen")
        kept_variables = ['ident', 'carbu01', 'carbu02']
        vehicule = vehicule[kept_variables]
        vehicule.rename(columns = {'ident': 'ident_men'}, inplace = True)
        vehicule.rename(columns = {'carbu01': 'carbu1'}, inplace = True)
        vehicule.rename(columns = {'carbu02': 'carbu2'}, inplace = True)
        vehicule["veh_tot"] = '1'
        vehicule["veh_essence"] = (vehicule['carbu1'] == '1') + (vehicule['carbu2'] == '1')
        vehicule["veh_diesel"] = (vehicule['carbu1'] == '2') + (vehicule['carbu2'] == '2')

    if year == 2005:
        vehicule = survey.get_values(table = "automobile")
        kept_variables = ['ident_men', 'carbu', 'vag']  # TODO: on ne fait rien de vag
        vehicule = vehicule[kept_variables]
        vehicule["veh_tot"] = 1
        vehicule["veh_essence"] = (vehicule['carbu'] == '1')
        vehicule["veh_diesel"] = (vehicule['carbu'] == '2')

    # Compute the number of cars by category
    vehicule = vehicule.groupby(by = 'ident_men')["veh_tot", "veh_essence", "veh_diesel"].sum()

    # Save in temporary store
    temporary_store['automobile_{}'.format(year)] = vehicule


if __name__ == '__main__':
    import sys
    import time
    logging.basicConfig(level = logging.INFO, stream = sys.stdout)
    deb = time.clock()
    year = 2005
    build_homogeneisation_vehicules(year = year)

    log.info("step 0_2_homogeneisation_vehicules duration is {}".format(time.clock() - deb))

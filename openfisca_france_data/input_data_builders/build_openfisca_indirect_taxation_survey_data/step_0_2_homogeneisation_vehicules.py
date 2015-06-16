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


from openfisca_survey_manager.survey_collections import SurveyCollection


from openfisca_france_data.temporary import temporary_store_decorator
from openfisca_france_data import default_config_files_directory as config_files_directory
from openfisca_france_data.input_data_builders.build_openfisca_indirect_taxation_survey_data.utils \
    import ident_men_dtype


log = logging.getLogger(__name__)


# **************************************************************************************************************************
# * Etape n° 0-2 : HOMOGENEISATION DES DONNEES SUR LES VEHICULES
# **************************************************************************************************************************
# **************************************************************************************************************************
#
#
# DONNEES SUR LES TYPES DE CARBURANTS


@temporary_store_decorator(config_files_directory = config_files_directory, file_name = 'indirect_taxation_tmp')
def build_homogeneisation_vehicules(temporary_store = None, year = None):
    assert temporary_store is not None
    """Compute vehicule numbers by type"""

    assert year is not None
    # Load data
    bdf_survey_collection = SurveyCollection.load(
        collection = 'budget_des_familles', config_files_directory = config_files_directory)
    survey = bdf_survey_collection.get_survey('budget_des_familles_{}'.format(year))

    if year == 1995:
        vehicule = None

    # L'enquête BdF 1995 ne contient pas d'information sur le type de carburant utilisé par les véhicules.

    if year == 2000:
        vehicule = survey.get_values(table = "depmen")
        kept_variables = ['ident', 'carbu01', 'carbu02']
        vehicule = vehicule[kept_variables]
        vehicule.rename(columns = {'ident': 'ident_men'}, inplace = True)
        vehicule.rename(columns = {'carbu01': 'carbu1'}, inplace = True)
        vehicule.rename(columns = {'carbu02': 'carbu2'}, inplace = True)
        vehicule["veh_tot"] = 1
        vehicule["veh_essence"] = 1 * (vehicule['carbu1'] == 1) + 1 * (vehicule['carbu2'] == 1)
        vehicule["veh_diesel"] = 1 * (vehicule['carbu1'] == 2) + 1 * (vehicule['carbu2'] == 2)
        vehicule.index = vehicule.index.astype(ident_men_dtype)


    if year == 2005:
        vehicule = survey.get_values(table = "automobile")
        kept_variables = ['ident_men', 'carbu']
        vehicule = vehicule[kept_variables]
        vehicule["veh_tot"] = 1
        vehicule["veh_essence"] = (vehicule['carbu'] == 1)
        vehicule["veh_diesel"] = (vehicule['carbu'] == 2)

    if year == 2011:
        try:
            vehicule = survey.get_values(table = "AUTOMOBILE")
        except:
            vehicule = survey.get_values(table = "automobile")
        kept_variables = ['ident_me', 'carbu']
        vehicule = vehicule[kept_variables]
        vehicule.rename(columns = {'ident_me': 'ident_men'}, inplace = True)
        vehicule["veh_tot"] = 1
        vehicule["veh_essence"] = (vehicule['carbu'] == 1)
        vehicule["veh_diesel"] = (vehicule['carbu'] == 2)

    # Compute the number of cars by category and save
    if year != 1995:
        vehicule = vehicule.groupby(by = 'ident_men')["veh_tot", "veh_essence", "veh_diesel"].sum()
        vehicule["pourcentage_vehicule_essence"] = 0
        vehicule.pourcentage_vehicule_essence.loc[vehicule.veh_tot != 0] = vehicule.veh_essence / vehicule.veh_tot
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

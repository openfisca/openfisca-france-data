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


import logging
import os
import pandas

from openfisca_survey_manager.surveys import Survey, SurveyCollection
from openfisca_france_data.input_data_builders.build_openfisca_indirect_taxation_survey_data.step_0_1_1_homogeneisation_donnees_depenses \
    import build_depenses_homogenisees

from openfisca_france_data.input_data_builders.build_openfisca_indirect_taxation_survey_data.step_0_1_2_imputations_loyers_proprietaires \
    import build_imputation_loyers_proprietaires

from openfisca_france_data.input_data_builders.build_openfisca_indirect_taxation_survey_data.step_0_2_homogeneisation_vehicules \
    import build_homogeneisation_vehicules

from openfisca_france_data.input_data_builders.build_openfisca_indirect_taxation_survey_data.step_0_3_homogeneisation_caracteristiques_menages \
    import build_homogeneisation_caracteristiques_sociales

from openfisca_france_data.input_data_builders.build_openfisca_indirect_taxation_survey_data.step_0_4_homogeneisation_revenus_menages \
    import build_homogeneisation_revenus_menages

from openfisca_france_data.input_data_builders.build_openfisca_indirect_taxation_survey_data.step_03_calage\
    import build_depenses_calees

from openfisca_france_data.input_data_builders.build_openfisca_indirect_taxation_survey_data.step_04_homogeneisation_categories_fiscales\
    import build_menage_consumption_by_categorie_fiscale

log = logging.getLogger(__name__)

from openfisca_france_data.temporary import TemporaryStore
temporary_store = TemporaryStore.create(file_name = "indirect_taxation_tmp")


def run_all(year = 2005, year_calage = 2007, year_data_list = [2005, 2010], filename = "test_indirect_taxation"):

    # 4 étape parallèles d'homogénéisation des données sources :

    # Gestion des dépenses de consommation:
    build_depenses_homogenisees(year = year)
    build_imputation_loyers_proprietaires(year = year)
    build_depenses_calees(year_calage, year_data_list)
    build_menage_consumption_by_categorie_fiscale(year_calage, year_data_list)
    categorie_fiscale_data_frame = temporary_store["menage_consumption_by_categorie_fiscale_{}".format(year_calage)]
    depenses_calees_by_grosposte = temporary_store["depenses_calees_by_grosposte_{}".format(year_calage)]

    # Gestion des véhicules:
    build_homogeneisation_vehicules(year = year)
    vehicule = temporary_store['automobile_{}'.format(year)]

    # Gestion des variables socio démographiques:
    build_homogeneisation_caracteristiques_sociales(year = year)
    menage = temporary_store['donnes_socio_demog_{}'.format(year)]

    # Gestion des variables revenues:
    build_homogeneisation_revenus_menages(year = year)
    revenus = temporary_store["revenus_{}".format(year)]

    # DataFrame résultant de ces 4 étapes
    data_frame = pandas.concat([revenus, vehicule, categorie_fiscale_data_frame, menage, depenses_calees_by_grosposte], axis = 1)

    data_frame.index.name = "ident_men"
    data_frame.reset_index(inplace = True)

    # Saving the data_frame
    openfisca_survey_collection = SurveyCollection(name = "openfisca_indirect_taxation")
    openfisca_survey_collection.set_config_files_directory()
    output_data_directory = openfisca_survey_collection.config.get('data', 'output_directory')
    survey_name = "openfisca_indirect_taxation_data_{}".format(year)
    table = "input"
    hdf5_file_path = os.path.join(
        os.path.dirname(output_data_directory),
        "{}.h5".format(survey_name),
        )
    survey = Survey(
        name = survey_name,
        hdf5_file_path = hdf5_file_path,
        )
    survey.insert_table(name = table)
    survey.fill_hdf(data_frame = data_frame, table = table)
    openfisca_survey_collection.surveys[survey_name] = survey
    openfisca_survey_collection.dump(collection = "openfisca_indirect_taxation")


if __name__ == '__main__':
    import time
    start = time.time()
    year = 2005
    year_calage = 2007
    year_data_list = [2005, 2010]
    run_all(year, year_calage, year_data_list)
    log.info("{}".format(time.time() - start))

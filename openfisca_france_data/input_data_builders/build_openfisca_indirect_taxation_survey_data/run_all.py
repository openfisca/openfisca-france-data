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


from __future__ import division


import logging
import os
import pandas
import numpy


from openfisca_survey_manager.survey_collections import SurveyCollection
from openfisca_survey_manager.surveys import Survey
from openfisca_france_data import default_config_files_directory as config_files_directory

from openfisca_france_data.input_data_builders.build_openfisca_indirect_taxation_survey_data.utils \
    import find_nearest_inferior

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
    import build_depenses_calees, build_revenus_cales

from openfisca_france_data.input_data_builders.build_openfisca_indirect_taxation_survey_data.step_04_homogeneisation_categories_fiscales\
    import build_menage_consumption_by_categorie_fiscale

from openfisca_france_data.temporary import TemporaryStore

from openfisca_france_data.input_data_builders.build_openfisca_indirect_taxation_survey_data.utils \
    import ident_men_dtype


log = logging.getLogger(__name__)


def run_all(year_calage = 2011, year_data_list = [1995, 2000, 2005, 2011]):

    temporary_store = TemporaryStore.create(file_name = "indirect_taxation_tmp")

    # Quelle base de données choisir pour le calage ?
    year_data = find_nearest_inferior(year_data_list, year_calage)

    # 4 étape parallèles d'homogénéisation des données sources :
    # Gestion des dépenses de consommation:
    build_depenses_homogenisees(year = year_data)
    build_imputation_loyers_proprietaires(year = year_data)

    build_depenses_calees(year_calage = year_calage, year_data = year_data)
    build_menage_consumption_by_categorie_fiscale(year_calage = year_calage, year_data = year_data)

    categorie_fiscale_data_frame = temporary_store["menage_consumption_by_categorie_fiscale_{}".format(year_calage)]
    categorie_fiscale_data_frame.index = categorie_fiscale_data_frame.index.astype(ident_men_dtype)

    temporary_store["menage_consumption_by_categorie_fiscale_{}".format(year_calage)] = categorie_fiscale_data_frame

    temporary_store["menage_consumption_by_categorie_fiscale_{}".format(year_calage)] = categorie_fiscale_data_frame

    depenses_calees_by_grosposte = temporary_store["depenses_calees_by_grosposte_{}".format(year_calage)]
    depenses_calees_by_grosposte.index = depenses_calees_by_grosposte.index.astype(ident_men_dtype)
    depenses_calees = temporary_store["depenses_calees_{}".format(year_calage)]
    depenses_calees.index = depenses_calees.index.astype(ident_men_dtype)

    # Gestion des véhicules:
    build_homogeneisation_vehicules(year = year_data)
    if year_calage != 1995:
        vehicule = temporary_store['automobile_{}'.format(year_data)]
        vehicule.index = vehicule.index.astype(ident_men_dtype)
    else:
        vehicule = None

    # Gestion des variables socio démographiques:
    build_homogeneisation_caracteristiques_sociales(year = year_data)
    menage = temporary_store['donnes_socio_demog_{}'.format(year_data)]
    menage.index = menage.index.astype(ident_men_dtype)

    # Gestion des variables revenus:
    build_homogeneisation_revenus_menages(year = year_data)
    build_revenus_cales(year_calage = year_calage, year_data = year_data)
    revenus = temporary_store["revenus_cales_{}".format(year_calage)]
    revenus.index = revenus.index.astype(ident_men_dtype)

    temporary_store.close()

    # Concaténation des résults de ces 4 étapes

    preprocessed_data_frame_by_name = dict(
        revenus = revenus,
        vehicule = vehicule,
        categorie_fiscale_data_frame = categorie_fiscale_data_frame,
        menage = menage,
        depenses_calees = depenses_calees,
        depenses_calees_by_grosposte = depenses_calees_by_grosposte
        )

    for name, preprocessed_data_frame in preprocessed_data_frame_by_name.iteritems():
        assert preprocessed_data_frame.index.name == 'ident_men', \
            'Index is not labelled ident_men in data frame {}'.format(name)
        assert len(preprocessed_data_frame) != 0, 'Empty data frame {}'.format(name)
        print '-----'
        print name,
        print 'size: ', len(preprocessed_data_frame)
        print 'dtype :', preprocessed_data_frame.index.dtype,
        print 'nan_containing_variables: ', preprocessed_data_frame.isnull().any()[preprocessed_data_frame.isnull().any()].index

        assert preprocessed_data_frame.index.dtype == numpy.dtype('O'), "index for {} is {}".format(
            name, preprocessed_data_frame.index.dtype)

    data_frame = pandas.concat(
        [revenus, vehicule, categorie_fiscale_data_frame, menage, depenses_calees, depenses_calees_by_grosposte],
        axis = 1,
        )

    nan_containing_variables = list(data_frame.isnull().any()[data_frame.isnull().any()].index)
    nan_containing_variables_by_name = dict(
        (name, list(set(nan_containing_variables).intersection(set(preprocessed_data_frame.columns))))
        for name, preprocessed_data_frame in preprocessed_data_frame_by_name.iteritems()
        )
    import pprint

    pprint.pprint(nan_containing_variables_by_name)

    if year_data == 2005:
        for vehicule_variable in ['veh_tot', 'veh_essence', 'veh_diesel', 'pourcentage_vehicule_essence']:
            data_frame.loc[data_frame[vehicule_variable].isnull(), vehicule_variable] = 0
        for variable in ['age{}'.format(i) for i in range(3, 14)] + ['agecj', 'agfinetu', 'agfinetu_cj', 'nenfhors']:
            data_frame.loc[data_frame[variable].isnull(), variable] = 0
    if year_data == 2011:
        for var in ['veh_tot', 'veh_essence', 'veh_diesel', 'pourcentage_vehicule_essence', 'rev_disp_loyerimput',
                    'rev_disponible', 'ratio_loyer_impute', 'loyer_impute', 'ratio_revenus']:
            data_frame.loc[data_frame[var].isnull(), var] = 0

    data_frame.index.name = "ident_men"
    # TODO: Homogénéiser: soit faire en sorte que ident_men existe pour toutes les années
    # soit qu'elle soit en index pour toutes
    try:
        data_frame.reset_index(inplace = True)
    except ValueError, e:
        print "ignoring reset_index because \n" + str(e)

    # Remove duplicated colums causing bug with HDFStore
    # according to https://github.com/pydata/pandas/issues/6240
    # using solution form stackoverflow
    # http://stackoverflow.com/questions/16938441/how-to-remove-duplicate-columns-from-a-dataframe-using-python-pandas
    data_frame = data_frame.T.groupby(level = 0).first().T

    log.info('Saving the openfisca indirect taxation input dataframe')
    try:
        openfisca_survey_collection = SurveyCollection.load(
            collection = 'openfisca_indirect_taxation', config_files_directory = config_files_directory)
    except:
        openfisca_survey_collection = SurveyCollection(
            name = 'openfisca_indirect_taxation', config_files_directory = config_files_directory)

    output_data_directory = openfisca_survey_collection.config.get('data', 'output_directory')
    survey_name = "openfisca_indirect_taxation_data_{}".format(year_calage)
    table = "input"
    hdf5_file_path = os.path.join(output_data_directory, "{}.h5".format(survey_name))
    survey = Survey(
        name = survey_name,
        hdf5_file_path = hdf5_file_path,
        )
    survey.insert_table(name = table, data_frame = data_frame)
    openfisca_survey_collection.surveys.append(survey)
    openfisca_survey_collection.dump()


def run(years_calage):
    import time
    year_data_list = [1995, 2000, 2005, 2011]
    for year_calage in years_calage:
        start = time.time()
        run_all(year_calage, year_data_list)
        log.info("Finished {}".format(time.time() - start))
        print "Base construite pour l'année {} à partir de l'enquête bdf {}".format(
            year_calage, find_nearest_inferior(year_data_list, year_calage)
            )

if __name__ == '__main__':
    import sys
    logging.basicConfig(level = logging.INFO, stream = sys.stdout)
    years_calage = [2000, 2005, 2011]
    run(years_calage)

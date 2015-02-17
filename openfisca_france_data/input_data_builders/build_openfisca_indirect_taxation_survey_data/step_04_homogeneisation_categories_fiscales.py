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
import pandas
from ConfigParser import SafeConfigParser

from openfisca_france_data import default_config_files_directory as config_files_directory
from openfisca_france_data.temporary import TemporaryStore

from openfisca_france_data.input_data_builders.build_openfisca_indirect_taxation_survey_data.step_0_1_1_homogeneisation_donnees_depenses \
    import normalize_coicop


log = logging.getLogger(__name__)


temporary_store = TemporaryStore.create(file_name = "indirect_taxation_tmp")


def build_menage_consumption_by_categorie_fiscale(year_data = None, year_calage = None):
    """Build menage consumption by categorie fiscale dataframe """

    assert year_calage is not None
    assert year_data is not None

    # Load matrices de passage
    matrice_passage_data_frame, selected_parametres_fiscalite_data_frame = \
        get_transfert_data_frames(year_data)

    # Load data
    coicop_data_frame = temporary_store.extract('depenses_calees_{}'.format(year_calage))

    # Grouping by categorie_fiscale
    selected_parametres_fiscalite_data_frame = \
        selected_parametres_fiscalite_data_frame[['posteCOICOP', 'categoriefiscale']]
    # print selected_parametres_fiscalite_data_frame
    selected_parametres_fiscalite_data_frame.set_index('posteCOICOP', inplace = True)

    # Normalisation des coicop de la feuille excel pour être cohérent avec depenses_calees
    normalized_coicop = [
        normalize_coicop(coicop)
        for coicop in selected_parametres_fiscalite_data_frame.index
        ]
    selected_parametres_fiscalite_data_frame.index = normalized_coicop
    categorie_fiscale_by_coicop = selected_parametres_fiscalite_data_frame.to_dict()['categoriefiscale']

    # print categorie_fiscale_by_coicop
    categorie_fiscale_labels = [
        categorie_fiscale_by_coicop.get(coicop)
        for coicop in coicop_data_frame.columns
        ]
<<<<<<< HEAD
    # print categorie_fiscale_labels
=======
    #TODO: gérer les catégorie fiscales "None" = dépenses énergétiques (4) & tabac (2)
#    print categorie_fiscale_labels
>>>>>>> Apply normalization to categories fiscales
    tuples = zip(categorie_fiscale_labels, coicop_data_frame.columns)
    coicop_data_frame.columns = pandas.MultiIndex.from_tuples(tuples, names=['categoriefiscale', 'coicop'])
    # print coicop_data_frame.columns

    categorie_fiscale_data_frame = coicop_data_frame.groupby(level = 0, axis = 1).sum()
    rename_columns = dict(
        [(number, "categorie_fiscale_{}".format(number)) for number in categorie_fiscale_data_frame.columns]
        )
    categorie_fiscale_data_frame.rename(
        columns = rename_columns,
        inplace = True,
        )
    categorie_fiscale_data_frame['role_menage'] = 0
    temporary_store["menage_consumption_by_categorie_fiscale"] = categorie_fiscale_data_frame
    categorie_fiscale_data_frame.reset_index(inplace = True)

    return categorie_fiscale_data_frame


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
    year_data = 2005
    year_calage = 2007
    build_menage_consumption_by_categorie_fiscale(year_data, year_calage)
    log.info("step 01 demo duration is {}".format(time.clock() - deb))

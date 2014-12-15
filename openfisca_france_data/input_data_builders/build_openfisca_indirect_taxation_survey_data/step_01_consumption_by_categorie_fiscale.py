#! /usr/bin/env python
# -*- coding: utf-8 -*-


# OpenFisca -- A versatile microsimulation software
# By: OpenFisca Team <contact@openfisca.fr>
#
# Copyright (C) 2011, 2012, 2013, 2014 OpenFisca Team
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
import pkg_resources

import pandas as pd
from pandas import read_excel


from openfisca_survey_manager.surveys import SurveyCollection

log = logging.getLogger(__name__)

from openfisca_france_data.temporary import TemporaryStore

temporary_store = TemporaryStore.create(file_name = "indirect_taxation_tmp")

from ConfigParser import SafeConfigParser


def build_menage_consumption_by_categorie_fiscale(year = None):
    """Build menage consumption by categorie fiscale dataframe """
    matrice_passage_data_frame, selected_parametres_fiscalite_data_frame = \
        get_transfert_data_frames(year)

    assert year is not None
    # Load data
    bdf_survey_collection = SurveyCollection.load(collection = 'budget_des_familles')
    survey = bdf_survey_collection.surveys['budget_des_familles_{}'.format(year)]

    c05d = survey.get_values(table = "c05d")
    c05d.drop('pondmen', axis = 1, inplace = True)
    c05d.set_index('ident_men', inplace = True)

    del bdf_survey_collection, survey

    # Grouping by coicop
    coicop_poste_bdf = matrice_passage_data_frame[['poste{}'.format(year), 'posteCOICOP']]
    coicop_poste_bdf.set_index('poste{}'.format(year), inplace = True)
    coicop_by_poste_bdf = coicop_poste_bdf.to_dict()['posteCOICOP']
    del coicop_poste_bdf

    def reformat_consumption_column_coicop(coicop):
        try:
            return int(coicop.replace('c', '').lstrip('0'))
        except:
            return None

    coicop_labels = [
        coicop_by_poste_bdf.get(reformat_consumption_column_coicop(poste_bdf))
        for poste_bdf in c05d.columns
        ]
    tuples = zip(coicop_labels, c05d.columns)
    c05d.columns = pd.MultiIndex.from_tuples(tuples, names=['coicop', 'poste{}'.format(year)])

    coicop_data_frame = c05d.groupby(level = 0, axis = 1).sum()
    # print coicop_data_frame

    # Grouping by categorie_fiscale
    selected_parametres_fiscalite_data_frame = \
        selected_parametres_fiscalite_data_frame[['posteCOICOP', 'categoriefiscale']]
    # print selected_parametres_fiscalite_data_frame
    selected_parametres_fiscalite_data_frame.set_index('posteCOICOP', inplace = True)
    categorie_fiscale_by_coicop = selected_parametres_fiscalite_data_frame.to_dict()['categoriefiscale']
    # print categorie_fiscale_by_coicop
    categorie_fiscale_labels = [
        categorie_fiscale_by_coicop.get(coicop)
        for coicop in coicop_data_frame.columns
        ]
    # print categorie_fiscale_labels
    tuples = zip(categorie_fiscale_labels, coicop_data_frame.columns)
    coicop_data_frame.columns = pd.MultiIndex.from_tuples(tuples, names=['categoriefiscale', 'coicop'])
    # print coicop_data_frame

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
    openfisca_france_data_location = pkg_resources.get_distribution('openfisca-france-data').location
    config_files_directory = os.path.join(openfisca_france_data_location)
    config_local_ini = os.path.join(config_files_directory, 'config_local.ini')
    config_ini = os.path.join(config_files_directory, 'config.ini')
    parser.read([config_ini, config_local_ini])
    directory_path  = os.path.normpath(
        parser.get("openfisca_france_indirect_taxation", "assets")
        )
    matrice_passage_file_path = os.path.join(directory_path, "Matrice passage {}-COICOP.xls".format(year))
    parametres_fiscalite_file_path = os.path.join(directory_path, "Parametres fiscalite indirecte.xls")
    matrice_passage_data_frame = read_excel(matrice_passage_file_path)
    parametres_fiscalite_data_frame = read_excel(parametres_fiscalite_file_path, sheetname = "categoriefiscale")
    # print parametres_fiscalite_data_frame
    selected_parametres_fiscalite_data_frame = \
        parametres_fiscalite_data_frame[parametres_fiscalite_data_frame.annee == year]
    return matrice_passage_data_frame, selected_parametres_fiscalite_data_frame


if __name__ == '__main__':
    import sys
    import time
    logging.basicConfig(level = logging.INFO, stream = sys.stdout)
    deb = time.clock()
    year = 2005
    build_menage_consumption_by_categorie_fiscale(year = year)

    log.info("step 01 demo duration is {}".format(time.clock() - deb))

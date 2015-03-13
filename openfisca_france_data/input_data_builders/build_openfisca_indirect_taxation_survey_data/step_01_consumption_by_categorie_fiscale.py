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
from openfisca_survey_manager.survey_collections import SurveyCollection


log = logging.getLogger(__name__)


temporary_store = TemporaryStore.create(file_name = "indirect_taxation_tmp")


def build_menage_consumption_by_categorie_fiscale(year = None):
    """Build menage consumption by categorie fiscale dataframe """
    matrice_passage_data_frame, selected_parametres_fiscalite_data_frame = \
        get_transfert_data_frames(year)

    assert year is not None
    # Load data
    bdf_survey_collection = SurveyCollection.load(collection = 'budget_des_familles')
    survey = bdf_survey_collection.get_survey('budget_des_familles_{}'.format(year))

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
    c05d.columns = pandas.MultiIndex.from_tuples(tuples, names=['coicop', 'poste{}'.format(year)])

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
    coicop_data_frame.columns = pandas.MultiIndex.from_tuples(tuples, names=['categoriefiscale', 'coicop'])
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


def normalize_coicop(code):
    '''Normalize_coicop est function d'harmonisation de la colonne d'entiers posteCOICOP de la table
matrice_passage_data_frame en la transformant en une chaine de 5 caractères
    '''
    # TODO il faut préciser ce que veut dire harmoniser
    if len(code) == 3:
        normalized_code = "0" + code + "0"  # "{0}{1}{0}".format(0, code)
    elif len(code) == 4:
        if not code.startswith("1") and not code.startswith("9"):
            normalized_code = "0" + code
        elif code in ["1151", "1181"]:
            normalized_code = "0" + code
        else:
            normalized_code = code + "0"
    elif len(code) == 5:
        normalized_code = code
    else:
        raise()
    return normalized_code


def normalize_coicop_cn(code):
    '''Normalize_coicop_cn permet de récupérer pour chaque poste COICOP sa nomenclature dans la CN
    '''
    if code.startswith("01"):
        normalized_code_cn = 1
    elif code.startswith("02"):
        normalized_code_cn = 2
    elif code.startswith("03"):
        normalized_code_cn = 3
    elif code.startswith("04"):
        normalized_code_cn = 4
    elif code.startswith("05"):
        normalized_code_cn = 5
    elif code.startswith("06"):
        normalized_code_cn = 6
    elif code.startswith("07"):
        if not code.startswith("073"):
            normalized_code_cn = 7
        else:
            normalized_code_cn = 8
    elif code.startswith("08"):
        normalized_code_cn = 8
    elif code.startswith("09"):
        normalized_code_cn = 9
    elif code.startswith("10"):
        normalized_code_cn = 9
    elif code.startswith("11"):
        normalized_code_cn = 10
    elif code.startswith("12"):
        normalized_code_cn = 11
    elif code.startswith("99"):
        normalized_code_cn = 12

    return normalized_code_cn

#x = matrice_passage_data_frame.posteCOICOP.astype('str')
#y = x.apply(normalize_coicop)
#z = y.apply(normalize_coicop_cn)


if __name__ == '__main__':
    import sys
    import time
    logging.basicConfig(level = logging.INFO, stream = sys.stdout)
    deb = time.clock()
    year = 2005
    build_menage_consumption_by_categorie_fiscale(year = year)

    log.info("step 01 demo duration is {}".format(time.clock() - deb))

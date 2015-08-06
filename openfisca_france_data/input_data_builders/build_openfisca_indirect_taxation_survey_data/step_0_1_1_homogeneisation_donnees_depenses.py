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


from __future__ import division


import os
import logging
import numpy
import pandas
from ConfigParser import SafeConfigParser


from openfisca_france_data.temporary import temporary_store_decorator
from openfisca_france_data import default_config_files_directory as config_files_directory
from openfisca_survey_manager.survey_collections import SurveyCollection


log = logging.getLogger(__name__)


@temporary_store_decorator(config_files_directory = config_files_directory, file_name = 'indirect_taxation_tmp')
def build_depenses_homogenisees(temporary_store = None, year = None):
    """Build menage consumption by categorie fiscale dataframe """
    assert temporary_store is not None
    assert year is not None

    bdf_survey_collection = SurveyCollection.load(
        collection = 'budget_des_familles', config_files_directory = config_files_directory
        )
    survey = bdf_survey_collection.get_survey('budget_des_familles_{}'.format(year))

    # HOMOGENEISATION DES BASES DE DONNEES DE DEPENSES

    if year == 1995:
        socioscm = survey.get_values(table = "socioscm")
        poids = socioscm[['mena', 'ponderrd', 'exdep', 'exrev']]
        # cette étape de ne garder que les données dont on est sûr de la qualité et de la véracité
        # exdep = 1 si les données sont bien remplies pour les dépenses du ménage
        # exrev = 1 si les données sont bien remplies pour les revenus du ménage
        poids = poids[(poids.exdep == 1) & (poids.exrev == 1)]
        del poids['exdep'], poids['exrev']
        poids.rename(
            columns = {
                'mena': 'ident_men',
                'ponderrd': 'pondmen',
                },
            inplace = True
            )
        poids.set_index('ident_men', inplace = True)

        conso = survey.get_values(table = "depnom")
        conso = conso[["valeur", "montant", "mena", "nomen5"]]
        conso = conso.groupby(["mena", "nomen5"]).sum()
        conso = conso.reset_index()
        conso.rename(
            columns = {
                'mena': 'ident_men',
                'nomen5': 'poste{}'.format(year),
                'valeur': 'depense',
                'montant': 'depense_avt_imput',
                },
            inplace = True
            )

        # Passage à l'euro
        conso.depense = conso.depense / 6.55957
        conso.depense_avt_imput = conso.depense_avt_imput / 6.55957
        conso_small = conso[[u'ident_men', u'poste1995', u'depense']]

        conso_unstacked = conso_small.set_index(['ident_men', 'poste1995']).unstack('poste1995')
        conso_unstacked = conso_unstacked.fillna(0)

        levels = conso_unstacked.columns.levels[1]
        labels = conso_unstacked.columns.labels[1]
        conso_unstacked.columns = levels[labels]
        conso_unstacked.rename(index = {0: 'ident_men'}, inplace = True)
        conso = conso_unstacked.merge(poids, left_index = True, right_index = True)
        conso = conso.reset_index()

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

    if year == 2005:
        print survey
        conso = survey.get_values(table = "c05d")

    if year == 2011:
        try:
            conso = survey.get_values(table = "C05")
        except:
            conso = survey.get_values(table = "c05")
        conso.rename(
            columns = {
                'ident_me': 'ident_men',
                },
            inplace = True,
            )
        del conso['ctot']

    # Grouping by coicop

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
    # cette étape permet d'harmoniser les df pour 1995 qui ne se présentent pas de la même façon que pour les trois autres années
    if year == 1995:
        coicop_labels = [
            normalize_coicop(coicop_by_poste_bdf.get(poste_bdf))
            for poste_bdf in conso.columns
            ]
    else:
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


def normalize_coicop(code):
    '''Normalize_coicop est function d'harmonisation de la colonne d'entiers posteCOICOP de la table
matrice_passage_data_frame en la transformant en une chaine de 5 caractères afin de pouvoir par la suite agréger les postes
COICOP selon les 12 postes agrégés de la nomenclature de la comptabilité nationale. Chaque poste contient 5 caractères,
les deux premiers (entre 01 et 12) correspondent à ces postes agrégés de la CN.

    '''
    # TODO: vérifier la formule !!!

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
        elif code in ["1151", "1181", "4552", "4522", "4511", "9122", "9151", "9211", "9341", "1411"]:
            # 1151 = Margarines et autres graisses végétales
            # 1181 = Confiserie
            # 04522 = Achat de butane, propane
            # 04511 = Facture EDF GDF non dissociables
            normalized_code = "0" + code
        else:
            # 99 = loyer, impots et taxes, cadeaux...
            normalized_code = code + "0"
    elif len(code) == 5:
        if not code.startswith("13") and not code.startswith("44") and not code.startswith("51"):
            normalized_code = code
        else:
            normalized_code = "99000"
    else:
        print "Problematic code {}".format(code)
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
    # TODO: faire un fichier équivalent pour 2010
    matrice_passage_file_path = os.path.join(directory_path, "Matrice passage {}-COICOP.xls".format(year))
    parametres_fiscalite_file_path = os.path.join(directory_path, "Parametres fiscalite indirecte.xls")
    matrice_passage_data_frame = pandas.read_excel(matrice_passage_file_path)
    if year == 2011:
        matrice_passage_data_frame['poste2011'] = matrice_passage_data_frame['poste2011'].apply(lambda x: int(x.replace('c', '').lstrip('0')))
    parametres_fiscalite_data_frame = pandas.read_excel(parametres_fiscalite_file_path, sheetname = "categoriefiscale")
    selected_parametres_fiscalite_data_frame = \
        parametres_fiscalite_data_frame[parametres_fiscalite_data_frame.annee == year]
    return matrice_passage_data_frame, selected_parametres_fiscalite_data_frame


if __name__ == '__main__':
    import sys
    import time
    logging.basicConfig(level = logging.INFO, stream = sys.stdout)
    deb = time.clock()
    year = 2011
    build_depenses_homogenisees(year = year)
    log.info("duration is {}".format(time.clock() - deb))

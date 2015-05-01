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

from ConfigParser import SafeConfigParser

import pandas

log = logging.getLogger(__name__)

from openfisca_france_data import default_config_files_directory as config_files_directory
from openfisca_france_data.input_data_builders.build_openfisca_indirect_taxation_survey_data.step_0_1_1_homogeneisation_donnees_depenses \
    import normalize_coicop

from openfisca_france_data.temporary import TemporaryStore
temporary_store = TemporaryStore.create(file_name = "indirect_taxation_tmp")


def calage_viellissement_depenses(year_data, year_calage, depenses, masses):
    depenses_calees = pandas.DataFrame()
    coicop_list = set(depenses.columns)
    # print coicop_list
    coicop_list.remove('pondmen')
    for column in coicop_list:
        coicop = normalize_coicop(column)
        grosposte = int(coicop[0:2])
#        print column, coicop, grosposte
# RAPPEL : 12 postes CN et COICOP
#    01 Produits alimentaires et boissons non alcoolisées
#    02 Boissons alcoolisées et tabac
#    03 Articles d'habillement et chaussures
#    04 Logement, eau, gaz, électricité et autres combustibles
#    05 Meubles, articles de ménage et entretien courant de l'habitation
#    06 Santé
#    07 Transports
#    08 Communication
#    09 Loisir et culture
#    10 Education
#    11 Hotels, cafés, restaurants
#    12 Biens et services divers
        if grosposte != 99:
           # print 'grosposte: ', grosposte
           # print masses
            ratio_bdf_cn = masses.at[grosposte, 'ratio_bdf{}_cn{}'.format(year_data, year_data)]
            ratio_cn_cn = masses.at[grosposte, 'ratio_cn{}_cn{}'.format(year_data, year_calage)]
            depenses_calees[column] = depenses[column] * ratio_bdf_cn * ratio_cn_cn
#            print 'Pour le grosposte {}, le ratio de calage de la base bdf {} sur la cn est {}, le ratio de calage sur la cn pour l\'annee {} est {}'.format(grosposte, year_data, ratio_bdf_cn, year_calage,ratio_cn_cn)
    return depenses_calees


def calcul_ratios_calage(year_data, year_calage, data_bdf, data_cn):
    '''
    Fonction qui calcule les ratios de calage (bdf sur cn pour année de données) et de vieillissement
    à partir des masses de comptabilité nationale et des masses de consommation de bdf.
    '''
    masses = data_cn.merge(
        data_bdf, left_index = True, right_index = True
        )
    masses.rename(columns = {0: 'conso_bdf{}'.format(year_data)}, inplace = True)
    if year_calage != year_data:
        masses['ratio_cn{}_cn{}'.format(year_data, year_calage)] = (
            masses['consoCN_COICOP_{}'.format(year_calage)] / masses['consoCN_COICOP_{}'.format(year_data)]
            )
    if year_calage == year_data:
        masses['ratio_cn{}_cn{}'.format(year_data, year_calage)] = 1

    masses['ratio_bdf{}_cn{}'.format(year_data, year_data)] = (
        1000000 * masses['consoCN_COICOP_{}'.format(year_data)] / masses['conso_bdf{}'.format(year_data)]
        )
    return masses


def get_bdf_data_frames(year_data):
    '''
    Fonction qui récupère les dépenses de budget des familles
    et les agrège par poste (en tenant compte des poids respectifs des ménages)
    '''
    depenses_by_grosposte = temporary_store.extract('depenses_by_grosposte_{}'.format(year_data))
    grospostes_list = set(depenses_by_grosposte.columns)
    grospostes_list.remove('pondmen')

    dict_bdf_weighted_sum_by_grosposte = {}
    for grosposte in grospostes_list:
        depenses_by_grosposte['{}pond'.format(grosposte)] = (
            depenses_by_grosposte[grosposte] * depenses_by_grosposte['pondmen']
            )
        dict_bdf_weighted_sum_by_grosposte[grosposte] = depenses_by_grosposte['{}pond'.format(grosposte)].sum()
    df_bdf_weighted_sum_by_grosposte = pandas.DataFrame(
        pandas.Series(
            data = dict_bdf_weighted_sum_by_grosposte,
            index = dict_bdf_weighted_sum_by_grosposte.keys()
            )
        )
    return df_bdf_weighted_sum_by_grosposte


def get_cn_data_frames(year_data = None, year_calage = None):
    assert year_data is not None
    if year_calage is None:
        year_calage = year_data

    parser = SafeConfigParser()
    config_local_ini = os.path.join(config_files_directory, 'config_local.ini')
    config_ini = os.path.join(config_files_directory, 'config.ini')
    parser.read([config_ini, config_local_ini])

    directory_path = os.path.normpath(
        parser.get("openfisca_france_indirect_taxation", "assets")
        )

    parametres_fiscalite_file_path = os.path.join(directory_path, "Parametres fiscalite indirecte.xls")
    masses_cn_data_frame = pandas.read_excel(parametres_fiscalite_file_path, sheetname = "consommation_CN")
    if year_data != year_calage:
        masses_cn_12postes_data_frame = masses_cn_data_frame[['Code', year_data, year_calage]]
    else:
        masses_cn_12postes_data_frame = masses_cn_data_frame[['Code', year_data]]
    masses_cn_12postes_data_frame['code_unicode'] = masses_cn_12postes_data_frame.Code.astype(unicode)
    masses_cn_12postes_data_frame['len_code'] = masses_cn_12postes_data_frame['code_unicode'].apply(lambda x: len(x))

#    On ne garde que les 12 postes sur lesquels on cale:
    masses_cn_12postes_data_frame = masses_cn_12postes_data_frame[masses_cn_12postes_data_frame['len_code'] == 6]
    masses_cn_12postes_data_frame['code'] = masses_cn_12postes_data_frame.Code.astype(int)
    masses_cn_12postes_data_frame = masses_cn_12postes_data_frame.drop(['len_code', 'code_unicode', 'Code'], 1)
    if year_calage != year_data:
        masses_cn_12postes_data_frame.rename(
            columns = {
                year_data: 'consoCN_COICOP_{}'.format(year_data),
                year_calage: 'consoCN_COICOP_{}'.format(year_calage),
                'code': 'poste'
                },
            inplace = True,
            )
    else:
        masses_cn_12postes_data_frame.rename(
            columns = {
                year_data: 'consoCN_COICOP_{}'.format(year_data),
                'code': 'poste'
                },
            inplace = True,
            )
    masses_cn_12postes_data_frame.set_index('poste', inplace = True)
    return masses_cn_12postes_data_frame

def build_depenses_calees(year_calage, year_data):

    # Masses de calage provenant de la comptabilité nationale
    masses_cn_12postes_data_frame = get_cn_data_frames(year_data = year_data, year_calage = year_calage)
    # Enquête agrégée au niveau des gros postes de COICOP (12)
    df_bdf_weighted_sum_by_grosposte = get_bdf_data_frames(year_data)

    # Calcul des ratios de calage :
    masses = calcul_ratios_calage(
        year_data,
        year_calage,
        data_bdf = df_bdf_weighted_sum_by_grosposte,
        data_cn = masses_cn_12postes_data_frame
        )

    # Application des ratios de calage
    depenses = temporary_store['depenses_bdf_{}'.format(year_data)]
    depenses_calees = calage_viellissement_depenses(year_data, year_calage, depenses, masses)
    temporary_store['depenses_calees_{}'.format(year_calage)] = depenses_calees

    ###
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
        for coicop in depenses_calees.columns
        ]
    tuples_gros_poste = zip(depenses_calees.columns, grospostes)
    depenses_calees.columns = pandas.MultiIndex.from_tuples(tuples_gros_poste, names=['coicop', 'grosposte'])

    depenses_calees_by_grosposte = depenses_calees.groupby(level = 1, axis = 1).sum()

    column_groposte = [
        'coicop12_{}'.format(column)
        for column in depenses_calees_by_grosposte.columns
        ]
    depenses_calees_by_grosposte.columns = column_groposte

    # Sauvegarde de la base en coicop agrégée calée
    temporary_store['depenses_calees_by_grosposte_{}'.format(year_calage)] = depenses_calees_by_grosposte


def build_revenus_cales(year_calage, year_data):


    # Masses de calage provenant de la comptabilité nationale
    parser = SafeConfigParser()
    config_local_ini = os.path.join(config_files_directory, 'config_local.ini')
    config_ini = os.path.join(config_files_directory, 'config.ini')
    parser.read([config_ini, config_local_ini])

    directory_path = os.path.normpath(
        parser.get("openfisca_france_indirect_taxation", "assets")
        )

    parametres_fiscalite_file_path = os.path.join(directory_path, "Parametres fiscalite indirecte.xls")
    masses_cn_revenus_data_frame = pandas.read_excel(parametres_fiscalite_file_path, sheetname = "revenus_CN")

# ne pas oublier d'enlever l'accent à "loyers imputés" dans le document excel Parametres fiscalité indirecte

    masses_cn_revenus_data_frame.rename(
            columns = {
                'annee': 'year',
                'Revenu disponible brut': 'rev_disponible_cn',
                'Loyers imputes': 'loyer_imput_cn'
                },
            inplace = True
            )

    masses_cn_revenus_data_frame = masses_cn_revenus_data_frame[masses_cn_revenus_data_frame.year == year_calage]

    revenus = temporary_store['revenus_{}'.format(year_data)]


    weighted_sum_revenus = (revenus.pondmen * revenus.rev_disponible).sum()

    revenus.rev_disp_loyerimput = revenus.loyer_impute.astype(float)
    weighted_sum_loyer_impute = (revenus.pondmen * revenus.loyer_impute).sum()

    rev_disponible_cn = masses_cn_revenus_data_frame.rev_disponible_cn.sum()
    loyer_imput_cn = masses_cn_revenus_data_frame.loyer_imput_cn.sum()

    revenus_cales = revenus

    # Calcul des ratios de calage :
    revenus_cales['ratio_revenus'] = (rev_disponible_cn * 1000000 - loyer_imput_cn * 1000000)/ weighted_sum_revenus
    revenus_cales['ratio_loyer_impute'] = loyer_imput_cn * 1000000 / weighted_sum_loyer_impute


    # Application des ratios de calage
    revenus_cales.rev_disponible = revenus.rev_disponible * revenus_cales['ratio_revenus']
    revenus_cales.loyer_impute = revenus_cales.loyer_impute * revenus_cales['ratio_loyer_impute']
    revenus_cales.rev_disp_loyerimput = revenus_cales.rev_disponible + revenus_cales.loyer_impute

    temporary_store['revenus_cales_{}'.format(year_calage)] = revenus_cales



# Vérification des résultats du calage :
#    La différence du nombre de colonne vient du fait que l'on ne garde pas
#    les postes 99... qui sont des dépenses en impôts, taxes, loyers...


if __name__ == '__main__':
    import sys
    import time
    logging.basicConfig(level = logging.INFO, stream = sys.stdout)
    deb = time.clock()
    year_calage = 2000
    year_data = 2000

    build_depenses_calees(year_calage, year_data)
    build_revenus_cales(year_calage, year_data)

    log.info("step 03 calage duration is {}".format(time.clock() - deb))

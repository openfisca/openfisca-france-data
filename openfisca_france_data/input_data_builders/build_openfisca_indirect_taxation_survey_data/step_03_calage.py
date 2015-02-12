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

import numpy as np
import pandas as pd
from pandas import merge

log = logging.getLogger(__name__)

from openfisca_france_data import default_config_files_directory as config_files_directory

from openfisca_france_data.temporary import TemporaryStore
temporary_store = TemporaryStore.create(file_name = "indirect_taxation_tmp")


def get_cn_data_frames(year = None, year_calage = None):
    assert year is not None
    if year_calage is None:
        year_calage = year
    
    parser = SafeConfigParser()
    config_local_ini = os.path.join(config_files_directory, 'config_local.ini')
    config_ini = os.path.join(config_files_directory, 'config.ini')
    parser.read([config_ini, config_local_ini])

    directory_path = os.path.normpath(
        parser.get("openfisca_france_indirect_taxation", "assets")
        )

    parametres_fiscalite_file_path = os.path.join(directory_path, "Parametres fiscalite indirecte.xls")
    masses_cn_data_frame = pd.read_excel(parametres_fiscalite_file_path, sheetname = "consommation_CN")
    masses_cn_12postes_data_frame = masses_cn_data_frame[['Code', year, year_calage]]
    masses_cn_12postes_data_frame['code_unicode'] = masses_cn_12postes_data_frame.Code.astype(unicode)
    masses_cn_12postes_data_frame['len_code'] = masses_cn_12postes_data_frame['code_unicode'].apply(lambda x: len(x))

#    On ne garde que les 12 postes sur lesquels on cale:
    masses_cn_12postes_data_frame = masses_cn_12postes_data_frame[masses_cn_12postes_data_frame['len_code'] == 6]
    masses_cn_12postes_data_frame['code'] = masses_cn_12postes_data_frame.Code.astype(int)
    masses_cn_12postes_data_frame = masses_cn_12postes_data_frame.drop(['len_code', 'code_unicode','Code'], 1)

    if year_calage != year:
        masses_cn_12postes_data_frame.rename(
            columns = {
                year: 'consoCN_COICOP_{}'.format(year),
                year_calage: 'consoCN_COICOP_{}'.format(year_calage),
                'code': 'poste'
                },
            inplace = True,
            )
    else:
        masses_cn_12postes_data_frame.rename(
            columns = {
                year: 'consoCN_COICOP_{}'.format(year),
                'code': 'poste'
                },
            inplace = True,
            )
            
#    nomenclature_commune_file_path = os.path.join(directory_path, "Nomenclature commune.xls")
#    nomenclature_commune = pd.read_excel(nomenclature_commune_file_path, sheetname = "nomenclature")

    return masses_cn_12postes_data_frame

def weighted_sum(groupe, var):
    '''
    Fonction qui calcule la moyenne pondérée par groupe d'une variable
    '''
    data = groupe[var]
    weights = groupe['pondmen']
    return (data * weights).sum()


def collapsesum(data_frame, by = None, var = None):
    '''
    Pour une variable, fonction qui calcule la moyenne pondérée au sein de chaque groupe.
    '''
    assert by is not None
    assert var is not None
    grouped = data_frame.groupby([by])
    return grouped.apply(lambda x: weighted_sum(groupe = x, var =var))


def define_year_data(year_data_list, year_calage):
    diff=[]
    for i in range(0,len(year_data_list)):
        diff.append(year_calage - year_data_list[i])
   
    for i in range(0,len(year_data_list)):
        if diff[i]<0:
            diff[i] = 10

    minimum = np.argmin(diff)
    year_to_keep = year_data_list[minimum]
    
    #Todo: gérer les exceptions : années avant 2005...
    return  year_to_keep



if __name__ == '__main__':
    import sys
    import time
    logging.basicConfig(level = logging.INFO, stream = sys.stdout)
    deb = time.clock()

    # Quelle base de données choisir pour le calage ?
    year_calage=2007
    year_data_list = [2005, 2010]
    year_data = define_year_data(year_data_list, year_calage)

    # Masses de calage provenant de la comptabilité nationale
    masses_cn_12postes_data_frame = get_cn_data_frames(year = year_data, year_calage = year_calage)
    masses_cn_12postes_data_frame.set_index('poste', inplace = True)

    # Enquête agrégée au niveau des gros postes de COICOP (12)
    depenses_by_grosposte = temporary_store['depenses_by_grosposte_{}'.format(year_data)]

    dict_bdf_weighted_sum_by_grosposte = {}
    for grosposte in range(1,10):
        depenses_by_grosposte['{}pond'.format(grosposte)] = depenses_by_grosposte[grosposte]*depenses_by_grosposte['pondmen']
        dict_bdf_weighted_sum_by_grosposte[grosposte] = depenses_by_grosposte['{}pond'.format(grosposte)].sum()
    df_bdf_weighted_sum_by_grosposte = pd.DataFrame(pd.Series(data = dict_bdf_weighted_sum_by_grosposte, index = dict_bdf_weighted_sum_by_grosposte.keys()))

#   Calcul des ratios de calage :     
    masses = masses_cn_12postes_data_frame.merge(df_bdf_weighted_sum_by_grosposte, left_index = True, right_index = True)
    masses.rename(columns= {0:'conso_bdf{}'.format(year_data)}, inplace = True)
    masses['ratio_cn{}_cn{}'.format(year_data, year_calage)] = masses['consoCN_COICOP_{}'.format(year_calage)]/masses['consoCN_COICOP_{}'.format(year_data)]
    masses['ratio_bdf{}_cn{}'.format(year_data,year_data)] = 1000000 * masses['consoCN_COICOP_{}'.format(year_data)]/masses['conso_bdf{}'.format(year_data)]

# Application des ratios de calage 
    depenses = temporary_store['depenses_bdf_{}'.format(year_data)]
#
#    bygrosposte_df = pd.DataFrame(collapsesum(depenses,"grosposte","depense"))
#    bygrosposte_df.rename(columns = {0:'conso_bdf{}'.format(year)}, inplace = True)
#
#    bygrosposte_df['poste'] = bygrosposte_df.index.astype(int)
#    df_cn = get_CN_data_frames(year=2005,year_calage =2010)
#    df_cn['poste']=df_cn['poste'].astype(int)
#    depenses_cn_df = merge(left = df_cn, right=bygrosposte_df, on='poste')
#    depenses_cn_df['ratio_cn{}_cn{}'.format(year, year_calage)] = depenses_cn_df['consoCN_COICOP_{}'.format(year_calage)]/depenses_cn_df['consoCN_COICOP_{}'.format(year)]
#    depenses_cn_df['ratio_bdf{}_cn{}'.format(year,year)] = 1000000 * depenses_cn_df['consoCN_COICOP_{}'.format(year)]/depenses_cn_df['conso_bdf{}'.format(year)]
#    print depenses_cn_df

    log.info("step 03 calage duration is {}".format(time.clock() - deb))

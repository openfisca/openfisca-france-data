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
import pkg_resources

import pandas as pd
from pandas import read_excel, merge

log = logging.getLogger(__name__)

from ConfigParser import SafeConfigParser

def get_CN_data_frames(year = None,year_calage=None):
    '''
    
    '''
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

    parametres_fiscalite_file_path = os.path.join(directory_path, "Parametres fiscalite indirecte.xls")
    conso_cn_data_frame = read_excel(parametres_fiscalite_file_path, sheetname = "consommation_CN")

    selected_conso_cn_data_frame = conso_cn_data_frame[['Code',year,year_calage]]

    selected_conso_cn_data_frame['code_unicode']= selected_conso_cn_data_frame.Code.astype(unicode)
    selected_conso_cn_data_frame['len_code'] = selected_conso_cn_data_frame['code_unicode'].apply(lambda x: len(x))

    selected_conso_cn_data_frame = selected_conso_cn_data_frame[selected_conso_cn_data_frame['len_code']==6]
    selected_conso_cn_data_frame = selected_conso_cn_data_frame.drop(['len_code','code_unicode'],1)
   
    if year_calage <> year:
        selected_conso_cn_data_frame.rename(columns={
            year: 'consoCN_COICOP_{}'.format(year), 
            year_calage: 'consoCN_COICOP_{}'.format(year_calage),
            'Code': 'poste'}, inplace=True)
    else:
        selected_conso_cn_data_frame.rename(columns={
            year: 'consoCN_COICOP_{}'.format(year), 
            'Code': 'poste'}, inplace=True)        
    return selected_conso_cn_data_frame
    

def wsum(groupe, var):
    '''
    Fonction qui calcule la moyenne pondérée par groupe d'une variable
    '''
    d = groupe[var]
    w = groupe['pondmen']
    return (d * w).sum()
    
def collapsesum(dataframe, groupe, var):
    '''
    Pour une variable, fonction qui calcule la moyenne pondérée au sein de chaque groupe.
    '''
    grouped = dataframe.groupby([groupe])
    var_weighted_grouped = grouped.apply(lambda x: wsum(groupe = x,var =var))
    return var_weighted_grouped
    
# TODO: finir cette fonction qui sélectionne la data d'input automatiquement en fonction de l'année de simulation (calage)
#def define_year_data(year_data_list, year_calage):
#    diff=[]
#    for i in range(0,len(year_data_list)-1):    
#        print year_data_list[1]
##        diff[i] = year_calage - year_data_list[i]
#    return diff
#    define_year_data([2005,2010], 2011)
#    year_data_list = [2005,2010]


if __name__ == '__main__':
    import sys
    import time
    logging.basicConfig(level = logging.INFO, stream = sys.stdout)
    deb = time.clock()
    year = 2005
    year_calage=2010

    get_CN_data_frames(year=year, year_calage=year_calage)
    
    #TODO: get depense_data_frame from step_O1
    df= pd.pandas.io.stata.read_stata("/Volumes/LE GROS DD/IPP/TaxationIndirecte/Donnees_BdF_homogeneisees/2005/dépenses_BdF.dta")
#    df= pd.pandas.io.stata.read_stata("C:/Users/Vincent/Desktop/BdF/Taxation indirecte/Donnees BdF homogeneisees/2005/depenses_BdF.dta")

    bygrosposte_df = pd.DataFrame(collapsesum(df,"grosposte","depense"))
    bygrosposte_df.rename(columns = {0:'conso_bdf{}'.format(year)}, inplace = True)

    bygrosposte_df['poste'] = bygrosposte_df.index.astype(int)
    df_cn = get_CN_data_frames(year=2005,year_calage =2010)
    df_cn['poste']=df_cn['poste'].astype(int)
    depenses_cn_df = merge(left = df_cn, right=bygrosposte_df, on='poste')
    depenses_cn_df['ratio_cn{}_cn{}'.format(year, year_calage)] = depenses_cn_df['consoCN_COICOP_{}'.format(year_calage)]/depenses_cn_df['consoCN_COICOP_{}'.format(year)]
    depenses_cn_df['ratio_bdf{}_cn{}'.format(year,year)] = 1000000 * depenses_cn_df['consoCN_COICOP_{}'.format(year)]/depenses_cn_df['conso_bdf{}'.format(year)]
    print depenses_cn_df
    
    log.info("step 03 calage duration is {}".format(time.clock() - deb))
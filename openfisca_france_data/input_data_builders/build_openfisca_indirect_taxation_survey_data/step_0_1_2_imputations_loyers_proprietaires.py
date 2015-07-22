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


from ConfigParser import SafeConfigParser
import logging
import pandas


from openfisca_france_data.temporary import temporary_store_decorator
from openfisca_france_data import default_config_files_directory as config_files_directory
from openfisca_survey_manager.survey_collections import SurveyCollection


log = logging.getLogger(__name__)


# **************************************************************************************************************************
# * Etape n° 0-1-2 : IMPUTATION DE LOYERS POUR LES MENAGES PROPRIETAIRES
# **************************************************************************************************************************
@temporary_store_decorator(config_files_directory = config_files_directory, file_name = 'indirect_taxation_tmp')
def build_imputation_loyers_proprietaires(temporary_store = None, year = None):
    """Build menage consumption by categorie fiscale dataframe """

    assert temporary_store is not None
    assert year is not None

    # Load data
    bdf_survey_collection = SurveyCollection.load(collection = 'budget_des_familles',
        config_files_directory = config_files_directory)
    survey = bdf_survey_collection.get_survey('budget_des_familles_{}'.format(year))

    if year == 1995:
        imput00 = survey.get_values(table = "socioscm")
        # cette étape permet de ne garder que les données dont on est sûr de la qualité et de la véracité
        # exdep = 1 si les données sont bien remplies pour les dépenses du ménage
        # exrev = 1 si les données sont bien remplies pour les revenus du ménage
        imput00 = imput00[(imput00.exdep == 1) & (imput00.exrev == 1)]
        imput00 = imput00[(imput00.exdep == 1) & (imput00.exrev == 1)]
        kept_variables = ['mena', 'stalog', 'surfhab', 'confort1', 'confort2', 'confort3', 'confort4',
                        'ancons', 'sitlog', 'nbphab', 'rg', 'cc']
        imput00 = imput00[kept_variables]
        imput00.rename(columns = {'mena': 'ident_men'}, inplace = True)

        #TODO: continue variable cleaning
        var_to_filnas = ['surfhab']
        for var_to_filna in var_to_filnas:
            imput00[var_to_filna] = imput00[var_to_filna].fillna(0)

        var_to_ints = ['sitlog', 'confort1', 'stalog', 'surfhab', 'ident_men', 'ancons', 'nbphab']
        for var_to_int in var_to_ints:
            imput00[var_to_int] = imput00[var_to_int].astype(int)

        depenses = temporary_store['depenses_{}'.format(year)]
        depenses.reset_index(inplace = True)
        depenses_small = depenses[['ident_men', '04110', 'pondmen']].copy()
        depenses_small.ident_men = depenses_small.ident_men.astype('int')
        imput00 = depenses_small.merge(imput00, on = 'ident_men').set_index('ident_men')
        imput00.rename(columns = {'04110': 'loyer_reel'}, inplace = True)

#       * une indicatrice pour savoir si le loyer est connu et l'occupant est locataire

        imput00['observe'] = (imput00.loyer_reel > 0) & (imput00.stalog.isin([3, 4]))
        imput00['maison_appart'] = imput00.sitlog == 1

        imput00['catsurf'] = (
            1 +
            (imput00.surfhab > 15) +
            (imput00.surfhab > 30) +
            (imput00.surfhab > 40) +
            (imput00.surfhab > 60) +
            (imput00.surfhab > 80) +
            (imput00.surfhab > 100) +
            (imput00.surfhab > 150)
            )
        assert imput00.catsurf.isin(range(1, 9)).all()
        # TODO: vérifier ce qe l'on fait notamment regarder la vleur catsurf = 2 ommise dans le code stata
        imput00.maison = 1 - ((imput00.cc == 5) & (imput00.catsurf == 1) & (imput00.maison_appart == 1))
        imput00.maison = 1 - ((imput00.cc == 5) & (imput00.catsurf == 3) & (imput00.maison_appart == 1))
        imput00.maison = 1 - ((imput00.cc == 5) & (imput00.catsurf == 8) & (imput00.maison_appart == 1))
        imput00.maison = 1 - ((imput00.cc == 4) & (imput00.catsurf == 1) & (imput00.maison_appart == 1))

        try:
            parser = SafeConfigParser()
            config_local_ini = os.path.join(config_files_directory, 'config_local.ini')
            config_ini = os.path.join(config_files_directory, 'config.ini')
            parser.read([config_ini, config_local_ini])
            directory_path = os.path.normpath(
                parser.get("openfisca_france_indirect_taxation", "assets")
                )
            hotdeck = pandas.read_stata(os.path.join(directory_path, 'hotdeck_result.dta'))
        except:
            hotdeck = survey.get_values(table = 'hotdeck_result')


        imput00.reset_index(inplace = True)
        hotdeck.ident_men = hotdeck.ident_men.astype('int')
        imput00 = imput00.merge(hotdeck, on = 'ident_men')
        imput00.loyer_impute[imput00.observe] = 0
        imput00.reset_index(inplace = True)
        loyers_imputes = imput00[['ident_men', 'loyer_impute']].copy()
        assert loyers_imputes.loyer_impute.notnull().all()
        loyers_imputes.rename(columns = dict(loyer_impute = '0411'), inplace = True)

    # POUR BdF 2000 ET 2005, ON UTILISE LES LOYERS IMPUTES CALCULES PAR L'INSEE
    if year == 2000:
        # Garder les loyers imputés (disponibles dans la table sur les ménages)
        loyers_imputes = survey.get_values(table = "menage", variables = ['ident', 'rev81'])
        loyers_imputes.rename(
            columns = {
                'ident': 'ident_men',
                'rev81': '0421',
                },
            inplace = True,
            )

    if year == 2005:
        # Garder les loyers imputés (disponibles dans la table sur les ménages)
        loyers_imputes = survey.get_values(table = "menage")
        kept_variables = ['ident_men', 'rev801_d']
        loyers_imputes = loyers_imputes[kept_variables]
        loyers_imputes.rename(columns = {'rev801_d': '0421'}, inplace = True)

    if year == 2011:
        try:
            loyers_imputes = survey.get_values(table = "MENAGE")
        except:
            loyers_imputes = survey.get_values(table = "menage")

        kept_variables = ['ident_me', 'rev801']
        loyers_imputes = loyers_imputes[kept_variables]
        loyers_imputes.rename(columns = {'rev801': '0421', 'ident_me': 'ident_men'},
                              inplace = True)

    # Joindre à la table des dépenses par COICOP
    loyers_imputes.set_index('ident_men', inplace = True)
    temporary_store['loyers_imputes_{}'.format(year)] = loyers_imputes
    depenses = temporary_store['depenses_{}'.format(year)]
    depenses.index = depenses.index.astype('int64')
    loyers_imputes.index = loyers_imputes.index.astype('int64')
    assert set(depenses.index) == set(loyers_imputes.index)
    assert len(set(depenses.columns).intersection(set(loyers_imputes.columns))) == 0
    depenses = depenses.merge(loyers_imputes, left_index = True, right_index = True)

    # ****************************************************************************************************************
    #  Etape n° 0-1-3 : SAUVER LES BASES DE DEPENSES HOMOGENEISEES DANS LE BON DOSSIER
    # ****************************************************************************************************************

    # Save in temporary store
    temporary_store['depenses_bdf_{}'.format(year)] = depenses


if __name__ == '__main__':
    import sys
    import time
    logging.basicConfig(level = logging.INFO, stream = sys.stdout)
    deb = time.clock()
    year = 1995
    build_imputation_loyers_proprietaires(year = year)
    log.info("step 0_1_2_build_imputation_loyers_proprietaires duration is {}".format(time.clock() - deb))

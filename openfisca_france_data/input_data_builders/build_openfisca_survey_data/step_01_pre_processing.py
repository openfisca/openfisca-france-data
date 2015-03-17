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

import datetime

import gc
import numpy as np
import logging


from openfisca_france_data import default_config_files_directory as config_files_directory
from openfisca_france_data.temporary import TemporaryStore
from openfisca_france_data.input_data_builders.build_openfisca_survey_data.utils import assert_dtype
from openfisca_survey_manager.survey_collections import SurveyCollection


from openfisca_france_data.input_data_builders.build_openfisca_survey_data.base import create_replace

log = logging.getLogger(__name__)

temporary_store = TemporaryStore.create(file_name = "erfs")


# Prepare the some useful merged tables

# Menages et Individus


def create_indivim(year = None):
    """
    Création de la table individus concaténée (merged)
    """
    assert year is not None
    # load data
    erfs_survey_collection = SurveyCollection.load(
        collection = 'erfs', config_files_directory = config_files_directory)

    replace = create_replace(year)
    survey = erfs_survey_collection.get_survey('erfs_{}'.format(year))
    erfmen = survey.get_values(table = replace["erf_menage"])
    eecmen = survey.get_values(table = replace["eec_menage"])
    erfind = survey.get_values(table = replace["erf_indivi"])
    eecind = survey.get_values(table = replace["eec_indivi"])


#normalement l'option faire passer en lowercase et de remplacer tout "Ident"+yr par ident à été ajoutée dans une méthode de classe get_values survey.py
#    for table in [erfmen, eecmen, erfind, eecind]:
#        for column_name in table:
##            table.rename(columns = {column_name: column_name.lower()}, inplace = True)
#            if column_name == "ident08" :
#                table.rename(columns = {column_name: "ident"}, inplace = True)

    # travail sur la cohérence entre les bases
    noappar_m = eecmen[~(eecmen.ident.isin(erfmen.ident.values))]

    noappar_i = eecmen[~(eecmen.ident.isin(erfmen.ident.values))]
    noappar_i = noappar_i.drop_duplicates(subset = 'ident', take_last = True)
    # TODO: vérifier qu'il n'y a théoriquement pas de doublon

    difference = set(noappar_i.ident).symmetric_difference(noappar_m.ident)
    intersection = set(noappar_i.ident) & set(noappar_m.ident)
    log.info("There are {} diffenrents entries and {} intrsections".format(len(difference), len(intersection)))
    del noappar_i, noappar_m, difference, intersection
    gc.collect()

    # fusion enquete emploi et source fiscale
    menagem = erfmen.merge(eecmen)
    indivim = eecind.merge(erfind, on = ['noindiv', 'ident', 'noi'], how = "inner")

    # optimisation des types? Controle de l'existence en passant
    # TODO: minimal dtype
    # TODO: this should be done somewhere else
    var_list = ([
        'acteu',
        'agepr',
        'cohab',
        'contra',
        'encadr',
        'forter',
        'lien',
        'mrec',
#        'naia',
#TODO: fix this error on naia for 2007 (TypeError: invalid type comparison)
        'noicon',
        'noimer',
        'noiper',
        'prosa',
        'retrai',
        'rstg',
        'statut',
        'stc',
        'titc',
        'txtppb',
        ])

#    for indivim.columns in indivim:
#     for var in indivim:
    for var in var_list:
        if indivim[var].dtype != 'float64' and indivim[var].dtype != 'float32':
            filter00 = ((indivim[var] == "") | (indivim[var] ==  ".")) #  crée un filtre pour les valeurs manquantes, ne marche pas si type en float
            indivim[var][filter00] = np.nan
        try:
            indivim[var] = indivim[var].astype("float32")
        except Exception as e:
            log.info("{} {}".format(e, var))

########################
# création de variables#
########################

#   actrec : activité recodée comme preconisé par l'INSEE p84 du guide utilisateur
    indivim["actrec"] = np.nan
    # Attention : Q: pas de 6 ?!! A : Non pas de 6, la variable recodée de l'INSEE (voit p84 du guide methodo), ici \
    # la même nomenclatue à été adopée

#    3: contrat a durée déterminée
    indivim['actrec'][indivim['acteu'] == 1] = 3
    # TODO: check what is done

#    8 : femme (homme) au foyer, autre inactif
    indivim['actrec'][indivim['acteu'] == 3] = 8


#    1 : actif occupé non salarié
    filter1 = (indivim.acteu == 1) & (indivim.stc.isin([1, 3]))  # actifs occupés non salariés à son compte ou pour un
    indivim["actrec"][filter1] = 1                                # membre de sa famille
#   2 : salarié pour une durée non limitée
    filter2 = (indivim['acteu'] == 1) & (((indivim['stc'] == 2) & (indivim['contra'] == 1)) | (indivim['titc'] == 2))
    indivim['actrec'][filter2] = 2
#   4 : au chomage
    filter4 = (indivim['acteu'] == 2) | ((indivim['acteu'] == 3) & (indivim['mrec'] == 1))
    indivim['actrec'][filter4] = 4
#   5 : élève étudiant , stagiaire non rémunéré
    filter5 = (indivim['acteu'] == 3) & ((indivim['forter'] == 2) | (indivim['rstg'] == 1))
    indivim['actrec'][filter5] = 5
#   7 : retraité, préretraité, retiré des affaires unchecked
    filter7 = (indivim['acteu'] == 3) & ((indivim['retrai'] == 1) | (indivim['retrai'] == 2))
    indivim['actrec'][filter7] = 7
#   9 : probablement enfants de - de 16 ans TODO: check that fact in database and questionnaire
    indivim['actrec'][indivim['acteu'].isnull()] = 9

    indivim.actrec = indivim.actrec.astype("int8")
    assert_dtype(indivim['actrec'], "int8")
#   TODO : compare the result with results provided by Insee
#   tu99
    if year == 2009:
        erfind['tu99'] = None  # TODO: why ?

#   locataire
    menagem["locataire"] = menagem.so.isin([3, 4, 5])
    menagem["locataire"] = menagem["locataire"].astype("bool")

    transfert = indivim.ix[indivim['lpr'] == 1, ['ident', 'ddipl']]
    menagem = menagem.merge(transfert)

    # correction
    def _manually_remove_errors():
        '''
        This method is here because some oddities can make it through the controls throughout the procedure
        It is here to remove all these individual errors that compromise the process.
        '''
        if year == 2006:
            indivim.lien[indivim.noindiv == 603018905] = 2
            indivim.noimer[indivim.noindiv == 603018905] = 1
            log.info("{}".format(indivim[indivim.noindiv == 603018905].to_string()))

    _manually_remove_errors()

    # save
    save_temp(menagem, name="menagem", year=year)
    del eecmen, erfmen, menagem, transfert
    gc.collect()
    save_temp(indivim, name="indivim", year=year)
    del erfind, eecind
    gc.collect()


def create_enfants_a_naitre(year = None):
    '''
    '''
    assert year is not None

    erfs_survey_collection = SurveyCollection.load(collection = 'erfs')
    survey = erfs_survey_collection.surveys['erfs_{}'.format(year)]
#   Enfant à naître (NN pour nouveaux nés)
    individual_vars = [
        'acteu',
        'agepr',
        'cohab',
        'contra',
        'forter',
        'ident',
        'lien',
        'lpr',
        'mrec',
        'naia',
        'naim',
        'noi',
        'noicon',
        'noimer',
        'noindiv',
        'noiper',
        'retrai',
        'rga',
        'rstg',
        'sexe',
        'stc',
        'titc',
        ]

    eeccmp1 = survey.get_values(table = "eec_cmp_1", variables = individual_vars)
    eeccmp2 = survey.get_values(table = "eec_cmp_2", variables = individual_vars)
    eeccmp3 = survey.get_values(table = "eec_cmp_3", variables = individual_vars)
    tmp = eeccmp1.merge(eeccmp2, how = "outer")
    enfants_a_naitre = tmp.merge(eeccmp3, how = "outer")

    # optimisation des types? Controle de l'existence en passant
    # pourquoi pas des int quand c'est possible
    # TODO: minimal dtype TODO: shoudln't be here
    for var in individual_vars:
        enfants_a_naitre[var] = enfants_a_naitre[var].astype('float')
#    del eeccmp1, eeccmp2, eeccmp3, individual_vars  #TODO: Adrien: me fait planter python

    # création de variables
    enfants_a_naitre['declar1'] = ''
    enfants_a_naitre['noidec'] = 0
    enfants_a_naitre['ztsai'] = 0
    enfants_a_naitre['year'] = year
    enfants_a_naitre.year = enfants_a_naitre.year.astype("float32")  # TODO: should be an integer but NaN are present
    enfants_a_naitre['agepf'] = enfants_a_naitre.year - enfants_a_naitre.naia
    enfants_a_naitre['agepf'][enfants_a_naitre.naim >= 7] -= 1
    enfants_a_naitre['actrec'] = 9
    enfants_a_naitre['quelfic'] = 'ENF_NN'
    enfants_a_naitre['persfip'] = ""

    # TODO: deal with agepf
    for series_name in ['actrec', 'noidec', 'ztsai']:
        assert_dtype(enfants_a_naitre[series_name], "int")

    # selection
    enfants_a_naitre = enfants_a_naitre[
        (
            (enfants_a_naitre.naia == enfants_a_naitre.year) & (enfants_a_naitre.naim >= 10)
            ) | (
                (enfants_a_naitre.naia == enfants_a_naitre.year + 1) & (enfants_a_naitre.naim <= 5)
                )
        ].copy()

    save_temp(enfants_a_naitre, name = "enfants_a_naitre", year = year)
    gc.collect()


if __name__ == '__main__':
    log.info('Entering 01_pre_proc')
    import sys
    import time
    logging.basicConfig(level = logging.INFO, stream = sys.stdout)
    deb = time.clock()
    year = 2009
    create_indivim(year = year)
    create_enfants_a_naitre(year = year)
    log.info("etape 01 pre-processing terminee en {}".format(time.clock() - deb))

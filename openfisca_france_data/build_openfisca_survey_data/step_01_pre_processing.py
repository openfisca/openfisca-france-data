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


import gc

import logging

from openfisca_france_data.surveys import SurveyCollection
from openfisca_france_data.build_openfisca_survey_data import save_temp
from openfisca_france_data.build_openfisca_survey_data.utilitaries import assert_dtype

log = logging.getLogger(__name__)

# Prepare the some useful merged tables

# Menages et Individus


def create_indivim(year = 2006):
    '''
    '''
    # load
    erfs_survey_collection = SurveyCollection.load(collection = 'erfs')
    survey = erfs_survey_collection.surveys['erfs_{}'.format(year)]

    erfmen = survey.get_values(table = "erf_menage")
    eecmen = survey.get_values(table = "eec_menage")
    log.info(erfmen.info())

    erfind = survey.get_values(table = "erf_indivi")
    eecind = survey.get_values(table = "eec_indivi")

    log.info(eecind.info())
    log.info(erfind.info())

    # travail sur la cohérence entre les bases
    noappar_m = eecmen[~(eecmen.ident.isin(erfmen.ident.values))]

    noappar_i = eecmen[~(eecmen.ident.isin(erfmen.ident.values))]
    noappar_i = noappar_i.drop_duplicates(cols = 'ident', take_last = True)
    #TODO: vérifier qu'il n'y a théoriquement pas de doublon

    difference = set(noappar_i.ident).symmetric_difference(noappar_m.ident)
    intersection = set(noappar_i.ident) & set(noappar_m.ident)
    log.info((difference, intersection))
    del noappar_i, noappar_m, difference, intersection
    gc.collect()

    #fusion enquete emploi et source fiscale
    menagem = erfmen.merge(eecmen)
    indivim = eecind.merge(erfind, on = ['noindiv', 'ident', 'noi'], how = "inner")

    # optimisation des types? Controle de l'existence en passant
    #TODO: minimal dtype
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
        'naia',
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

    for var in var_list:
        try:
            indivim[var] = indivim[var].astype("float32")
        except:
            print "{} is missing".format(var)

    # création de variables
    ## actrec
    indivim['actrec'] = 0
    #TODO: pas de 6 ?!!
    filter1 = (indivim['acteu'] == 1) & (indivim['stc'].isin([1, 3]))
    indivim['actrec'][filter1] = 1
    filter2 = (indivim['acteu'] == 1) & (((indivim['stc'] == 2) & (indivim['contra'] == 1)) | (indivim['titc'] == 2))
    indivim['actrec'][filter2] = 2
    indivim['actrec'][indivim['acteu'] == 1] = 3
    filter4 = (indivim['acteu'] == 2) | ((indivim['acteu'] == 3) & (indivim['mrec'] == 1))
    indivim['actrec'][filter4] = 4
    filter5 = (indivim['acteu'] == 3) & ((indivim['forter'] == 2) | (indivim['rstg'] == 1))
    indivim['actrec'][filter5] = 5
    filter7 = (indivim['acteu'] == 3) & ((indivim['retrai'] == 1) | (indivim['retrai'] == 2))
    indivim['actrec'][filter7] = 7
    indivim['actrec'][indivim['acteu'] == 3] = 8
    indivim['actrec'][indivim['acteu'].isnull()] = 9

    assert_dtype(indivim['actrec'], "int")

    # tu99
    if year == 2009:
        erfind['tu99'] = None  # TODO: why ?

    ## locataire
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
            print indivim[indivim.noindiv == 603018905].to_string()

    _manually_remove_errors()

    # save
    save_temp(menagem, name="menagem", year=year)
    del eecmen, erfmen, menagem, transfert
    gc.collect()
    save_temp(indivim, name="indivim", year=year)
    del erfind, eecind
    gc.collect()


def create_enfants_a_naitre(year = 2006):
    '''
    '''

    erfs_survey_collection = SurveyCollection.load()
    survey = erfs_survey_collection.surveys['erfs_{}'.format(year)]

    ### Enfant à naître (NN pour nouveaux nés)
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
        print var
        enfants_a_naitre[var] = enfants_a_naitre[var].astype('float')
    del eeccmp1, eeccmp2, eeccmp3, individual_vars

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

    #selection
    enfants_a_naitre = enfants_a_naitre[
        (
            (enfants_a_naitre.naia == enfants_a_naitre.year.) & (enfants_a_naitre.naim >= 10)
            ) | (
                    (enfants_a_naitre.naia == enfants_a_naitre.year + 1) & (enfants_a_naitre.naim. <= 5)
                    )
        ].copy()

    save_temp(enfants_a_naitre, name = "enfants_a_naitre", year = year)
    gc.collect()


if __name__ == '__main__':
    print('Entering 01_pre_proc')
    import sys
    logging.basicConfig(level = logging.INFO, stream = sys.stdout)
    import time
    deb = time.clock()
    year = 2006
    create_indivim(year = year)
    create_enfants_a_naitre(year = year)
    print time.clock() - deb

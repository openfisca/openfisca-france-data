#! /usr/bin/env python
import gc
import numpy as np
import logging


from openfisca_survey_manager.temporary import temporary_store_decorator
from openfisca_france_data.utils import assert_dtype
from openfisca_france_data.erfs.input_data_builder.base import (
    year_specific_by_generic_data_frame_name
    )
from openfisca_survey_manager.survey_collections import SurveyCollection


log = logging.getLogger(__name__)


def create_actrec_variable(indivim):
    """
    Création de la variables actrec
    pour activité recodée comme preconisé par l'INSEE p84 du guide méthodologique de l'ERFS
    """
    assert "actrec" not in indivim.columns
    indivim["actrec"] = np.nan
    # Attention : Pas de 6, la variable recodée de l'INSEE (voit p84 du guide methodo), ici \
    # la même nomenclature à été adopée
    # 3: contrat a durée déterminée
    indivim.loc[indivim.acteu == 1, 'actrec'] = 3
    # 8: femme (homme) au foyer, autre inactif
    indivim.loc[indivim.acteu == 3, 'actrec'] = 8
    # 1: actif occupé non salarié
    filter1 = (indivim.acteu == 1) & (indivim.stc.isin([1, 3]))  # actifs occupés non salariés à son compte ou pour un
    indivim.loc[filter1, 'actrec'] = 1                              # membre de sa famille
    # 2: salarié pour une durée non limitée
    filter2 = (indivim.acteu == 1) & (((indivim.stc == 2) & (indivim.contra == 1)) | (indivim.titc == 2))
    indivim.loc[filter2, 'actrec'] = 2
    # 4: au chomage
    filter4 = (indivim.acteu == 2) | ((indivim.acteu == 3) & (indivim.mrec == 1))
    indivim.loc[filter4, 'actrec'] = 4
    # 5: élève étudiant , stagiaire non rémunéré
    filter5 = (indivim.acteu == 3) & ((indivim.forter == 2) | (indivim.rstg == 1))
    indivim.loc[filter5, 'actrec'] = 5
    # 7: retraité, préretraité, retiré des affaires unchecked
    filter7 = (indivim.acteu == 3) & ((indivim.retrai == 1) | (indivim.retrai == 2))
    indivim.loc[filter7, 'actrec'] = 7
    # 9: probablement enfants de - de 16 ans TODO: check that fact in database and questionnaire
    indivim.loc[indivim.acteu == 0, 'actrec'] = 9

    assert indivim.actrec.notnull().all()
    indivim.actrec = indivim.actrec.astype("int8")
    assert_dtype(indivim.actrec, "int8")

    assert (indivim.actrec != 6).all(), 'actrec ne peut pas être égale à 6'
    assert indivim.actrec.isin(range(1, 10)).all(), 'actrec values are outside the interval [1, 9]'


def create_variable_locataire(menagem):
    # Locataire
    menagem["locataire"] = menagem.so.isin([3, 4, 5])
    assert_dtype(menagem.locataire, "bool")


def check_integer_dtype(indivim, var_list):
    for var in var_list:
        assert np.issubdtype(indivim[var].dtype, np.integer), \
            "Variable {} dtype is {} and should be an integer".format(var, indivim[var].dtype)


def manually_remove_noindiv_errors(indivim):
    '''
    This method is here because some oddities can make it through the controls throughout the procedure
    It is here to remove all these individual errors that compromise the process.
    '''
    if year == 2006:
        indivim.lien[indivim.noindiv == 603018905] = 2
        indivim.noimer[indivim.noindiv == 603018905] = 1
        log.info("{}".format(indivim[indivim.noindiv == 603018905].to_string()))


@temporary_store_decorator(file_name = "erfs")
def merge_tables(temporary_store = None, year = None):
    """
    Création des tables ménages et individus concaténée (merged)
    """
    # Prepare the some useful merged tables

    assert temporary_store is not None
    assert year is not None
    # load data
    erfs_survey_collection = SurveyCollection.load(
        collection = 'erfs', config_files_directory = config_files_directory)

    year_specific_by_generic = year_specific_by_generic_data_frame_name(year)
    survey = erfs_survey_collection.get_survey('erfs_{}'.format(year))
    erfmen = survey.get_values(table = year_specific_by_generic["erf_menage"])
    eecmen = survey.get_values(table = year_specific_by_generic["eec_menage"])
    erfind = survey.get_values(table = year_specific_by_generic["erf_indivi"])
    eecind = survey.get_values(table = year_specific_by_generic["eec_indivi"])

    # travail sur la cohérence entre les bases
    noappar_m = eecmen[~(eecmen.ident.isin(erfmen.ident.values))].copy()

    noappar_i = eecmen[~(eecind.ident.isin(erfind.ident.values))].copy()
    noappar_i = noappar_i.drop_duplicates(subset = 'ident', take_last = True)
    # TODO: vérifier qu'il n'y a théoriquement pas de doublon

    difference = set(noappar_i.ident).symmetric_difference(noappar_m.ident)
    intersection = set(noappar_i.ident) & set(noappar_m.ident)
    log.info("There are {} differences and {} intersections".format(len(difference), len(intersection)))
    del noappar_i, noappar_m, difference, intersection
    gc.collect()

    # fusion enquete emploi et source fiscale
    menagem = erfmen.merge(eecmen)
    indivim = eecind.merge(erfind, on = ['noindiv', 'ident', 'noi'], how = "inner")
    var_list = [
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
        'otitc',
        'txtppb',
        ]
    check_integer_dtype(indivim, var_list)

    create_actrec_variable(indivim)
    create_variable_locataire(menagem)
    menagem = menagem.merge(
        indivim.loc[indivim.lpr == 1, ['ident', 'ddipl']].copy()
        )
    manually_remove_noindiv_errors(indivim)

    temporary_store['menagem_{}'.format(year)] = menagem
    del eecmen, erfmen, menagem
    gc.collect()
    temporary_store['indivim_{}'.format(year)] = indivim
    del erfind, eecind


@temporary_store_decorator(file_name = "erfs")
def create_enfants_a_naitre(temporary_store = None, year = None):
    '''
    '''
    assert temporary_store is not None
    assert year is not None

    erfs_survey_collection = SurveyCollection.load(
        collection = 'erfs', config_files_directory = config_files_directory)
    survey = erfs_survey_collection.get_survey('erfs_{}'.format(year))
    # Enfant à naître (NN pour nouveaux nés)
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
    year_specific_by_generic = year_specific_by_generic_data_frame_name(year)
    eeccmp1 = survey.get_values(table = year_specific_by_generic["eec_cmp_1"], variables = individual_vars)
    eeccmp2 = survey.get_values(table = year_specific_by_generic["eec_cmp_2"], variables = individual_vars)
    eeccmp3 = survey.get_values(table = year_specific_by_generic["eec_cmp_3"], variables = individual_vars)
    tmp = eeccmp1.merge(eeccmp2, how = "outer")
    enfants_a_naitre = tmp.merge(eeccmp3, how = "outer")

    # optimisation des types? Controle de l'existence en passant
    # pourquoi pas des int quand c'est possible
    # TODO: minimal dtype TODO: shoudln't be here
    for var in individual_vars:
        assert_dtype(enfants_a_naitre[var], 'float')
    del eeccmp1, eeccmp2, eeccmp3, individual_vars, tmp
    gc.collect()

    # création de variables
    enfants_a_naitre['declar1'] = ''
    enfants_a_naitre['noidec'] = 0
    enfants_a_naitre['ztsai'] = 0
    enfants_a_naitre['year'] = year
    enfants_a_naitre.year = enfants_a_naitre.year.astype("float32")  # TODO: should be an integer but NaN are present
    enfants_a_naitre['agepf'] = enfants_a_naitre.year - enfants_a_naitre.naia
    enfants_a_naitre.loc[enfants_a_naitre.naim >= 7,'agepf'] -= 1
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

    temporary_store["enfants_a_naitre_{}".format(year)] = enfants_a_naitre

if __name__ == '__main__':
    log.info('Entering 01_pre_proc')
    import sys
    import time
    logging.basicConfig(level = logging.INFO, stream = sys.stdout)
    deb = time.clock()
    year = 2009
    merge_tables(year = year)
    create_enfants_a_naitre(year = year)
    log.info("etape 01 pre-processing terminee en {}".format(time.clock() - deb))

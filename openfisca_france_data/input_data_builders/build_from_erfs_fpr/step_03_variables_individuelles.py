#!/usr/bin/env python
# -*- coding: utf-8 -*-


import gc
import logging
import numpy as np

from openfisca_france_data.temporary import temporary_store_decorator
from openfisca_france_data.input_data_builders.build_openfisca_survey_data.utils import (
    assert_dtype, 
    id_formatter,
    )

log = logging.getLogger(__name__)


@temporary_store_decorator(file_name = 'erfs_fpr')
def create_variables_individuelles(temporary_store = None, year = None):
    """
    Création des variables individuelles
    """

    assert temporary_store is not None
    assert year is not None

    kind = 'erfs_fpr'

    log.info('step_03_variables_individuelles: Création des variables individuelles')

    indivim = temporary_store['indivim_{}'.format(year)]

    create_age_variables(indivim, year)
    create_activite_variable(indivim)
    create_revenus_variables(indivim)

    variables = [
        'activite',
        'age',
        'age_en_mois',
        'chomage_imposable',
        'pensions_alimentaires_percues',
        'rag',
        'retraite_imposable',
        'ric',
        'rnc',
        'salaire_imposable',
        'idmen',
        'quimen',
        'idfoy',
        'quifoy',
        'idfam',
        'quifam',
        'noindiv',
        ]
    data_frame = create_ids_and_roles(indivim)[variables].copy()
    del indivim
    gc.collect()
    for entity_id in ['idmen', 'idfoy', 'idfam']:
        log.info('Reformat ids: {}'.format(entity_id))
        data_frame = id_formatter(data_frame, entity_id)
    data_frame.reset_index(inplace = True)
    temporary_store['input_{}'.format(year)] = data_frame
    log.info(u"step_03_variables_individuelles terminée")


# helpers

def create_activite_variable(indivim):
    """
    Création de la variable activite
    0 = Actif occupé
    1 = Chômeur
    2 = Étudiant, élève
    3 = Retraité
    4 = Autre inactif
    """
    create_actrec_variable(indivim)

    indivim['activite'] = np.nan
    indivim.loc[indivim.actrec <= 3, 'activite'] = 0
    indivim.loc[indivim.actrec == 4, 'activite'] = 1
    indivim.loc[indivim.actrec == 5, 'activite'] = 2
    indivim.loc[indivim.actrec == 7, 'activite'] = 3
    indivim.loc[indivim.actrec == 8, 'activite'] = 4
    indivim.loc[indivim.age <= 13, 'activite'] = 2  # ce sont en fait les actrec=9
    message = "Valeurs prises par la variable activité \n {}".format(indivim['activite'].value_counts(dropna = False))
    assert indivim.activite.notnull().all(), message
    assert indivim.activite.isin(range(5)).all(), message


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


def create_age_variables(indivim, year = None):
    """
    Création de la variables actrec
    pour activité recodée comme preconisé par l'INSEE p84 du guide méthodologique de l'ERFS
    """
    assert year is not None
    indivim['age'] = year - indivim.naia - 1
    indivim['age_en_mois'] = 12 * indivim.age + 12 - indivim.naim  # TODO why 12 - naim

    for variable in ['age', 'age_en_mois']:
        assert indivim[variable].notnull().all(), "Il y a {} entrées non renseignées pour la variable {}".format(
            indivim[variable].notnull().sum(), variable)


def create_revenus_variables(indivim):
    old_by_new_variables = {
        'chomage_i': 'chomage_imposable',
        'pens_alim_recue_i': 'pensions_alimentaires_percues',
        'rag_i': 'rag',
        'retraites_i': 'retraite_imposable',
        'ric_i': 'ric',
        'rnc_i': 'rnc',
        'salaires_i': 'salaire_imposable',
        }
    for variable in old_by_new_variables.keys():
        print variable, variable in indivim.columns.tolist()
        assert variable in indivim.columns.tolist(), "La variable {} n'est pas présente".format(variable)

    indivim.rename(
        columns = old_by_new_variables,
        inplace = True,
        )

    for variable in old_by_new_variables.values():
        if (indivim[variable] < 0).any():
            log.info("La variable {} contient des valeurs négatives\n {}".format(
                variable,
                indivim[variable].value_counts().loc[indivim[variable].value_counts().index < 0]
                )
            )


def create_ids_and_roles(indivim):
    old_by_new_variables = {
        'ident': 'idmen',
        }
    indivim.rename(
        columns = old_by_new_variables,
        inplace = True,
        )
    indivim['quimen'] = 9
    indivim.loc[indivim.lpr == 1, 'quimen'] = 0
    indivim.loc[indivim.lpr == 2, 'quimen'] = 1

    indivim['idfoy'] = indivim['idmen'].copy()
    indivim['idfam'] = indivim['idmen'].copy()
    indivim['quifoy'] = indivim['quimen'].copy()
    indivim['quifam'] = indivim['quimen'].copy()

    return indivim.loc[indivim.quimen <= 1].copy()


def todo_create(indivim):
    indivim.loc[indivim.titc.isnull(), 'titc'] = 0
    assert indivim.titc.notnull().all(), \
        u"Problème avec les titc"  # On a 420 NaN pour les varaibels statut, titc etc

    log.info(u"    6.2 : Variable statut")
    indivim.loc[indivim.statut.isnull(), 'statut'] = 0
    indivim.statut = indivim.statut.astype('int')
    indivim.loc[indivim.statut == 11, 'statut'] = 1
    indivim.loc[indivim.statut == 12, 'statut'] = 2
    indivim.loc[indivim.statut == 13, 'statut'] = 3
    indivim.loc[indivim.statut == 21, 'statut'] = 4
    indivim.loc[indivim.statut == 22, 'statut'] = 5
    indivim.loc[indivim.statut == 33, 'statut'] = 6
    indivim.loc[indivim.statut == 34, 'statut'] = 7
    indivim.loc[indivim.statut == 35, 'statut'] = 8
    indivim.loc[indivim.statut == 43, 'statut'] = 9
    indivim.loc[indivim.statut == 44, 'statut'] = 10
    indivim.loc[indivim.statut == 45, 'statut'] = 11
    assert indivim.statut.isin(range(12)).all(), u"statut value over range"
    log.info("Valeurs prises par la variable statut \n {}".format(
        indivim['statut'].value_counts(dropna = False)))

    log.info(u"    6.3 : variable txtppb")
    indivim.loc[indivim.txtppb.isnull(), 'txtppb'] = 0
    assert indivim.txtppb.notnull().all()
    indivim.loc[indivim.nbsala.isnull(), 'nbsala'] = 0
    indivim.nbsala = indivim.nbsala.astype('int')
    indivim.loc[indivim.nbsala == 99, 'nbsala'] = 10
    assert indivim.nbsala.isin(range(11)).all()
    log.info("Valeurs prises par la variable txtppb \n {}".format(
        indivim['txtppb'].value_counts(dropna = False)))

    log.info(u"    6.4 : variable chpub et CSP")
    indivim.loc[indivim.chpub.isnull(), 'chpub'] = 0
    indivim.chpub = indivim.chpub.astype('int')
    assert indivim.chpub.isin(range(11)).all()

    indivim['cadre'] = 0
    indivim.loc[indivim.prosa.isnull(), 'prosa'] = 0
    assert indivim.prosa.notnull().all()
    log.info("Valeurs prises par la variable encadr \n {}".format(indivim['encadr'].value_counts(dropna = False)))

    # encadr : 1=oui, 2=non
    indivim.loc[indivim.encadr.isnull(), 'encadr'] = 2
    indivim.loc[indivim.encadr == 0, 'encadr'] = 2
    assert indivim.encadr.notnull().all()
    assert indivim.encadr.isin([1, 2]).all()

    indivim.loc[indivim.prosa.isin([7, 8]), 'cadre'] = 1
    indivim.loc[(indivim.prosa == 9) & (indivim.encadr == 1), 'cadre'] = 1
    assert indivim.cadre.isin(range(2)).all()



if __name__ == '__main__':
    import sys
    logging.basicConfig(level = logging.INFO, stream = sys.stdout)
    # logging.basicConfig(level = logging.INFO,  filename = 'step_03.log', filemode = 'w')
    year = 2012
    create_variables_individuelles(year = year)


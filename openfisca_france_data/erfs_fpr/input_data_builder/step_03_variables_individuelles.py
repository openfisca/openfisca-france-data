#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division

import logging
import numpy as np
import pandas as pd


from openfisca_france_data.utils import (
    assert_dtype,
    )
from openfisca_survey_manager.temporary import temporary_store_decorator

log = logging.getLogger(__name__)


@temporary_store_decorator(file_name = 'erfs_fpr')
def build_variables_individuelles(temporary_store = None, year = None):
    """
    Création des variables individuelles
    """

    assert temporary_store is not None
    assert year is not None

    log.info('step_03_variables_individuelles: Création des variables individuelles')

    individus = temporary_store['individus_{}'.format(year)]
    create_variables_individuelles(individus, year)
    temporary_store['individus_{}'.format(year)] = individus
    log.info(u"step_03_variables_individuelles terminée")


# helpers

def create_variables_individuelles(individus, year):
    create_age_variables(individus, year)
    create_activite_variable(individus)
    create_revenus_variables(individus)
    create_categorie_salarie_variable(individus)
    create_effectif_entreprise_variable(individus)
    create_contrat_de_travail(individus)


def create_activite_variable(individus):
    """
    Création de la variable activite
    0 = Actif occupé
    1 = Chômeur
    2 = Étudiant, élève
    3 = Retraité
    4 = Autre inactif
    """
    create_actrec_variable(individus)

    individus['activite'] = np.nan
    individus.loc[individus.actrec <= 3, 'activite'] = 0
    individus.loc[individus.actrec == 4, 'activite'] = 1
    individus.loc[individus.actrec == 5, 'activite'] = 2
    individus.loc[individus.actrec == 7, 'activite'] = 3
    individus.loc[individus.actrec == 8, 'activite'] = 4
    individus.loc[individus.age <= 13, 'activite'] = 2  # ce sont en fait les actrec=9
    message = "Valeurs prises par la variable activité \n {}".format(individus['activite'].value_counts(dropna = False))
    assert individus.activite.notnull().all(), message
    assert individus.activite.isin(range(5)).all(), message


def create_actrec_variable(individus):
    """
    Création de la variables actrec
    pour activité recodée comme preconisé par l'INSEE p84 du guide méthodologique de l'ERFS
    """
    assert "actrec" not in individus.columns
    individus["actrec"] = np.nan
    # Attention : Pas de 6, la variable recodée de l'INSEE (voit p84 du guide methodo), ici \
    # la même nomenclature à été adopée
    # 3: contrat a durée déterminée
    individus.loc[individus.acteu == 1, 'actrec'] = 3
    # 8: femme (homme) au foyer, autre inactif
    individus.loc[individus.acteu == 3, 'actrec'] = 8
    # 1: actif occupé non salarié
    filter1 = (individus.acteu == 1) & (individus.stc.isin([1, 3]))  # actifs occupés non salariés à son compte
    individus.loc[filter1, 'actrec'] = 1                             # ou pour un membre de sa famille
    # 2: salarié pour une durée non limitée
    filter2 = (individus.acteu == 1) & (((individus.stc == 2) & (individus.contra == 1)) | (individus.titc == 2))
    individus.loc[filter2, 'actrec'] = 2
    # 4: au chomage
    filter4 = (individus.acteu == 2) | ((individus.acteu == 3) & (individus.mrec == 1))
    individus.loc[filter4, 'actrec'] = 4
    # 5: élève étudiant , stagiaire non rémunéré
    filter5 = (individus.acteu == 3) & ((individus.forter == 2) | (individus.rstg == 1))
    individus.loc[filter5, 'actrec'] = 5
    # 7: retraité, préretraité, retiré des affaires unchecked
    filter7 = (individus.acteu == 3) & ((individus.retrai == 1) | (individus.retrai == 2))
    individus.loc[filter7, 'actrec'] = 7
    # 9: probablement enfants de - de 16 ans TODO: check that fact in database and questionnaire
    individus.loc[individus.acteu == 0, 'actrec'] = 9

    assert individus.actrec.notnull().all()
    individus.actrec = individus.actrec.astype("int8")
    assert_dtype(individus.actrec, "int8")

    assert (individus.actrec != 6).all(), 'actrec ne peut pas être égale à 6'
    assert individus.actrec.isin(range(1, 10)).all(), 'actrec values are outside the interval [1, 9]'


def create_age_variables(individus, year = None):
    """
    Création de la variables actrec
    pour activité recodée comme preconisé par l'INSEE p84 du guide méthodologique de l'ERFS
    """
    assert year is not None
    individus['age'] = year - individus.naia - 1
    individus['age_en_mois'] = 12 * individus.age + 12 - individus.naim  # TODO why 12 - naim

    for variable in ['age', 'age_en_mois']:
        assert individus[variable].notnull().all(), "Il y a {} entrées non renseignées pour la variable {}".format(
            individus[variable].notnull().sum(), variable)


def create_categorie_salarie_variable(individus):
    """
    Création de la variable categorie_salarie:
        u"prive_non_cadre
        u"prive_cadre
        u"public_titulaire_etat
        u"public_titulaire_militaire
        u"public_titulaire_territoriale
        u"public_titulaire_hospitaliere
        u"public_non_titulaire

    A partir des variables de l'ecc' :
    chpub :
        1 - Etat
        2 - Collectivités locales, HLM
        3 - Hôpitaux publics
        4 - Particulier
        5 - Entreprise publique (La Poste, EDF-GDF, etc.)
        6 - Entreprise privée, association
    encadr : (encadrement de personnes)
        1 - Oui
        2 - Non
    statut :
        11 - Indépendants
        12 - Employeurs
        13 - Aides familiaux
        21 - Intérimaires
        22 - Apprentis
        33 - CDD (hors Etat, coll.loc.), hors contrats aides
        34 - Stagiaires et contrats aides (hors Etat, coll.loc.)
        35 - Autres contrats (hors Etat, coll.loc.)
        43 - CDD (Etat, coll.loc.), hors contrats aides
        44 - Stagiaires et contrats aides (Etat, coll.loc.)
        45 - Autres contrats (Etat, coll.loc.)
    titc :
        1 - Elève fonctionnaire ou stagiaire
        2 - Agent titulaire
        3 - Contractuel

    """
    # TODO: Est-ce que les stagiaires sont considérées comme des contractuels dans OF ?

    assert individus.chpub.isin(range(0, 7)).all(), \
        "chpub n'est pas toujours dans l'intervalle [1, 6]\n{}".format(individus.chpub.value_counts())

    assert individus.chpub.isin(range(0, 7)).all(), \
        "chpub n'est pas toujours dans l'intervalle [1, 6]\n{}".format(individus.chpub.value_counts())

    individus.loc[individus.encadr == 0, 'encadr'] = 2
    assert individus.encadr.isin(range(1, 3)).all(), \
        "encadr n'est pas toujours dans l'intervalle [1, 2]\n{}".format(individus.encadr.value_counts())

    assert individus.prosa.isin(range(0, 10)).all(), \
        "prosa n'est pas toujours dans l'intervalle [0, 9]\n{}".format(individus.prosa.value_counts())

    statut_values = [0, 11, 12, 13, 21, 22, 33, 34, 35, 43, 44, 45]
    assert individus.statut.isin(statut_values).all(), \
        "statut n'est pas toujours dans l'ensemble {} des valeurs antendues.\n{}".format(
            statut_values,
            individus.statut.value_counts()
            )

    assert individus.titc.isin(range(4)).all(), \
        "titc n'est pas toujours dans l'ensemble [0, 3] des valeurs antendues.\n{}".format(
            individus.statut.value_counts()
            )

    chpub = individus.chpub
    titc = individus.titc

    # encadrement
    assert 'cadre' not in individus.columns
    individus['cadre'] = False
    individus.loc[individus.prosa.isin([7, 8]), 'cadre'] = True
    individus.loc[(individus.prosa == 9) & (individus.encadr == 1), 'cadre'] = True
    cadre = (individus.statut == 35) & (chpub > 3) & individus.cadre
    del individus['cadre']

    # etat_stag = (chpub==1) & (titc == 1)
    etat_titulaire = (chpub == 1) & (titc == 2)
    etat_contractuel = (chpub == 1) & (titc == 3)

    militaire = False  # TODO:

    # collect_stag = (chpub==2) & (titc == 1)
    collectivites_locales_titulaire = (chpub == 2) & (titc == 2)
    collectivites_locales_contractuel = (chpub == 2) & (titc == 3)

    # hosp_stag = (chpub==2)*(titc == 1)
    hopital_titulaire = (chpub == 3) & (titc == 2)
    hopital_contractuel = (chpub == 3) & (titc == 3)

    contractuel = collectivites_locales_contractuel | hopital_contractuel | etat_contractuel

    individus['categorie_salarie'] = np.select(
        [0, 1, 2, 3, 4, 5, 6],
        [0, cadre, etat_titulaire, militaire, collectivites_locales_titulaire, hopital_titulaire, contractuel]
        )

    assert individus['categorie_salarie'].isin(range(10)).all(), \
        "categorie_salarie n'est pas toujours dans l'intervalle [0, 9]\n{}".format(
            individus.categorie_salarie.value_counts())


def create_contrat_de_travail(individus):
    """
    Création de la variable contrat_de_travail
        0 - temps_plein
        1 - temps_partiel
        2 - forfait_heures_semaines
        3 - forfait_heures_mois
        4 - forfait_heures_annee
        5 - forfait_jours_annee
        6 - sans_objet
    à partir de la variables tppred (Temps de travail dans l'emploi principal)
        0 - Sans objet (ACTOP='2') ou non renseigné principal
        1 - Temps complet
        2 - Temps partiel
    qui doit être construite à partir de tpp
        0 - Sans objet (ACTOP='2') ou non renseigné
        1 - A temps complet
        2 - A temps partiel
        3 - Sans objet (pour les personnes non salariées qui estiment que cette question ne
            s'applique pas à elles)
    et de duhab
        1 - Temps partiel de moins de 15 heures
        2 - Temps partiel de 15 à 29 heures
        3 - Temps partiel de 30 heures ou plus
        4 - Temps complet de moins de 30 heures
        5 - Temps complet de 30 à 34 heures
        6 - Temps complet de 35 à 39 heures
        7 - Temps complet de 40 heures ou plus
        9 - Pas d'horaire habituel ou horaire habituel non déclaré
    TODO: utiliser la variable forfait
    """
    assert individus.tppred.isin(range(3)).all(), \
        'tppred values {} should be in [0, 1, 2]'
    individus['contrat_de_travail'] = 6  # sans objet
    individus.loc[individus.activite == 0, 'contrat_de_travail'] = (individus.tppred - 1)
    assert individus.contrat_de_travail.isin([0, 1, 6]).all()
    assert (individus.query('activite == 0').contrat_de_travail.isin([0, 1])).all()
    print individus.groupby('activite')['contrat_de_travail'].value_counts(dropna = False)
    assert (individus.query('activite != 0').contrat_de_travail == 6).all()


def create_effectif_entreprise_variable(individus):
    """
    Création de la variable effectif_entreprise
    à partir de la variable nbsala qui prend les valeurs suivantes:
        0 - Non pertinent
        1 - Aucun salarié
        2 - 1 ou 4 salariés
        3 - 5 à 9 salariés
        4 - 10 à 19 salariés
        5 - 20 à 49 salariés
        6 - 50 à 199 salariés
        7 - 200 à 499 salariés
        8 - 500 à 999 salariés
        9 - 1000 salariés ou plus
        99 - Ne sait pas
    """

    assert individus.nbsala.isin(range(0, 10) + [99]).all(), \
        "nbsala n'est pas toujours dans l'intervalle [0, 9] ou 99 \n{}".format(
            individus.nbsala.value_counts())
    individus['effectif_entreprise'] = np.select(
        [0, 1, 5, 10, 20, 50, 200, 500, 1000],
        [
            individus.nbsala.isin([0, 1]),  # 0
            individus.nbsala == 2,  # 1
            individus.nbsala == 3,  # 5
            individus.nbsala == 4,  # 10
            individus.nbsala == 5,  # 20
            (individus.nbsala == 6) | (individus.nbsala == 99),  # 50
            individus.nbsala == 7,  # 200
            individus.nbsala == 8,  # 500
            individus.nbsala == 9,  # 1000
            ]
        )

    assert individus.effectif_entreprise.isin([0, 1, 5, 10, 20, 50, 200, 500, 1000]).all(), \
        "effectif_entreprise n'est pas toujours dans [0, 1, 5, 10, 20, 50, 200, 500, 1000] \n{}".format(
            individus.effectif_entreprise.value_counts())


def create_revenus_variables(individus):
    """
    Création des variables:
        chomage_imposable,
        pensions_alimentaires_percues,
        rag,
        retraite_imposable,
        ric,
        rnc,
        salaire_imposable,
    """

    old_by_new_variables = {
        'chomage_i': 'chomage_net',
        'pens_alim_recue_i': 'pensions_alimentaires_percues',
        'rag_i': 'rag_net',
        'retraites_i': 'retraite_net',
        'ric_i': 'ric_net',
        'rnc_i': 'rnc_net',
        'salaires_i': 'salaire_net',
        }
    for variable in old_by_new_variables.keys():
        assert variable in individus.columns.tolist(), "La variable {} n'est pas présente".format(variable)

    individus.rename(
        columns = old_by_new_variables,
        inplace = True,
        )

    for variable in old_by_new_variables.values():
        if (individus[variable] < 0).any():

            negatives_values = individus[variable].value_counts().loc[individus[variable].value_counts().index < 0]
            log.info("La variable {} contient {} valeurs négatives\n {}".format(
                variable,
                negatives_values.sum(),
                negatives_values,
                )
            )

    imposable_by_components = {
        'chomage_imposable': ['chomage_net', 'csg_nd_crds_cho_i'],
        'rag': ['rag_net', 'csg_nd_crds_rag_i'],
        'retraite_imposable': ['retraite_net', 'csg_nd_crds_ret_i'],
        'ric': ['ric_net', 'csg_nd_crds_ric_i'],
        'rnc': ['rnc_net', 'csg_nd_crds_rnc_i'],
        'salaire_imposable': ['salaire_net', 'csg_nd_crds_sal_i'],
        }
    for imposable, components in imposable_by_components.iteritems():
        individus[imposable] = sum(individus[component] for component in components)

    individus['chomage_brut'] = individus.csgchod_i + individus.chomage_imposable
    individus['retraite_brute'] = individus.csgrstd_i + individus.retraite_imposable
    #
    # csg des revenus de replacement
    # 0 - Non renseigné/non pertinent
    # 1 - Exonéré
    # 2 - Taux réduit
    # 3 - Taux plein
    taux = pd.concat(
        [
            individus.csgrstd_i / individus.retraite_brute,
            individus.csgchod_i / individus.chomage_brut,
        ],
        axis=1
        ).max(axis = 1)
    taux.loc[(0 < taux) & (taux < .1)].hist(bins = 100)
    individus['taux_csg_remplacement'] = np.select(
        [
            taux.isnull(),
            taux.notnull() & (taux < 0.021),
            taux.notnull() & (taux > 0.021) & (taux < 0.0407),
            taux.notnull() & (taux > 0.0407)
            ],
        [0, 1, 2, 3]
        )
    assert individus.taux_csg_remplacement.isin(range(4)).all()


def todo_create(individus):
    log.info(u"    6.3 : variable txtppb")
    individus.loc[individus.txtppb.isnull(), 'txtppb'] = 0
    assert individus.txtppb.notnull().all()
    log.info("Valeurs prises par la variable txtppb \n {}".format(
        individus['txtppb'].value_counts(dropna = False)))


if __name__ == '__main__':
    import sys
    logging.basicConfig(level = logging.INFO, stream = sys.stdout)
    # logging.basicConfig(level = logging.INFO,  filename = 'step_03.log', filemode = 'w')
    year = 2012
    build_variables_individuelles(year = year)

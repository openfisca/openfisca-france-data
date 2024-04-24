import logging
import numpy as np
import pandas as pd

from openfisca_core import periods
from openfisca_france_data import select_to_match_target
from openfisca_france_data.common import (
    create_salaire_de_base,
    create_traitement_indiciaire_brut,
    )
from openfisca_france_data import openfisca_france_tax_benefit_system
from openfisca_france_data.smic import (
    smic_annuel_net_by_year,
    smic_annuel_imposable_by_year,
    )
from openfisca_france_data.utils import assert_dtype
from openfisca_survey_manager.temporary import temporary_store_decorator

log = logging.getLogger(__name__)


@temporary_store_decorator(file_name = 'erfs_fpr')
def build_variables_individuelles(temporary_store = None, year = None):
    """Création des variables individuelles."""

    assert temporary_store is not None
    assert year is not None

    individus = temporary_store['individus_{}_post_01'.format(year)]

    openfisca_by_erfs_variable = {
        'chomage_i': 'chomage_imposable',
        'pens_alim_recue_i': 'pensions_alimentaires_percues',
        'pens_invalidite_i': 'pensions_invalidite',
        'rag_i': 'rag',
        'retraites_i': 'retraite_imposable',
        'ric_i': 'ric',
        'rnc_i': 'rnc',
        'salaires_i': 'salaire_imposable',
        }

    for variable in openfisca_by_erfs_variable.keys():
        assert variable in individus.columns.tolist(), "La variable {} n'est pas présente".format(variable)

    individus.rename(
        columns = openfisca_by_erfs_variable,
        inplace = True,
        )


    individus['rpns_imposables'] = individus['rag'] + individus['ric'] + individus['rnc']

    create_variables_individuelles(individus, year)
    assert 'salaire_de_base' in individus.columns , 'salaire de base not in individus'
    assert 'traitement_indiciaire_brut' in individus.columns , 'traitement indiciaire brut not in individus'
    assert 'primes_fonction_publique' in individus.columns , 'primes fonction publique not in individus'
    temporary_store['individus_{}'.format(year)] = individus
    return individus


# helpers

def create_variables_individuelles(individus, year, survey_year = None, revenu_type = 'imposable'):
    """Création des variables individuelles."""
    period = periods.period(year)
    tax_benefit_system = openfisca_france_tax_benefit_system

    # variables démographiques
    create_ages(individus, year)
    create_date_naissance(individus, age_variable = None, annee_naissance_variable = 'naia', mois_naissance = 'naim',
         year = year)
    # Base pour constituer les familles, foyers, etc.
    create_statut_matrimonial(individus)

    # variable d'activite
    create_activite(individus)
    create_contrat_de_travail(individus, period = period, salaire_type = revenu_type)
    create_categorie_salarie(individus, period = period, survey_year = survey_year)
    create_categorie_non_salarie(individus)
    # inversion des revenus pour retrouver le brut
    # pour les revenus de remplacement on a la csg et la crds dans l'erfs-fpr donc on peut avoir le brut directement
    create_revenus_remplacement_bruts(individus)
    # On n'a pas le salaire et le traitement_indiciaire brut, on doit l'inverser
    # comme on a la crds et la csg non déductible on recalcule l'imposable puis on inverse l'imposable pour avoir le brut
    #individus['salaire_imposable'] = individus.salaire_net + individus.csg_nd_crds_sal_i
    create_salaire_de_base(
        individus,
        period = period,
        revenu_type = revenu_type,
        tax_benefit_system = tax_benefit_system,
        )
    create_traitement_indiciaire_brut(
        individus,
        period = period,
        revenu_type = revenu_type,
        tax_benefit_system = tax_benefit_system,
        )
    create_traitement_indiciaire_brut(
        individus,
        period = period,
        revenu_type = revenu_type,
        tax_benefit_system = tax_benefit_system)

    # Pour les cotisations patronales qui varient avec la taille de l'entreprise'
    create_effectif_entreprise(individus, period = period, survey_year = survey_year)

    return individus


def create_activite(individus):
    """Création de la variable activite.

    0 = Actif occupé
    1 = Chômeur
    2 = Étudiant, élève
    3 = Retraité
    4 = Autre inactif
    """
    create_actrec(individus)

    individus['activite'] = np.nan
    individus.loc[individus.actrec <= 3, 'activite'] = 0
    individus.loc[individus.actrec == 4, 'activite'] = 1
    individus.loc[individus.actrec == 5, 'activite'] = 2
    individus.loc[individus.actrec == 7, 'activite'] = 3
    individus.loc[individus.actrec == 8, 'activite'] = 4
    individus.loc[(individus.age <= 13) | (individus.actrec == 9), 'activite'] = 2
    message = "Valeurs prises par la variable activité \n {}".format(individus['activite'].value_counts(dropna = False))
    assert individus.activite.notnull().all(), message
    assert individus.activite.isin(range(5)).all(), message


def create_actrec(individus):
    """Création de la variables actrec.

    acterc pour activité recodée comme preconisé par l'INSEE p84 du guide méthodologique de l'ERFS
    """
    assert "actrec" not in individus.columns
    individus["actrec"] = np.nan
    acteu = 'act' if 'act' in individus else 'acteu'
    # Attention : Pas de 6, la variable recodée de l'INSEE (voit p84 du guide methodo), ici \
    # la même nomenclature à été adopée
    # 3: contrat a durée déterminée
    individus.loc[individus[acteu]== 1, 'actrec'] = 3
    # 8: femme (homme) au foyer, autre inactif
    individus.loc[individus[acteu] == 3, 'actrec'] = 8
    # 1: actif occupé non salarié
    filter1 = (individus[acteu] == 1) & (individus.stc.isin([1, 3]))  # actifs occupés non salariés à son compte
    individus.loc[filter1, 'actrec'] = 1                             # ou pour un membre de sa famille
    # 2: salarié pour une durée non limitée
    filter2 = (individus[acteu] == 1) & (((individus.stc == 2) & (individus.contra == 1)) | (individus.titc == 2))
    individus.loc[filter2, 'actrec'] = 2
    # 4: au chomage
    filter4 = (individus[acteu] == 2) | ((individus[acteu] == 3) & (individus.mrec == 1))
    individus.loc[filter4, 'actrec'] = 4
    # 5: élève étudiant , stagiaire non rémunéré
    filter5 = (individus[acteu] == 3) & ((individus.forter == 2) | (individus.rstg == 1))
    individus.loc[filter5, 'actrec'] = 5
    # 7: retraité, préretraité, retiré des affaires unchecked
    try: # cas >= 2014, evite de ramener l'année dans la fonction
        filter7 = (individus[acteu] == 3) & ((individus.ret == 1))
    except Exception:
        pass
    try: # cas 2004 - 2013
        filter7 = (individus[acteu] == 3) & ((individus.retrai == 1) | (individus.retrai == 2))
    except Exception: # cas 1996 - 2003
        cstot = 'dcstot' if 'dcstot' in individus else 'cstotr'
        filter7 = (individus[acteu] == 3) & ((individus[cstot] == 7))

    individus.loc[filter7, 'actrec'] = 7
    # 9: probablement enfants de - de 16 ans TODO: check that fact in database and questionnaire
    individus.loc[individus[acteu] == 0, 'actrec'] = 9

    assert individus.actrec.notnull().all()
    individus.actrec = individus.actrec.astype("int8")
    assert_dtype(individus.actrec, "int8")

    assert (individus.actrec != 6).all(), 'actrec ne peut pas être égale à 6'
    assert individus.actrec.isin(range(1, 10)).all(), 'actrec values are outside the interval [1, 9]'


def create_ages(individus, year = None):
    """Création des variables age et age_en_moi."""
    assert year is not None
    individus['age'] = year - individus.naia - 1
    individus['age_en_mois'] = 12 * individus.age + 12 - individus.naim  # TODO why 12 - naim

    for variable in ['age', 'age_en_mois']:
        assert individus[variable].notnull().all(), "Il y a {} entrées non renseignées pour la variable {}".format(
            individus[variable].notnull().sum(), variable)


def create_categorie_salarie(individus, period, survey_year = None):
    """Création de la variable categorie_salarie.

    Ses modalités sont;
      - "prive_non_cadre
      - "prive_cadre
      - "public_titulaire_etat
      - "public_titulaire_militaire
      - "public_titulaire_territoriale
      - "public_titulaire_hospitaliere
      - "public_non_titulaire
      - "non_pertinent"
    à partir des variables de l'eec' :
      - chpub :
          Variable déjà présente dans les fichiers antérieurs à 2013. Cependant, ses modalités ont été réordonnées ainsi :
          les modalités 1, 2, 3, 4, 5 et 6 de la variable CHPUB dans les fichiers antérieurs à 2013 correspondent à partir de
          2013 aux modalités respectives 3, 4, 5, 7, 2 et 1. Par ailleurs, une nouvelle modalité, Sécurité sociale (6) a été
          créée en 2013.
          A partir de (>=) 2013:
              1 Entreprise privée ou association
              2 Entreprise publique (EDF, La Poste, SNCF, etc.)
              3 État
              4 Collectivités territoriales
              5 Hôpitaux publics
              6 Sécurité sociale
              7 Particulier
          Avant (<) 2013:
              1 - Etat
              2 - Collectivités locales, HLM
              3 - Hôpitaux publics
              4 - Particulier
              5 - Entreprise publique (La Poste, EDF-GDF, etc.)
              6 - Entreprise privée, association

      - encadr : (encadrement de personnes)
          1 - Oui
          2 - Non

      - prosa (survey_year < 2013, voir qprc)
          1 Manoeuvre ou ouvrier spécialisé
          2 Ouvrier qualifié ou hautement qualifié
          3 Technicien
          4 Employé de bureau, de commerce, personnel de services, personnel de catégorie C ou D
          5 Agent de maîtrise, maîtrise administrative ou commerciale VRP (non cadre) personnel de catégorie B
          7 Ingénieur, cadre (à l'exception des directeurs généraux ou de ses adjoints directs) personnel de catégorie A
          8 Directeur général, adjoint direct
          9 Autre

      - qprc (survey_year >= 2013, voir prosa)
          Vide Sans objet (personnes non actives occupées, travailleurs informels et travailleurs intérimaires,
                          en activité temporaire ou d'appoint)
          1 Manoeuvre ou ouvrier spécialisé
          2 Ouvrier qualifié ou hautement qualifié, technicien d'atelier
          3 Technicien
          4 Employé de bureau, employé de commerce, personnel de services, personnel de catégorie C
          dans la fonction publique
          5 Agent de maîtrise, maîtrise administrative ou commerciale, VRP (non cadre), personnel de
          catégorie B dans la fonction publique
          6 Ingénieur, cadre (à l'exception des directeurs ou de leurs adjoints directs) personnel de
          catégorie A dans la fonction publique
          7 Directeur général, adjoint direct
          8 Autre
          9 Non renseigné

      - statut :
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

      - titc :
          1 - Elève fonctionnaire ou stagiaire
          2 - Agent titulaire
          3 - Contractuel

    """
    assert period is not None
    if survey_year is None:
        survey_year = period.start.year

    if survey_year >= 2013:
        log.debug(f"Using qprcent to infer chpub for year {survey_year}")
        chpub_replacement = {
            0: 0,
            3: 1,
            4: 2,
            5: 3,
            7: 4,
            2: 5,
            1: 6,
            6: 1,
            }
        individus['chpub'] = individus.chpub.map(chpub_replacement)

        log.debug('Using qprc to infer prosa for year {}'.format(survey_year))
        qprc_to_prosa = {
            0: 0,
            1: 1,
            2: 2,
            3: 3,
            4: 4,
            5: 5,
            6: 7,
            7: 8,
            8: 9,
            9: 5,  # On met les non renseignés en catégorie B
            }
        individus['prosa'] = individus.qprcent.map(qprc_to_prosa)
        # Actually prosa is there I don't need to change it further
    else:
        pass

    assert individus.chpub.isin(range(0, 7)).all(), \
        "chpub n'est pas toujours dans l'intervalle [0, 6]\n{}".format(individus.chpub.value_counts(dropna = False))

# N'existe qu'à partir de 2006 inclu
# On pourrait prendre csei mais elle ne recoupe pas bien prosa, ce serait vraiment
# une autre manière de déterminer la catégorie salariale.
    if 'encadr' in individus:
       individus.loc[individus.encadr == 0, 'encadr'] = 2
       assert individus.encadr.isin(range(1, 3)).all(), \
           "encadr n'est pas toujours dans l'intervalle [1, 2]\n{}".format(individus.encadr.value_counts(dropna = False))

    assert individus.prosa.isin(range(0, 10)).all(), \
        "prosa n'est pas toujours dans l'intervalle [0, 9]\n{}".format(individus.prosa.value_counts())

    statut_values = [0, 11, 12, 13, 21, 22, 33, 34, 35, 43, 44, 45, 99]
    assert individus.statut.isin(statut_values).all(), \
        "statut n'est pas toujours dans l'ensemble {} des valeurs antendues.\n{}".format(
            statut_values,
            individus.statut.value_counts(dropna = False)
            )

    if survey_year >= 2013:
        if individus.titc.isnull().any():
            individus.loc[
                individus.titc.isnull() & ~(individus.chpub.isin([3, 4, 5])),
                'titc'
            ] = 0
        assert individus.titc.isin(range(5)).all(), \
            "titc n'est pas toujours dans l'ensemble [0, 1, 2, 3, 4] des valeurs antendues.\n{}".format(
                individus.titc.value_counts(dropna = False)
                )
    else:
        assert individus.titc.isin(range(4)).all(), \
            "titc n'est pas toujours dans l'ensemble [0, 1, 2, 3] des valeurs antendues.\n{}".format(
                individus.titc.value_counts(dropna = False)
                )

    chpub = individus.chpub
    titc = individus.titc

    # encadrement
    assert 'cadre' not in individus.columns
    individus['cadre'] = False
    individus.loc[individus.prosa.isin([7, 8]), 'cadre'] = True
    if 'encadr' in individus: #N'existe qu'à partir de 2006 inclu
        individus.loc[(individus.prosa == 9) & (individus.encadr == 1), 'cadre'] = True
    cadre = (
        (individus.statut >= 21) & (individus.statut <= 35)  # En activité hors fonction publique
        & (chpub > 3) # Hors fonction publique mais entreprise publique
        & individus.cadre
        )
    del individus['cadre']

    # etat_stag = (chpub == 1) & (titc == 1)
    etat_titulaire = (chpub == 1) & ((titc == 2) | (titc == 1))
    etat_contractuel = (chpub == 1) & (titc == 3)

    militaire = False  # TODO:

    # collect_stag = (chpub==2) & (titc == 1)
    collectivites_locales_titulaire = (chpub == 2) & ((titc == 2) | (titc == 1))
    collectivites_locales_contractuel = (chpub == 2) & (titc == 3)

    # hosp_stag = (chpub==2)*(titc == 1)
    hopital_titulaire = (chpub == 3) & ((titc == 2) | (titc == 1))
    hopital_contractuel = (chpub == 3) & (titc == 3)
    contractuel = collectivites_locales_contractuel | hopital_contractuel | etat_contractuel

    if 'salaire_net' in individus and (individus['salaire_net'] > 0).any():
        actif_occupe = individus['salaire_net'] > 0
    elif 'salaire_imposable' in individus and (individus['salaire_imposable'] > 0).any():
        actif_occupe = individus['salaire_imposable'] > 0
    else:
        assert False, u'Pas de variable de salaire disponible non nuelle pour déterminer si un actif est occupé'

    #   TODO: may use something like this but to be improved and tested
    #    individus['categorie_salarie'] = np.select(
    #         [non_cadre, cadre, etat_titulaire, militaire, collectivites_locales_titulaire, hopital_titulaire,
    #               contractuel, non_pertinent]  # Choice list
    #         [0, 1, 2, 3, 4, 5, 6, 7],  # Condlist
    #         )

    individus['categorie_salarie'] = actif_occupe * (
        0 +
        1 * cadre +
        2 * etat_titulaire +
        3 * militaire +
        4 * collectivites_locales_titulaire +
        5 * hopital_titulaire +
        6 * contractuel
        ) + np.logical_not(actif_occupe) * 7

    log.debug('Les valeurs de categorie_salarie sont: \n {}'.format(
        individus['categorie_salarie'].value_counts(dropna = False)))
    assert individus['categorie_salarie'].isin(range(8)).all(), \
        "categorie_salarie n'est pas toujours dans l'intervalle [0, 7]\n{}".format(
            individus.categorie_salarie.value_counts(dropna = False))


def create_categorie_non_salarie(individus):
    """Création de la variable categorie_salarie.

    Ses modalités sont:
      - "non_pertinent
      - "artisan
      - "commercant
      - "profession_liberale
    à partir des variables de l'eec' :
      - cstot
        - 00 Non renseigné (pour les actifs)
        - 11 Agriculteurs sur petite exploitation
        - 12 Agriculteurs sur moyenne exploitation
        - 13 Agriculteurs sur grande exploitation
        - 21 Artisans
        - 22 Commerçants et assimilés
        - 23 Chefs d'entreprise de 10 salariés ou plus
        - 31 Professions libérales
        - 33 Cadres de la fonction publique
        - 34 Professeurs, professions scientifiques
        - 35 Professions de l'information, des arts et des spectacles
        - 37 Cadres administratifs et commerciaux d'entreprise
        - 38 Ingénieurs et cadres techniques d'entreprise
        - 42 Professeurs des écoles, instituteurs et assimilés
        - 43 Professions intermédiaires de la santé et du travail social
        - 44 Clergé, religieux
        - 45 Professions intermédiaires administratives de la fonction publique
        - 46 Professions intermédiaires administratives et commerciales des entreprises
        - 47 Techniciens
        - 48 Contremaîtres, agents de maîtrise
        - 52 Employés civils et agents de service de la fonction publique
        - 53 Policiers et militaires
        - 54 Employés administratifs d'entreprise
        - 55 Employés de commerce
        - 56 Personnels des services directs aux particuliers
        - 62 Ouvriers qualifiés de type industriel
        - 63 Ouvriers qualifiés de type artisanal
        - 64 Chauffeurs
        - 65 Ouvriers qualifiés de la manutention, du magasinage et du transport
        - 67 Ouvriers non qualifiés de type industriel
        - 68 Ouvriers non qualifiés de type artisanal
        - 69 Ouvriers agricoles
        - 71 Anciens agriculteurs exploitants
        - 72 Anciens artisans, commerçants, chefs d'entreprise
        - 74 Anciens cadres
        - 75 Anciennes professions intermédiaires
        - 77 Anciens employés
        - 78 Anciens ouvriers
        - 81 Chômeurs n'ayant jamais travaillé
        - 83 Militaires du contingent
        - 84 Elèves, étudiants
        - 85 Personnes diverses sans activité professionnelle de moins de 60 ans (sauf retraités)
        - 86 Personnes diverses sans activité professionnelle de 60 ans et plus (sauf retraités)
    """
    assert individus.cstot.notnull().all()
    if not pd.api.types.is_numeric_dtype(individus.cstot):
        individus.replace(
            {
                'cstot' : {'': '0', '00': '0'}
                },
            inplace = True
            )

    individus['cstot'] = individus.cstot.astype('int')
    assert set(individus.cstot.unique()) < set([
        0,
        11, 12, 13,
        21, 22, 23,
        31, 33, 34, 35, 37, 38,
        42, 43, 44, 45, 46, 47, 48,
        52, 53, 54, 55, 56,
        62, 63, 64, 65, 67, 68, 69,
        71, 72, 74, 75, 77, 78,
        81, 83, 84, 85, 86,
        ])

    agriculteur = individus.cstot.isin([11, 12, 13])
    artisan = individus.cstot.isin([21])
    commercant = individus.cstot.isin([22])
    chef_entreprise = individus.cstot.isin([23])
    profession_liberale = individus.cstot.isin([31])
    individus['categorie_non_salarie'] = 0
    individus.loc[
        agriculteur | artisan,
        'categorie_non_salarie'
        ] = 1
    individus.loc[
        commercant | chef_entreprise,
        'categorie_non_salarie'
        ] = 2
    individus.loc[
        profession_liberale,
        'categorie_non_salarie'
        ] = 3
    #fix un peu crade : cstot ne semble pas recouvrir tout le champ des personnes qui ont du rpns
    # on met par défaut ces gens là en chef d'entreprise
    individus.loc[
        ((individus['rpns_imposables'] != 0) & (individus['categorie_non_salarie'] == 0)),
        'categorie_non_salarie'
        ] = 2


def create_contrat_de_travail(individus, period, salaire_type = 'imposable'):
    """Création de la variable contrat_de_travail et heure_remunerees_volume.

    Ses modliatés sont:
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
    On utilise également hcc pour déterminer le nombre d'heures
    TODO: utiliser la variable forfait
    """
    if not isinstance(period, periods.Period):
        period = periods.period(period)

    assert salaire_type in ['net', 'imposable']

    if ((individus.hhc.dtype != 'float') & (individus.hhc.dtype != 'float32')):
        individus.loc[individus.hhc == "", "hhc"] = np.nan
        individus.hhc = individus.hhc.astype(float)
    individus.loc[individus.hhc <= 0.01 , "hhc"] = np.nan

    assert ((individus.hhc > 0) | individus.hhc.isnull()).all()

    assert individus.tppred.isin(range(3)).all(), \
        'tppred values {} should be in [0, 1, 2]'.format(individus.tppred.unique())

    assert (
        individus.duhab.isin(range(10)) & (individus.duhab != 8)
        ).all(), 'duhab values {} should be in [0, 1, 2, 3, 4, 5, 6, 7, 9]'.format(individus.duhab.unique())

    individus['contrat_de_travail'] = 6  # sans objet par défaut
    if salaire_type == 'net':
        assert (individus.query('salaire_net == 0').contrat_de_travail == 6).all()
        log.debug('Salaire retenu: {}'.format('salaire_net'))
        individus['salaire'] = individus.salaire_net.copy()
        smic = smic_annuel_net_by_year[period.start.year]

    elif salaire_type == 'imposable':
        individus['salaire_imposable'] = individus.salaire_imposable.fillna(0)
        assert (individus.query('salaire_imposable == 0').contrat_de_travail == 6).all()
        log.debug('Salaire retenu: {}'.format('salaire_imposable'))
        individus['salaire'] = individus.salaire_imposable.copy()
        smic = smic_annuel_imposable_by_year[period.start.year]

    if period.unit == 'month':
        smic = period.size * smic / 12

    # Etape préliminaire : construction d'une variable pour avoir une estimation de la part de l'année connue en emploi.
    # l'idée est d'utiliser les variables sp00-sp12 qui décrivent la situation principale pour chaque mois, du mois de l'enquête (sp00) à 12 mois en arrièvre (sp12).
    # Cela permet de compenser le fait que sinon on ne regarde la situation de l'emploi que pour la semaine de référence alors qu'on a des revenus annuels.

    # d abord on recupere le mois de l'enquete
    individus['mois_enquete'] = [int(str(i)[4:6]) for i in individus.datdeb]
    assert (individus.mois_enquete.isin(range(9, 13))).all()

    # # on ne prend que les mois de l'année en cours donc on n'a pas le même nombre de mois connus selon le mois de l'enquête

    individus['nb_mois_salariat_annee'] = 0
    for i in ["00", "01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11"]:
        individus['nb_mois_salariat_annee'] = individus.nb_mois_salariat_annee + np.where(int(i) < individus['mois_enquete'], np.where((individus[f"sp{i}"] == 1), 1, 0), 0)
        individus['nb_mois_salariat_annee'] = individus.nb_mois_salariat_annee + np.where(int(i) < individus['mois_enquete'], np.where((individus[f"sp{i}"] == 2), 1, 0), 0)

    # # normalement sp == 2 c'est de l'emploi non salarié mais possible que ce soit des statuts micro ou autre imposé dans assimilé salaire donc qu'on voit en salaire
    # # si sp est nan un mois donnée, le mois est considéré comme non travaillé

    individus['part_salariat_annee_connue'] = individus['nb_mois_salariat_annee'] / individus['mois_enquete']
    individus['part_salariat_annee_connue'] = np.where(individus['part_salariat_annee_connue'] == 0, 1, individus['part_salariat_annee_connue'])
    # s'il n'y a aucun mois travaillé dans l'année on met à 1 comme ça on ne l'utilise pas


    # 0 On élimine les individus avec un salaire_net nul des salariés
    # 1. utilisation de tppred et durhab
    # 1.1  temps_plein
    individus.query('tppred == 1').duhab.value_counts(dropna = False)
    assert (individus.query('tppred == 1').duhab >= 4).all()
    individus.loc[
        (individus.salaire > 0) & (
            (individus.tppred == 1) | (individus.duhab.isin(range(4, 8)))
            ),
        'contrat_de_travail'
        ] = 0
    assert (individus.query('salaire == 0').contrat_de_travail == 6).all()
    # 1.2 temps partiel
    assert (individus.query('tppred == 2').duhab.isin([1, 2, 3, 9])).all()
    individus.loc[
        (individus.salaire > 0) & (
            (individus.tppred == 2) | (individus.duhab.isin(range(1, 4)))
            ),
        'contrat_de_travail'
        ] = 1

    # on met à temps partiel les personnes qui se déclarent en temps plein au moment de l'enquète mais qui ont des périodes d'inactivité dans l'année
    passage_temps_plein_temps_partiel = (
        (individus.contrat_de_travail == 0) &
        (individus.salaire > 0) &
        (individus.part_salariat_annee_connue < 1)
    )
    individus.loc[passage_temps_plein_temps_partiel, 'contrat_de_travail'] = 1
    assert (individus.query('salaire == 0').contrat_de_travail == 6).all()
    assert (individus.query('contrat_de_travail == 0').part_salariat_annee_connue == 1).all()
    # 2. On traite les salaires horaires inféreurs au SMIC
    # 2.1 temps plein
    temps_plein = individus.query('(contrat_de_travail == 0) & (salaire > 0)')
    # (temps_plein.salaire > smic).value_counts()
    # temps_plein.query('salaire < 15000').salaire.hist()
    individus['heures_remunerees_volume'] = 0
    # On bascule à temps partiel et on réajuste les heures des temps plein qui ne touche pas le smic
    temps_plein_sous_smic = (
        (individus.contrat_de_travail == 0) &
        (individus.salaire > 0) &
        (individus.salaire < smic)
        )

    assert (individus.loc[temps_plein_sous_smic].part_salariat_annee_connue == 1).all()
    # il n'y a bien que des individus qu'on a pas pu mettre à temps partiel du fait de la part salariat dans l'année connue

    individus.loc[
        temps_plein_sous_smic,
        'contrat_de_travail'] = 1
    individus.loc[
        temps_plein_sous_smic,
        'heures_remunerees_volume'] = individus.loc[
            temps_plein_sous_smic,
            'salaire'
            ] / smic * 35
    assert (individus.loc[temps_plein_sous_smic, 'heures_remunerees_volume'] < 35).all()
    assert (individus.loc[temps_plein_sous_smic, 'heures_remunerees_volume'] > 0).all()
    assert (individus.query('salaire == 0').contrat_de_travail == 6).all()
    del temps_plein, temps_plein_sous_smic

    # 2.2 Pour les temps partiel on prends les heures hhc
    individus.loc[(individus.hhc > 35) & (individus.hhc.notnull()) & (individus.contrat_de_travail == 1),'hhc'] = 35
    individus.loc[(passage_temps_plein_temps_partiel) & (individus.hhc.isnull()), 'hhc'] = 35
    del passage_temps_plein_temps_partiel
    # on met 35h aux individus qui étaient à temps plein et qu'on a basculé en temps partiel pour la part salarié dans l'année

    # On vérfie que celles qu'on a créées jusqu'ici sont correctes
    assert (individus.query('salaire == 0').contrat_de_travail == 6).all()
    assert (individus.query('(contrat_de_travail == 1) & (salaire > 0)').heures_remunerees_volume < 35).all()

    axes = (individus.query('(contrat_de_travail == 1) & (salaire > 0)').hhc).hist(bins=100)
    axes.set_title("Heures (hhc)")
    # individus.query('(contrat_de_travail == 1) & (salaire > 0)').hhc.isnull().sum() = 489
    # 2.2.1 On abaisse le nombre d'heures pour que les gens touchent au moins le smic horaire
    temps_partiel = (individus.contrat_de_travail == 1) & (individus.salaire > 0)
    moins_que_smic_horaire_hhc = (
        ((individus.salaire / (individus.hhc * individus.part_salariat_annee_connue)) < (smic / 35)) # on adapte le nombre d'heure en fonction de la part travaillée observée dans l'année
        )
    hhc_positif = (individus.hhc.notnull() & (individus.hhc > 0))
    # Si on dispose de la variable hhc on l'utilise
    # Si moins que le SMIC on met au SMIC
    individus.loc[
        temps_partiel & moins_que_smic_horaire_hhc & hhc_positif,
        'heures_remunerees_volume'
        ] = individus.loc[
            temps_partiel & moins_que_smic_horaire_hhc & hhc_positif,
            'salaire'
            ] / smic * 35
    # Sinon on met le nombre d'heures renseignées au proratat du temps de travail dans l'année
    individus.loc[
        temps_partiel & (~moins_que_smic_horaire_hhc) & hhc_positif,
        'heures_remunerees_volume'
        ] = individus.loc[
            temps_partiel & (~moins_que_smic_horaire_hhc) & hhc_positif,
            'hhc'
            ] * individus.loc[
            temps_partiel & (~moins_que_smic_horaire_hhc) & hhc_positif,
            'part_salariat_annee_connue'
            ] # on adapte le nombre d'heure en fonction de la part travaillée observée dans l'année

    assert (individus.loc[temps_partiel & moins_que_smic_horaire_hhc & hhc_positif, 'heures_remunerees_volume'] < 35).all()
    assert (individus.loc[temps_partiel & moins_que_smic_horaire_hhc & hhc_positif, 'heures_remunerees_volume'] > 0).all()
    assert (individus.loc[temps_partiel & (~moins_que_smic_horaire_hhc) & hhc_positif, 'heures_remunerees_volume'] <= 35).all()
    assert (individus.loc[temps_partiel & (~moins_que_smic_horaire_hhc) & hhc_positif, 'heures_remunerees_volume'] > 0).all()

    individus.loc[temps_partiel & (~moins_que_smic_horaire_hhc) & hhc_positif & (individus.heures_remunerees_volume == 35),'contrat_de_travail'] = 0
    individus.loc[temps_partiel & (~moins_que_smic_horaire_hhc) & hhc_positif & (individus.heures_remunerees_volume == 35),'heures_remunerees_volume'] = 0

    axes = (
        individus
        .loc[temps_partiel]
        .query('(contrat_de_travail == 1) & (salaire > 0)')
        .heures_remunerees_volume
        .hist(bins=100)
        )
    axes.set_title("Heures (heures_remunerees_volume)")
    # 2.2.2 Il reste à ajuster le nombre d'heures pour les salariés à temps partiel qui n'ont pas de hhc
    # et qui disposent de moins que le smic_horaire ou de les basculer en temps plein sinon
    moins_que_smic_horaire_sans_hhc = (individus.salaire < smic * (individus.part_salariat_annee_connue)) & individus.hhc.isnull()
    individus.loc[
        temps_partiel & moins_que_smic_horaire_sans_hhc,
        'heures_remunerees_volume'
        ] = individus.loc[
            temps_partiel & moins_que_smic_horaire_sans_hhc,
            'salaire'
            ] / smic * 35

    plus_que_smic_horaire_sans_hhc_temps_plein = (
        (individus.salaire >= smic * (individus.part_salariat_annee_connue)) &
        individus.hhc.isnull() &
        (individus.part_salariat_annee_connue == 1)
        )
    individus.loc[
        temps_partiel & plus_que_smic_horaire_sans_hhc_temps_plein,
        'contrat_de_travail'
        ] = 0
    individus.loc[
        temps_partiel & plus_que_smic_horaire_sans_hhc_temps_plein,
        'heures_remunerees_volume'
        ] = 0

    plus_que_smic_horaire_sans_hhc_temps_partiel = (
        (individus.salaire >= smic * (individus.part_salariat_annee_connue)) &
        individus.hhc.isnull() &
        (individus.part_salariat_annee_connue < 1)
        )
    individus.loc[
        temps_partiel & plus_que_smic_horaire_sans_hhc_temps_partiel,
        'heures_remunerees_volume'
        ] = 35 * individus.part_salariat_annee_connue

    # 2.2.3 On repasse en temps plein ceux qui ont plus de 35 heures par semaine
    temps_partiel_bascule_temps_plein = (
        temps_partiel &
        (individus.heures_remunerees_volume >= 35)
        )
    individus.loc[
        temps_partiel_bascule_temps_plein,
        'contrat_de_travail',
        ] = 0
    individus.loc[
        temps_partiel_bascule_temps_plein,
        'heures_remunerees_volume',
        ] = 0
    del temps_partiel, temps_partiel_bascule_temps_plein, moins_que_smic_horaire_hhc#, moins_que_smic_horaire_sans_hhc
    assert (individus.query('contrat_de_travail == 0').heures_remunerees_volume == 0).all()
    assert (individus.query('contrat_de_travail == 1').heures_remunerees_volume < 35).all()
    assert (individus.query('salaire == 0').contrat_de_travail == 6).all()
    assert (individus.query('contrat_de_travail == 6').heures_remunerees_volume == 0).all()
    # 2.3 On traite ceux qui ont un salaire mais pas de contrat de travail renseigné
    # (temps plein ou temps complet)
    salarie_sans_contrat_de_travail = (
        (individus.salaire > 0) &
        ~individus.contrat_de_travail.isin([0, 1])
        )
    # 2.3.1 On passe à temps plein ceux qui ont un salaire supérieur au SMIC annuel et qui ont travaillé toute l'année jusqu'à l'enquête
    individus.loc[
        salarie_sans_contrat_de_travail &
        (individus.salaire >= smic) &
        (individus.part_salariat_annee_connue == 1),
        'contrat_de_travail'
        ] = 0
    assert (individus.loc[
        salarie_sans_contrat_de_travail &
        (individus.salaire >= smic),
        'heures_remunerees_volume'
        ] == 0).all()
    # on passe à temps partiel ceux qui sont supérieur au smic mais qui ont une part travaillée inférieur à 1.
    # On leur attribut un nombre d'heure au proratat de la durée travaillée
    individus.loc[
        salarie_sans_contrat_de_travail &
        (individus.salaire >= smic * individus.part_salariat_annee_connue) &
        (individus.part_salariat_annee_connue < 1),
        'contrat_de_travail'
        ] = 1
    individus.loc[
        salarie_sans_contrat_de_travail &
        (individus.salaire >= smic * individus.part_salariat_annee_connue) &
        (individus.part_salariat_annee_connue < 1),
        'heures_remunerees_volume'
        ] = 35 * individus.part_salariat_annee_connue
    # 2.3.2 On passe à temps partiel ceux qui ont un salaire inférieur au SMIC annuel
    individus.loc[
        salarie_sans_contrat_de_travail &
        (individus.salaire < smic * individus.part_salariat_annee_connue),
        'contrat_de_travail'
        ] = 1
    individus.loc[
        salarie_sans_contrat_de_travail &
        (individus.salaire < smic * individus.part_salariat_annee_connue),
        'heures_remunerees_volume'
        ] = individus.loc[
            salarie_sans_contrat_de_travail &
            (individus.salaire < smic * individus.part_salariat_annee_connue),
            'salaire'
            ] / smic * 35
    # 2.3.3 On attribue des heures rémunérées aux individus à temps partiel qui ont un
    # salaire strictement positif mais un nombre d'heures travaillées nul
    salaire_sans_heures = (individus.contrat_de_travail == 1) & ~(individus.heures_remunerees_volume > 0)

    assert (individus.loc[salaire_sans_heures, 'salaire'] > 0).all()
    assert (individus.loc[salaire_sans_heures, 'duhab'] == 1).all()
    # Cela concerne peu de personnes qui ont par ailleurs duhab = 1 et un salaire supérieur au smic.
    # On leur attribue donc un nombre d'heures travaillées égal à 15.
    individus.loc[
        salaire_sans_heures &
        (individus.salaire > smic),
        'heures_remunerees_volume'] = 15
    #
    individus.query('salaire > 0').contrat_de_travail.value_counts(dropna = False)
    individus.query('salaire == 0').contrat_de_travail.value_counts(dropna = False)

    individus.loc[salarie_sans_contrat_de_travail, 'salaire'].min()
    individus.loc[salarie_sans_contrat_de_travail, 'salaire'].hist(bins = 1000)
    del salarie_sans_contrat_de_travail

    # On vérifie que l'on n'a pas fait d'erreurs
    assert (individus.salaire >= 0).all(), "Des salaires sont negatifs: {}".format(
            individus.loc[~(individus.salaire >= 0), 'salaire']
            )
    assert individus.contrat_de_travail.isin([0, 1, 6]).all()
    assert (individus.query('salaire > 0').contrat_de_travail.isin([0, 1])).all()
    assert (individus.query('salaire == 0').contrat_de_travail == 6).all()
    assert (individus.query('salaire == 0').heures_remunerees_volume == 0).all()
    assert (individus.query('contrat_de_travail in [0, 6]').heures_remunerees_volume == 0).all()
    assert (individus.query('contrat_de_travail == 1').heures_remunerees_volume < 35).all()
    assert (individus.heures_remunerees_volume >= 0).all()
    assert (individus.query('contrat_de_travail == 1').heures_remunerees_volume > 0).all(), \
        "Des heures des temps partiels ne sont pas strictement positives: {}".format(
            individus.query('contrat_de_travail == 1').loc[
                ~(individus.query('contrat_de_travail == 1').heures_remunerees_volume > 0),
                'heures_remunerees_volume'
                ]
            )

    # la variable heures_remunerees_volume est nombre d'heures par semaine. On ajuste selon la période
    period = periods.period(period)
    if period.unit == 'year':
        individus['heures_remunerees_volume'] = individus.heures_remunerees_volume * 52
    elif period.unit == 'month':
        if period.size == 1:
            individus['heures_remunerees_volume'] = individus.heures_remunerees_volume * 52 / 12
        elif period.size == 3:
            individus['heures_remunerees_volume'] = individus.heures_remunerees_volume * 52 / 4
        else:
            log.error('Wrong period {}. Should be month or year'.format(period))
            raise
    else:
        log.error('Wrong period {}. Should be month or year'.format(period))
        raise

     # On arrondit les heures supplémentaires à l'entier inférieur, et mon met 1 si en dessous de 1
    individus.loc[individus.contrat_de_travail == 1, 'heures_remunerees_volume'] = np.maximum(1,np.round(individus.loc[individus.contrat_de_travail == 1, 'heures_remunerees_volume']))

    del individus['salaire']

    return


def create_date_naissance(individus, age_variable = 'age', annee_naissance_variable = None, mois_naissance = None,
         year = None):
    """
    Création de la variable date_naissance à partir des variables age ou de l'année et du mois de naissance
    """
    assert year is not None
    assert bool(age_variable) != bool(annee_naissance_variable)  # xor

    random_state = np.random.RandomState(42)
    month_birth = 1 + random_state.randint(12, size = len(individus))
    day_birth = 1 + random_state.randint(28, size = len(individus))

    if age_variable is not None:
        assert age_variable in individus
        year_birth = (year - individus[age_variable]).astype(int)

    elif annee_naissance_variable is not None:
        year_birth = individus[annee_naissance_variable].astype(int)
        if mois_naissance is not None:
            month_birth = individus[mois_naissance].astype(int)

    # sometimes age is actually the year, fixing this by adding back year
    year_birth[year_birth < 1000] += year

    individus['date_naissance'] = pd.to_datetime(
        pd.DataFrame({
            'year': year_birth,
            'month': month_birth,
            'day': day_birth,
            })
        )


def create_effectif_entreprise(individus, period = None, survey_year = None):
    """Création de la variable effectif_entreprise.

    A partir de la variable nbsala qui prend les valeurs suivantes:
    Création de la variable effectif_entreprise à partir de la variable nbsala qui prend les valeurs suivantes:
    A partir de (>=) 2013
        0 Vide Sans objet ou non renseigné
        1 1 salarié
        2 2 salariés
        3 3 salariés
        4 4 salariés
        5 5 salariés
        6 6 salariés
        7 7 salariés
        8 8 salariés
        9 9 salariés
        10 10 à 49 salariés
        11 50 à 499 salariés
        12 500 salariés ou plus
        99 Ne sait pas
    Strictement avant (<) 2013
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
    assert period is not None
    if survey_year is None:
        survey_year = period.start.year

    if survey_year >= 2013:
        assert individus.nbsala.isin(list(range(0, 13)) + [99]).all(), \
            "nbsala n'est pas toujours dans l'intervalle [0, 12] ou 99 \n{}".format(
                individus.nbsala.value_counts(dropna = False))
        individus['effectif_entreprise'] = np.select( # condition_lits, choice_list
            [
                individus.nbsala == 0,  # 0
                individus.nbsala == 1,  # 1
                individus.nbsala == 2,  # 2
                individus.nbsala == 3,  # 3
                individus.nbsala == 4,  # 4
                individus.nbsala == 5,  # 5
                individus.nbsala == 6,  # 6
                individus.nbsala == 7,  # 7
                individus.nbsala == 8,  # 8
                individus.nbsala == 9,  # 9
                individus.nbsala == 10,  # 9
                (individus.nbsala == 11) | (individus.nbsala == 99),  # 9
                individus.nbsala == 12,  # 9
                ],
            [0, 1, 2, 3, 4, 5, 5, 7, 8, 9, 10, 50, 500],
            )
        assert individus.effectif_entreprise.isin([0, 1, 2, 3, 4, 5, 5, 7, 8, 9, 10, 50, 500]).all(), \
            "effectif_entreprise n'est pas toujours dans [0, 1, 5, 10, 20, 50, 200, 500, 1000] \n{}".format(
                individus.effectif_entreprise.value_counts(dropna = False))

    else:
        assert individus.nbsala.isin(list(range(0, 10)) + [99]).all(), \
            "nbsala n'est pas toujours dans l'intervalle [0, 9] ou 99 \n{}".format(
                individus.nbsala.value_counts(dropna = False))
        individus['effectif_entreprise'] = np.select(
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
                ],
            [0, 1, 5, 10, 20, 50, 200, 500, 1000],
            )

        assert individus.effectif_entreprise.isin([0, 1, 5, 10, 20, 50, 200, 500, 1000]).all(), \
            "effectif_entreprise n'est pas toujours dans [0, 1, 5, 10, 20, 50, 200, 500, 1000] \n{}".format(
                individus.effectif_entreprise.value_counts(dropna = False))
        log.debug('Effectif entreprise:\n{}'.format(
            individus.effectif_entreprise.value_counts(dropna = False)))


def create_revenus_remplacement_bruts(individus):
    """
    Reconstitution des variables de retraite et chomage brut à partir des variables nettes et des variables de csg et crds
    """

    # revenu_brut = revenu_net + csg_deductible + csg_non_deductible_crds
    individus['chomage_brut'] = individus.chomage_imposable + individus.csgchod_i #+ individus. csg_nd_crds_cho_i
    individus['retraite_brute'] =  individus.retraite_imposable + individus.csgrstd_i #+ individus.csg_nd_crds_ret_i


def create_statut_matrimonial(individus):
    """
    Création de la variable statut_marital qui prend les valeurs:
      1 - "Marié",
      2 - "Célibataire",
      3 - "Divorcé",
      4 - "Veuf",
      5 - "Pacsé",
      6 - "Jeune veuf"
    à partir de la variable matri qui prend les valeurs
      0 - sans objet (moins de 15 ans)
      1 - Célibataire
      2 - Marié(e) ou remarié(e)
      3 - Veuf(ve)
      4 - Divorcé(e)
    """
    assert individus.matri.isin(range(5)).all()

    individus['statut_marital'] = 2  # célibataire par défaut
    individus.loc[individus.matri == 2, 'statut_marital'] = 1  # marié(e)
    individus.loc[individus.matri == 3, 'statut_marital'] = 4  # veuf(ve)
    individus.loc[individus.matri == 4, 'statut_marital'] = 3  # divorcé(e)

    assert individus.statut_marital.isin(range(1, 7)).all()


def create_taux_csg_remplacement(individus, period, tax_benefit_system, sigma = (28.1) ** 2):
    assert 'revkire' in individus
    assert 'nbp' in individus
    if period.start.year < 2015:  # Should be an assert
        period = periods.period(2015)

    rfr = individus.revkire
    nbptr = individus.nbp / 100

    def compute_taux_csg_remplacement(rfr, nbptr):
        parameters = tax_benefit_system.get_parameters_at_instant(period.start)
        seuils = parameters.prelevements_sociaux.contributions_sociales.csg.remplacement.pensions_de_retraite_et_d_invalidite
        seuil_exoneration = seuils.seuil_de_rfr_1 + (nbptr - 1) * seuils.demi_part_suppl
        seuil_reduction = seuils.seuil_de_rfr_2 + (nbptr - 1) * seuils.demi_part_suppl
        taux_csg_remplacement = 0.0 * rfr
        taux_csg_remplacement = np.where(
            rfr <= seuil_exoneration,
            1,
            np.where(
                rfr <= seuil_reduction,
                2,
                3,
                )
            )

        return taux_csg_remplacement

    individus['rfr_special_csg_n'] = rfr
    individus['taux_csg_remplacement'] = compute_taux_csg_remplacement(rfr, nbptr)
    if sigma is not None:
        np.random.seed(42)
        rfr_n_1 = rfr + (individus.retraite_imposable > 0) * np.random.normal(
            scale = sigma, size = len(individus['taux_csg_remplacement'])
            )
    individus['rfr_special_csg_n_1'] = rfr_n_1
    individus['taux_csg_remplacement_n_1'] = compute_taux_csg_remplacement(rfr_n_1, nbptr)

    distribution = individus.groupby(['taux_csg_remplacement', 'taux_csg_remplacement_n_1'])['ponderation'].sum() / 1000
    log.debug("Distribution of taux_csg_remplacement (in thousands):\n", distribution)
    assert individus['taux_csg_remplacement_n_1'].isin(range(4)).all()
    assert individus['taux_csg_remplacement'].isin(range(4)).all()


def calibrate_categorie_salarie(individus, year = None, mass_by_categorie_salarie = None):
    assert mass_by_categorie_salarie is not None
    log.debug('Mass of salaries: ', mass_by_categorie_salarie)

    weight_individus = individus['ponderation'].values
    for rebalanced_categorie, target_mass in mass_by_categorie_salarie.items():
        categorie_salarie = individus['categorie_salarie'].values
        eligible = (
            (categorie_salarie == 0) | (categorie_salarie == rebalanced_categorie)
            )
        take = (categorie_salarie == rebalanced_categorie)
        log.info(
            """
initial take population: {}
initial eligible population: {}
target mass: {}""".format(
                (take * eligible * weight_individus).sum() / 1e6,
                (eligible * weight_individus).sum() / 1e6,
                target_mass / 1e6,
                ))
        selected = select_to_match_target(
            target_mass = target_mass,
            eligible = eligible,
            weights = weight_individus,
            take = take,
            seed = 9779972
            )
        log.debug("""
    final selected population: {}
    error: {} %
    """.format(
            (eligible * selected * weight_individus).sum() / 1e6,
            ((eligible * selected * weight_individus).sum() - target_mass) / target_mass * 100,
            ))
        individus.loc[selected, 'categorie_salarie'] = rebalanced_categorie
        log.debug(individus.groupby('categorie_salarie')['ponderation'].sum())
        seuil_salaire_imposable_mensuel = 2 * 3000
        individus.loc[
            (
                (individus.contrat_de_travail == 0)
                & (individus.categorie_salarie == 0)
                & (individus.salaire_imposable > 12 * seuil_salaire_imposable_mensuel)
                ),
            'categorie_salarie'
            ] = 1
        individus.loc[
            (
                (individus.contrat_de_travail == 1)
                & (individus.categorie_salarie == 0)
                & (individus.salaire_imposable  > (12 * seuil_salaire_imposable_mensuel) / (35 * 52) * individus.heures_remunerees_volume)
                ),
            'categorie_salarie'
            ] = 1


def todo_create(individus):
    txtppb = "txtppb" if "txtppb" in individus.columns else "txtppred"
    log.debug("6.3 : variable txtppb")
    individus.loc[individus.txtppb.isnull(), txtppb] = 0
    individus.loc[individus[txtppb] == 9, txtppb] = 0
    assert individus.txtppb.notnull().all()
    log.debug("Valeurs prises par la variable txtppb \n {}".format(
        individus[txtppb].value_counts(dropna = False)))


if __name__ == '__main__':

    import sys
    logging.basicConfig(level = logging.INFO, stream = sys.stdout)
    # logging.basicConfig(level = logging.INFO,  filename = 'step_03.log', filemode = 'w')
    year = 2014

    #    from openfisca_france_data.erfs_fpr.input_data_builder import step_01_preprocessing
    #    step_01_preprocessing.build_merged_dataframes(year = year)
    individus = build_variables_individuelles(year = year)

#from itertools import izip

from numpy import arange, array, floor, where
from numpy import minimum as min_
import pandas as pd
from pathlib import Path

from openfisca_france_data.model.base import *  # noqa
from openfisca_france_data import openfisca_france_data_location

class nbinde(Variable):
    value_type = int
    entity = Menage
    label = "Nombre d'individus dans le ménage. La valeur varie entre 1 et 6 pour 6 membres et plus."
    definition_period = YEAR

    def formula(menage, period, parameters):
        """
        Number of household members
        """

        age_en_mois_i = menage.members('age_en_mois', period)

        n1 = menage.sum(floor(age_en_mois_i) >= 0)

        return where(n1 >= 6, 6, n1)


def _ageq(age_en_mois):
    '''
    Calcule la tranche d'âge quinquennal
    moins de 25 ans : 0
    25 à 29 ans     : 1
    30 à 34 ans     : 2
    35 à 39 ans     : 3
    40 à 44 ans     : 4
    45 à 49 ans     : 5
    50 à 54 ans     : 6
    55 à 59 ans     : 7
    60 à 64 ans     : 8
    65 à 69 ans     : 9
    70 à 74 ans     :10
    75 à 79 ans     :11
    80 ans et plus  :12
    'ind'
    '''
    age = floor(age_en_mois / 12)
    tranche = array([(age >= ag) for ag in arange(25, 5, 81)]).sum(axis = 0)
    return tranche


def _nb_ageq0(self, age_en_mois_holder):
    '''
    Calcule le nombre d'individus dans chaque tranche d'âge quinquennal (voir ageq)
    'men'
    '''
    age_en_mois = self.split_by_roles(age_en_mois_holder)

    ag1 = 0
    nb = 0
    for agm in age_en_mois.itervalues():
        age = floor(agm / 12)
        nb += (ag1 <= age) & (age <= (ag1 + 4))
    return nb


class cohab(Variable):
    value_type = bool
    entity = Menage
    label = "Vie en couple"
    definition_period = YEAR

    def formula(menage, period, parameters):
        '''
        Indicatrice de vie en couple
        'men'
        '''

        return menage.nb_persons(role = Menage.CONJOINT) == 1


class act_cpl(Variable):
    is_period_size_independent = True
    value_type = int
    entity = Menage
    label = "Nombre d'actifs parmi la personne de référence du méange et son conjoint"
    definition_period = YEAR

    def formula(menage, period, parameters):
        '''
        Nombre d'actifs parmi la personne de référence et son conjoint
        'men'
        '''
        cohab = menage('cohab', period)

        return (
            1 * (menage.personne_de_reference('activite', period) <= 1) +
            1 * (menage.conjoint('activite', period) <= 1)
            ) * cohab


class act_enf(Variable):
    is_period_size_independent = True
    value_type = int
    entity = Menage
    label = "Nombre d'enfants actifs"
    definition_period = YEAR

    def formula(menage, period, parameters):
        '''
        Nombre de membres actifs du ménage autre que la personne de référence ou son conjoint
        'men'
        '''
        act_i = menage.members('activite', period)

        return menage.sum(1 * (act_i <= 1), role = Menage.ENFANT)


def _nb_act(act_cpl, act_enf):
    '''
    Nombre de membres actifs du ménage
    'men'
    '''
    return act_cpl + act_enf


# def _cplx(typmen15):
class cplx(Variable):
    value_type = bool
    entity = Menage
    label = "Indicatrice de ménage complexe. Un ménage est complexe si les personnes autres que la personne de référence ou son conjoint ne sont pas enfants."
    definition_period = YEAR

    def formula(menage, period, parameters):
        """
        Indicatrice de ménage complexe

        Un ménage est complexe si les personnes autres que la personne de référence ou son conjoint ne sont pas enfants.
        """

        individus = menage.members
        age_i = individus('age', period)

        is_enfant_plus_25 = individus.has_role(Famille.ENFANT) * (age_i > 25)
        is_not_pref = not_(individus.has_role(Menage.PERSONNE_DE_REFERENCE))
        is_demandeur = individus.has_role(Famille.DEMANDEUR)

        return menage.any(
            is_not_pref * is_demandeur + is_enfant_plus_25
            )



    # En fait on ne peut pas car on n'a les enfants qu'au sens des allocations familiales ...
    # return (typmen15 > 12)


class TypesMenage15(Enum):
    __order__ = 'inconnu personne_seule_active personne_seule_inactive famille_monoparentale_parent_actif famille_monoparentale_parent_inactif_enfant_actif famille_monoparentale_inactifs couple_sans_enfants_1_actif couple_sans_enfants_2_actifs couple_sans_enfants_inactifs couple_avec_enfants_1_actif couple_avec_enfants_2_actifs couple_avec_enfants_parents_inactifs_enfant_actif couple_avec_enfants_inactifs autres_1_actif autres_2_actifs autres_inactifs'  # Needed to preserve the order in Python 2
    inconnu = ""
    personne_seule_active = "Personne seule active"
    personne_seule_inactive = "Personne seule inactive"
    famille_monoparentale_parent_actif = "Familles monoparentales, parent actif"
    famille_monoparentale_parent_inactif_enfant_actif = "Familles monoparentales, parent inactif et au moins un enfant actif"
    famille_monoparentale_inactifs = "Familles monoparentales, tous inactifs"
    couple_sans_enfants_1_actif = "Couples sans enfant, 1 actif"
    couple_sans_enfants_2_actifs = "Couples sans enfant, 2 actifs"
    couple_sans_enfants_inactifs = "Couples sans enfant, tous inactifs"
    couple_avec_enfants_1_actif = "Couples avec enfant, 1 membre du couple actif"
    couple_avec_enfants_2_actifs = "Couples avec enfant, 2 membres du couple actif"
    couple_avec_enfants_parents_inactifs_enfant_actif = "Couples avec enfant, couple inactif et au moins un enfant actif"
    couple_avec_enfants_inactifs = "Couples avec enfant, tous inactifs"
    autres_1_actif = "Autres ménages, 1 actif"
    autres_2_actifs = "Autres ménages, 2 actifs ou plus"
    autres_inactifs = "Autres ménages, tous inactifs"


class typmen15(Variable):
    value_type = Enum
    possible_values = TypesMenage15
    default_value = TypesMenage15.inconnu
    entity = Menage
    label = "Type de ménage"
    definition_period = YEAR

    def formula(menage, period, parameters):
        '''
        Type de ménage en 15 modalités
        1 Personne seule active
        2 Personne seule inactive
        3 Familles monoparentales, parent actif
        4 Familles monoparentales, parent inactif et au moins un enfant actif
        5 Familles monoparentales, tous inactifs
        6 Couples sans enfant, 1 actif
        7 Couples sans enfant, 2 actifs
        8 Couples sans enfant, tous inactifs
        9 Couples avec enfant, 1 membre du couple actif
        10 Couples avec enfant, 2 membres du couple actif
        11 Couples avec enfant, couple inactif et au moins un enfant actif
        12 Couples avec enfant, tous inactifs
        13 Autres ménages, 1 actif
        14 Autres ménages, 2 actifs ou plus
        15 Autres ménages, tous inactifs
        'men'
        '''
        nbinde = menage('nbinde', period)
        cohab = menage('cohab', period)
        act_cpl = menage('act_cpl', period)
        cplx = menage('cplx', period)
        act_enf = menage('act_enf', period)

        res = 0 + (cplx == 0) * (
                1 * ((nbinde == 1) & (cohab == 0) & (act_cpl == 1)) +  # Personne seule active
                2 * ((nbinde == 1) & (cohab == 0) & (act_cpl == 0)) +  # Personne seule inactive
                3 * ((nbinde > 1) & (cohab == 0) & (act_cpl == 1)) +  # Familles monoparentales, parent actif
                4 * ((nbinde > 1) & (cohab == 0) & (act_cpl == 0) & (act_enf >= 1)) +  # Familles monoparentales, parent inactif et au moins un enfant actif
                5 * ((nbinde > 1) & (cohab == 0) & (act_cpl == 0) & (act_enf == 0)) +  # Familles monoparentales, tous inactifs
                6 * ((nbinde == 2) & (cohab == 1) & (act_cpl == 1)) +  # Couples sans enfant, 1 actif
                7 * ((nbinde == 2) & (cohab == 1) & (act_cpl == 2)) +  # Couples sans enfant, 2 actifs
                8 * ((nbinde == 2) & (cohab == 1) & (act_cpl == 0)) +  # Couples sans enfant, tous inactifs
                9 * ((nbinde > 2) & (cohab == 1) & (act_cpl == 1)) +  # Couples avec enfant, 1 membre du couple actif
                10 * ((nbinde > 2) & (cohab == 1) & (act_cpl == 2)) +  # Couples avec enfant, 2 membres du couple actif
                11 * ((nbinde > 2) & (cohab == 1) & (act_cpl == 0) & (act_enf >= 1)) +  # Couples avec enfant, couple inactif et au moins un enfant actif
                12 * ((nbinde > 2) & (cohab == 1) & (act_cpl == 0) & (act_enf == 0))  # Couples avec enfant, tous inactifs
                               ) + (cplx == 1) * (
                13 * (((act_cpl + act_enf) == 1)) +  # Autres ménages, 1 actif
                14 * (((act_cpl + act_enf) > 1)) +  # Autres ménages, 2 actifs ou plus
                15 * (((act_cpl + act_enf) == 0)))  # Autres ménages, tous inactifs

        # ratio = (( (typmen15!=res)).sum())/((typmen15!=0).sum())
        # ratio  2.7 % d'erreurs enfant non nés et erreur d'enfants
        return res

def create_dic_calage(year, base_year, liste_variable, base_initiale = None, **kwargs):
    dico_calage = dict()
    assert all(variable in ["age"] for variable in liste_variable), "A variable is asked to be calibrated, but no matching aggregate is implemented"
    if "age" in liste_variable:
        dico_calage = create_dic_age(year, base_year, dico_calage, base_initiale, **kwargs)
    return dico_calage

def create_dic_age(year, base_year, dico_calage, base_initiale):
    demographie_file = Path(
                openfisca_france_data_location,
                "openfisca_france_data",
                "assets",
                "aggregats",
                "demographie",
                "demographie_insee.csv"
                )
    df_demographie = pd.read_csv(demographie_file, skipfooter = 9, skiprows = 1, encoding_errors = 'replace', sep = ';', thousands = ".")
    df_demographie["age_calage"] = df_demographie[df_demographie.columns[0]].astype(int) # On passe par columns à cause du Â
    for annee in range(base_year, year + 1): # On limite à 100 l'age max, pour éviter l'absence de données
        df_demographie.loc[df_demographie["age_calage"] == 100, str(annee)] = sum(df_demographie[df_demographie["age_calage"] >= 100][str(annee)])
    df_demographie = df_demographie[df_demographie["age_calage"] <= 100]
    if base_initiale is None:
        dic_age = pd.Series(df_demographie[str(year)].values, index = df_demographie["age_calage"]).to_dict()
        dico_calage["age_calage"] = dic_age
        return dico_calage

    df_demographie["variation_totale"] = df_demographie[str(year)] / df_demographie[str(base_year)]

    base_initiale["age_calage"] = base_initiale["age_calage"].astype(int)
    base_initiale.loc[base_initiale["age_calage"] == 100, "N"] = sum(base_initiale[base_initiale["age_calage"] >= 100]["N"])
    base_initiale = base_initiale[base_initiale["age_calage"] <= 100]

    cible_finale = pd.merge(df_demographie, base_initiale, on = ("age_calage"), how = "inner")
    cible_finale["cible"] = round(cible_finale["N"] * cible_finale["variation_totale"])
    dic_age = pd.Series(cible_finale["cible"].values, index = cible_finale["age_calage"]).to_dict()
    dico_calage["age_calage"] = dic_age
    return dico_calage



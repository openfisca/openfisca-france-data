# -*- coding: utf-8 -*-


from __future__ import division

import inspect
import logging
import os
import pkg_resources

from numpy import (logical_not as not_, maximum as max_)
import pandas as pd

from openfisca_core import reforms
# from openfisca_core.formulas import set_input_divide_by_period

import openfisca_france

# Load input variables and output variables into entities
from .model import common, survey_variables  # noqa analysis:ignore
from .model.base import * # noqa  analysis:ignore


log = logging.getLogger(__name__)


def get_variables_from_module(module):
    variables = [
        getattr(module, item)
        for item in dir(module)
        if inspect.isclass(getattr(module, item))
        ]
    return [
        variable for variable in variables if issubclass(variable, Variable)
        ]


def get_variables_from_modules(modules):
    variables = list()
    for module in modules:
        variables.extend(get_variables_from_module(module))
    return variables


def impute_take_up(target_probability, eligible, weights, recourant_last_period, seed):
    """
    Compute a vector of boolean for take_up according a target probability accross eligble population
    """
    assert (target_probability >= 0) and (target_probability <= 1)
    if target_probability == 0:
        return eligible * False
    elif target_probability == 1:
        return eligible * True

    data = pd.DataFrame({
        'eligible': eligible,
        'weights': weights,
        'deja_recourant': recourant_last_period,
        })

    eligibles = data.loc[data.eligible == 1].copy()
    eligibles['recourant'] = eligibles.deja_recourant
    taux_recours_provisoire = eligibles.loc[eligibles.recourant].weights.sum() / eligibles.weights.sum()

    if target_probability > taux_recours_provisoire:
        adjusted_target_probability = (target_probability - taux_recours_provisoire) / (1 - taux_recours_provisoire)
        s_data = eligibles.loc[~eligibles.recourant].copy()
        s_data = s_data.sample(frac = adjusted_target_probability, replace = False, axis = 0, random_state = seed)
        eligibles.loc[eligibles.index.isin(s_data.index), 'recourant'] = True
        eligibles_recourants_indices = eligibles.query('eligible & recourant').index
        data['recourant'] = False
        data.loc[data.index.isin(eligibles_recourants_indices), 'recourant'] = True

    elif target_probability <= taux_recours_provisoire:
        adjusted_target_probability = 1 - target_probability / taux_recours_provisoire
        s_data = eligibles.loc[eligibles.recourant].copy()
        s_data = s_data.sample(frac = adjusted_target_probability, replace = False, axis = 0, random_state = seed)
        eligibles_non_recourant_indices = s_data.index
        data['recourant'] = data.deja_recourant & data.eligible
        data.loc[data.index.isin(eligibles_non_recourant_indices), 'recourant'] = False

    return data.recourant.values


variables = get_variables_from_modules([common, survey_variables])


class openfisca_france_data(reforms.Reform):

    def apply(self):
        for variable in variables:
            if variable == Variable:
                continue
            try:
                self.add_variable(variable)
            except AttributeError:
                self.update_variable(variable)

        neutralized_reductions = [
            'accult',
            'adhcga',
            'assvie',
            'cappme',
            'cotsyn',
            'creaen',
            'daepad',
            'deffor',
            'dfppce',
            'doment',
            'domlog',
            'domsoc',
            'donapd',
            'duflot',
            'ecodev',
            'ecpess',
            'garext',
            'intagr',
            'intcon',
            'intemp',
            'invfor',
            'invlst',
            'invrev',
            'locmeu',
            'mecena',
            'mohist',
            'patnat',
            'prcomp',
            'repsoc',
            'resimm',
            'rsceha',
            'saldom',
            'scelli',
            'sofica',
            'sofipe',
            'spfcpi',
            ]
        neutralized_credits = [
            'accult',
            'acqgpl',
            'aidmob',
            'aidper',
            'assloy',
            'autent',
            'ci_garext',
            'cotsyn',
            'creimp',
            'creimp_exc_2008',
            'direpa',
            'divide',
            'drbail',
            'inthab',
            'jeunes',
            'mecena',
            'percvm',
            'preetu',
            'quaenv',
            'saldom2',
            ]

        neutralized_variables = [
            'avantage_en_nature',
            'complementaire_sante_employeur',
            'complementaire_sante_salarie',
            'exoneration_cotisations_employeur_apprenti',
            'exoneration_cotisations_employeur_stagiaire',
            'exoneration_cotisations_salariales_apprenti',
            'exoneration_cotisations_salarie_stagiaire',
            'indemnite_fin_contrat',
            'indemnites_compensatrices_conges_payes',
            'nouvelle_bonification_indiciaire',
            'primes_salaires',
            'prevoyance_obligatoire_cadre',
            'reintegration_titre_restaurant_employeur',
            'remuneration_apprenti',
            'rsa_non_calculable',
            'stage_gratification_reintegration',
            'residence_dom',
            'residence_guadeloupe',
            'residence_guyane',
            'residence_martinique',
            'residence_mayotte',
            'residence_reunion',
            'cf_dom_enfant_trop_jeune',
            'cf_dom_enfant_eligible',
            'asi_aspa_condition_nationalite',
            'ape_avant_cumul',
            'apje_avant_cumul',
            # To reintegrate
            # Revenus
            'aah_base_ressources',
            'agirc_gmp_salarie',
            'supp_familial_traitement',  # Problème de l'autonomie financière
            'traitement_indiciaire_brut',
            'primes_fonction_publique',
            'remuneration_principale',
            'assiette_cotisations_sociales_public',
            'pension_civile_salarie',
            'indemnite_residence',
            'ircantec_salarie',
            'rafp_salarie',
            'contribution_exceptionnelle_solidarite',
            'fonds_emploi_hospitalier',
            'cotisations_employeur_non_contributives',
            'tns_auto_entrepreneur_benefice',
            'assiette_csg_non_abattue',
            # Volontary neutralization
            'rsa_has_ressources_substitution',
            'ass',
            ]

        neutralized_variables += list(set(neutralized_reductions + neutralized_credits))
        for neutralized_variable in neutralized_variables:
            log.info("Neutralizing {}".format(neutralized_variable))
            self.neutralize_column(neutralized_variable)

        class ppa(DatedVariable):
            column = FloatCol
            entity = Famille
            label = u"Prime Pour l'Activité"

            @dated_function(start = date(2016, 1, 1))
            def function(famille, period, legislation):
                period = period.this_month
                seuil_non_versement = legislation(period).prestations.minima_sociaux.ppa.seuil_non_versement
                # éligibilité étudiants

                ppa_eligibilite_etudiants = famille('ppa_eligibilite_etudiants', period)
                ppa = famille('ppa_fictive', period.last_3_months, extra_params = [period], options = [ADD]) / 3
                ppa = ppa * ppa_eligibilite_etudiants * (ppa >= seuil_non_versement)

                rsa_act_seul_recourant = famille('rsa_act_seul_recourant', period)
                rsa_socle_act_recourant = famille('rsa_socle_act_recourant', period)

                return period, ppa * (rsa_socle_act_recourant | rsa_act_seul_recourant)

        class rsa_montant(DatedVariable):
            column = FloatCol
            label = u"Revenu de solidarité active, avant prise en compte de la non-calculabilité."
            entity = Famille
            start_date = date(2009, 6, 1)

            @dated_function(start = date(2017, 1, 1))
            def function_2017(famille, period, legislation):
                period = period.this_month
                seuil_non_versement = legislation(period).prestations.minima_sociaux.rsa.rsa_nv
                rsa = famille('rsa_fictif', period.last_3_months, extra_params = [period], options = [ADD]) / 3
                rsa_socle_seul_recourant = famille('rsa_socle_seul_recourant', period)
                rsa_socle_act_recourant = famille('rsa_socle_act_recourant', period)

                rsa = (
                    rsa_socle_seul_recourant + rsa_socle_act_recourant
                    ) * rsa * (rsa >= seuil_non_versement)

                return period, rsa

            @dated_function(start = date(2016, 1, 1), stop = date(2016, 12, 31))
            def function_2016(famille, period, legislation):
                period = period.this_month
                rsa_socle_non_majore = famille('rsa_socle', period)
                rsa_socle_majore = famille('rsa_socle_majore', period)
                rsa_socle = max_(rsa_socle_non_majore, rsa_socle_majore)

                rsa_revenu_activite = famille('rsa_revenu_activite', period)
                rsa_forfait_logement = famille('rsa_forfait_logement', period)
                rsa_base_ressources = famille('rsa_base_ressources', period)

                rsa_socle_seul_recourant = famille('rsa_socle_seul_recourant', period)
                rsa_socle_act_recourant = famille('rsa_socle_act_recourant', period)

                P = legislation(period).prestations.minima_sociaux.rsa
                seuil_non_versement = P.rsa_nv
                montant = (
                    rsa_socle_seul_recourant + rsa_socle_act_recourant
                    ) * (
                        rsa_socle - rsa_forfait_logement - rsa_base_ressources + P.pente * rsa_revenu_activite
                        # Pente = 0 TODO migrer vers openfisca-france
                        )
                montant = montant * (montant >= seuil_non_versement)

                return period, montant

            @dated_function(start = date(2009, 6, 1), stop = date(2015, 12, 31))
            def function_2009_2015(famille, period, legislation):
                period = period.this_month
                rsa_socle_non_majore = famille('rsa_socle', period)
                rsa_socle_majore = famille('rsa_socle_majore', period)
                rsa_socle = max_(rsa_socle_non_majore, rsa_socle_majore)

                rsa_revenu_activite = famille('rsa_revenu_activite', period)
                rsa_forfait_logement = famille('rsa_forfait_logement', period)
                rsa_base_ressources = famille('rsa_base_ressources', period)

                rsa_socle_seul_recourant = famille('rsa_socle_seul_recourant', period)
                rsa_socle_act_recourant = famille('rsa_socle_act_recourant', period)
                rsa_act_seul_recourant = famille('rsa_act_seul_recourant', period)

                P = legislation(period).prestations.minima_sociaux.rsa
                seuil_non_versement = P.rsa_nv
                montant = (
                    rsa_socle_seul_recourant + rsa_socle_act_recourant + rsa_act_seul_recourant
                    ) * (
                        rsa_socle - rsa_forfait_logement - rsa_base_ressources + P.pente * rsa_revenu_activite
                        )
                montant = montant * (montant >= seuil_non_versement)

                return period, montant

        class rsa_socle_seul_recourant(Variable):
            column = BoolCol(default = False)
            label = u"Recourant au RSA socle si éligible."
            entity = Famille

            def function(famille, period, legislation):
                period = period.this_month
                last_period = period.last_month
                legislation_rsa = legislation(period).prestations.minima_sociaux.rsa

                if period.start.year <= legislation_rsa.non_recours.annee_initialisation:
                    weight_familles = famille('weight_familles', period)
                    return period, weight_familles < -10

                if period.start.year > legislation_rsa.non_recours.annee_initialisation:
                    rsa_socle_non_majore = famille('rsa_socle', period)
                    rsa_socle_majore = famille('rsa_socle_majore', period)
                    rsa_socle = max_(rsa_socle_non_majore, rsa_socle_majore)
                    rsa_forfait_logement = famille('rsa_forfait_logement', period)
                    rsa_base_ressources = famille('rsa_base_ressources', period)
                    rsa_revenu_activite = famille('rsa_revenu_activite', period)
                    weight_familles = famille('weight_familles', period)
                    eligible_rsa_socle = (rsa_socle - rsa_forfait_logement - rsa_base_ressources) > 0
                    eligible_rsa_socle_seul = eligible_rsa_socle & not_(rsa_revenu_activite > 0)
                    recourant_last_period = famille('rsa_socle_seul_recourant', last_period, max_nb_cycles = 1)
                    probabilite_de_non_recours = legislation_rsa.non_recours.probabilite_de_non_recours_socle_seul
                    recourant_rsa = impute_take_up(
                        target_probability = 1 - probabilite_de_non_recours,
                        eligible = eligible_rsa_socle_seul,
                        weights = weight_familles,
                        recourant_last_period = recourant_last_period,
                        seed = 240118
                        )
                    return period, recourant_rsa

        class rsa_socle_act_recourant(DatedVariable):
            column = BoolCol(default = False)
            label = u"Recourant au RSA activité si éligible."
            entity = Famille

            @dated_function(start = date(2016, 1, 1))
            def function_2016_(famille, period, legislation):
                period = period.this_month
                last_period = period.last_month
                legislation_rsa = legislation(period).prestations.minima_sociaux.rsa

                if period.start.year <= legislation_rsa.non_recours.annee_initialisation:
                    weight_familles = famille('weight_familles', period)
                    return period, weight_familles < -10

                if period.start.year > legislation_rsa.non_recours.annee_initialisation:
                    rsa_socle_non_majore = famille('rsa_socle', period)
                    rsa_socle_majore = famille('rsa_socle_majore', period)
                    rsa_socle = max_(rsa_socle_non_majore, rsa_socle_majore)
                    rsa_forfait_logement = famille('rsa_forfait_logement', period)
                    rsa_base_ressources = famille('rsa_base_ressources', period)
                    ppa_eligibilite_etudiants = famille('ppa_eligibilite_etudiants', period)
                    ppa_fictive = famille(
                        'ppa_fictive', period.last_3_months, extra_params = [period], options = [ADD]) / 3
                    ppa = ppa_fictive * ppa_eligibilite_etudiants

                    weight_familles = famille('weight_familles', period)
                    legislation_rsa = legislation(period).prestations.minima_sociaux.rsa
                    eligible_rsa_socle = (rsa_socle - rsa_forfait_logement - rsa_base_ressources) > 0
                    eligible_rsa_socle_ppa = eligible_rsa_socle & (ppa > 0)
                    recourant_last_period = famille('rsa_socle_act_recourant', last_period, max_nb_cycles = 1)
                    probabilite_de_non_recours = legislation_rsa.non_recours.probabilite_de_non_recours_socle_activite
                    recourant_rsa_socle_ppa = impute_take_up(
                        target_probability = 1 - probabilite_de_non_recours,
                        eligible = eligible_rsa_socle_ppa,
                        weights = weight_familles,
                        recourant_last_period = recourant_last_period,
                        seed = 9779972
                        )
                    return period, recourant_rsa_socle_ppa

            @dated_function(start = date(2009, 6, 1), stop = date(2015, 12, 31))
            def function_2009_2015(famille, period, legislation):
                period = period.this_month
                last_period = period.last_month
                legislation_rsa = legislation(period).prestations.minima_sociaux.rsa

                if period.start.year <= legislation_rsa.non_recours.annee_initialisation:
                    weight_familles = famille('weight_familles', period)
                    return period, weight_familles < -10

                if period.start.year > legislation_rsa.non_recours.annee_initialisation:
                    rsa_socle_non_majore = famille('rsa_socle', period)
                    rsa_socle_majore = famille('rsa_socle_majore', period)
                    rsa_socle = max_(rsa_socle_non_majore, rsa_socle_majore)
                    rsa_revenu_activite = famille('rsa_revenu_activite', period)
                    rsa_forfait_logement = famille('rsa_forfait_logement', period)
                    rsa_base_ressources = famille('rsa_base_ressources', period)
                    weight_familles = famille('weight_familles', period)

                    eligible_rsa_socle = (rsa_socle - rsa_forfait_logement - rsa_base_ressources) > 0
                    eligible_rsa_socle_act = eligible_rsa_socle & (rsa_revenu_activite > 0)
                    recourant_last_period = famille('rsa_socle_act_recourant', last_period, max_nb_cycles = 1)
                    probabilite_de_non_recours = legislation_rsa.non_recours.probabilite_de_non_recours_socle_activite
                    recourant_rsa_socle_activite = impute_take_up(
                        target_probability = 1 - probabilite_de_non_recours,
                        eligible = eligible_rsa_socle_act,
                        weights = weight_familles,
                        recourant_last_period = recourant_last_period,
                        seed = 2169065
                        )
                    return period, recourant_rsa_socle_activite

        class rsa_act_seul_recourant(DatedVariable):
            column = BoolCol(default = False)
            label = u"Recourant au RSA activité si éligible."
            entity = Famille

            @dated_function(start = date(2016, 1, 1))
            def function_2016_(famille, period, legislation):
                period = period.this_month
                last_period = period.last_month
                legislation_rsa = legislation(period).prestations.minima_sociaux.rsa

                if period.start.year <= legislation_rsa.non_recours.annee_initialisation:
                    weight_familles = famille('weight_familles', period)
                    return period, weight_familles < -10

                if period.start.year > legislation_rsa.non_recours.annee_initialisation:
                    rsa_socle_non_majore = famille('rsa_socle', period)
                    rsa_socle_majore = famille('rsa_socle_majore', period)
                    rsa_socle = max_(rsa_socle_non_majore, rsa_socle_majore)
                    rsa_forfait_logement = famille('rsa_forfait_logement', period)
                    rsa_base_ressources = famille('rsa_base_ressources', period)
                    ppa_eligibilite_etudiants = famille('ppa_eligibilite_etudiants', period)
                    ppa_fictive = famille(
                        'ppa_fictive', period.last_3_months, extra_params = [period], options = [ADD]) / 3
                    ppa = ppa_fictive * ppa_eligibilite_etudiants

                    weight_familles = famille('weight_familles', period)

                    eligible_rsa_socle = (rsa_socle - rsa_forfait_logement - rsa_base_ressources) > 0
                    eligible_ppa_seule = not_(eligible_rsa_socle) & (ppa > 0)
                    recourant_last_period = famille('rsa_act_seul_recourant', last_period, max_nb_cycles = 1)
                    probabilite_de_non_recours = legislation_rsa.non_recours.probabilite_de_non_recours_activite_seul
                    recourant_ppa = impute_take_up(
                        target_probability = 1 - probabilite_de_non_recours,
                        eligible = eligible_ppa_seule,
                        weights = weight_familles,
                        recourant_last_period = recourant_last_period,
                        seed = 9779972
                        )
                    return period, recourant_ppa

            @dated_function(start = date(2009, 6, 1), stop = date(2015, 12, 31))
            def function_2009_2015(famille, period, legislation):
                period = period.this_month
                last_period = period.last_month
                legislation_rsa = legislation(period).prestations.minima_sociaux.rsa

                if period.start.year <= legislation_rsa.non_recours.annee_initialisation:
                    weight_familles = famille('weight_familles', period)
                    return period, weight_familles < -10

                if period.start.year > legislation_rsa.non_recours.annee_initialisation:
                    rsa_socle_non_majore = famille('rsa_socle', period)
                    rsa_socle_majore = famille('rsa_socle_majore', period)
                    rsa_socle = max_(rsa_socle_non_majore, rsa_socle_majore)
                    rsa_revenu_activite = famille('rsa_revenu_activite', period)
                    rsa_forfait_logement = famille('rsa_forfait_logement', period)
                    rsa_base_ressources = famille('rsa_base_ressources', period)
                    weight_familles = famille('weight_familles', period)
                    legislation_rsa = legislation(period).prestations.minima_sociaux.rsa

                    eligible_rsa_socle = (rsa_socle - rsa_forfait_logement - rsa_base_ressources) > 0
                    eligible_rsa = (
                        rsa_socle - rsa_forfait_logement - rsa_base_ressources +
                        legislation_rsa.pente * rsa_revenu_activite
                        ) > 0
                    eligible_rsa_act_seul = not_(eligible_rsa_socle) & (rsa_revenu_activite > 0) & eligible_rsa
                    recourant_last_period = famille('rsa_act_seul_recourant', last_period, max_nb_cycles = 1)
                    probabilite_de_non_recours = legislation_rsa.non_recours.probabilite_de_non_recours_activite_seul
                    recourant_rsa_activite = impute_take_up(
                        target_probability = 1 - probabilite_de_non_recours,
                        eligible = eligible_rsa_act_seul,
                        weights = weight_familles,
                        recourant_last_period = recourant_last_period,
                        seed = 9779972
                        )
                    return period, recourant_rsa_activite

        def reform_modify_legislation_json(reference_legislation_json_copy):
            reform_legislation_subtree = {
                "@type": "Node",
                "description": u"Non recours au RSA",
                "children": {
                    "probabilite_de_non_recours_activite_seul": {
                        "@type": "Parameter",
                        "description": u"Probabilité de non recours au RSA activité",
                        "format": "float",
                        "values": [{
                            'start': u'2009-06-01',
                            'stop': u'2020-12-31',
                            'value': .68,
                            }],
                        },
                    "probabilite_de_non_recours_socle_activite": {
                        "@type": "Parameter",
                        "description": u"Probabilité de non recours au RSA socle seul",
                        "format": "float",
                        "unit": "currency",
                        "values": [{
                            'start': u'2009-06-01',
                            'stop': u'2020-12-31',
                            'value': .33,
                            }],
                        },
                    "probabilite_de_non_recours_socle_seul": {
                        "@type": "Parameter",
                        "description": u"Probabilité de non recours au RSA socle seul",
                        "format": "float",
                        "unit": "currency",
                        "values": [{
                            'start': u'2009-06-01',
                            'stop': u'2020-12-31',
                            'value': .36,
                            }],
                        },
                    "annee_initialisation": {
                        "@type": "Parameter",
                        "description": u"Probabilité de non recours au RSA socle seul",
                        "format": "integer",
                        "values": [{
                            'start': u'2009-06-01',
                            'stop': u'2020-12-31',
                            'value': 2011,  # Arbitraire
                            }],
                        },
                    },
                }
            reference_legislation_json_copy[
                'children']['prestations']['children']['minima_sociaux']['children']['rsa']['children'][
                    'non_recours'] = reform_legislation_subtree
            return reference_legislation_json_copy

        self.modify_legislation_json(modifier_function = reform_modify_legislation_json)
        self.update_variable(ppa)
        self.add_variable(rsa_socle_seul_recourant)
        self.add_variable(rsa_act_seul_recourant)
        self.add_variable(rsa_socle_act_recourant)
        self.update_variable(rsa_montant)


openfisca_france_tax_benefit_system = openfisca_france.FranceTaxBenefitSystem()
# The existence of either CountryTaxBenefitSystem or country_tax_benefit_system is mandatory
france_data_tax_benefit_system = openfisca_france_data(openfisca_france_tax_benefit_system)

CountryTaxBenefitSystem = lambda: france_data_tax_benefit_system  # noqa analysis:ignore

AGGREGATES_DEFAULT_VARS = [
    'cotisations_non_contributives',
    'csg',
    'crds',
    'irpp',
    'ppe',
    'ppe_brute',
    'af',
    'af_base',
    'af_majoration',
    'af_allocation_forfaitaire',
    'cf',
    'paje_base',
    'paje_naissance',
    'paje_clca',
    'paje_cmg',
    'ars',
    'aeeh',
    'asf',
    # 'aspa',
    'minimum_vieillesse',
    'aah',
    'caah',
    'rsa',
    'rsa_activite',
    'aefa',
    'api',
    # 'majo_rsa',
    'psa',
    'aides_logement',
    'alf',
    'als',
    'apl',
    ]
#  ajouter csgd pour le calcul des agrégats erfs
#  ajouter rmi pour le calcul des agrégats erfs


COUNTRY_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(
    pkg_resources.get_distribution('openfisca-france-data').location,
    'openfisca_france_data',
    'plugins',
    'aggregates'
    )
WEIGHT = "wprm"
WEIGHT_INI = "wprm_init"

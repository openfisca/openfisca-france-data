# -*- coding: utf-8 -*-


from __future__ import division

import inspect
import logging
import os
import pkg_resources

from numpy import (logical_not as not_, maximum as max_)
import pandas as pd

from openfisca_core import reforms
from openfisca_core.variables import Variable

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


def impute_take_up(target_probability, eligible, weights):
    """
    Compute a vector of boolean for take_up according a target probability accross eligble population
    """
    data = pd.DataFrame({
        'eligible': eligible,
        'weights': weights,
        })

    r_data = data.loc[data.eligible == 1]
    s_data = r_data.sample(frac = target_probability, replace = False, axis=0)
    s_data['recourant'] = True

    merged = data.merge(s_data, left_index = True, right_index = True, how = 'left')
    merged['recourant'] = merged.recourant.fillna(False)
    return merged.recourant.values


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
            ]

        neutralized_variables += list(set(neutralized_reductions + neutralized_credits))
        for neutralized_variable in neutralized_variables:
            log.info("Neutralizing {}".format(neutralized_variable))
            self.neutralize_column(neutralized_variable)

        # Non recours RSA

        class rsa_montant(Variable):
            column = FloatCol
            label = u"Revenu de solidarité active, avant prise en compte de la non-calculabilité."
            entity = Famille
            start_date = date(2009, 06, 1)

            def function(famille, period, legislation):
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

        class rsa_socle_act_recourant(Variable):
            column = BoolCol(default = True)
            label = u"Recourant au RSA activité si éligible."
            entity = Famille

            def function(famille, period, legislation):
                period = period.this_month
                rsa_socle_non_majore = famille('rsa_socle', period)
                rsa_socle_majore = famille('rsa_socle_majore', period)
                rsa_socle = max_(rsa_socle_non_majore, rsa_socle_majore)
                rsa_revenu_activite = famille('rsa_revenu_activite', period)
                rsa_forfait_logement = famille('rsa_forfait_logement', period)
                rsa_base_ressources = famille('rsa_base_ressources', period)
                weight_familles = famille('weight_familles', period)
                eligible_rsa_socle = (rsa_socle - rsa_forfait_logement - rsa_base_ressources) > 0
                eligible_rsa_socle_act = eligible_rsa_socle & (rsa_revenu_activite > 0)
                probabilite_de_non_recours = .33
                recourant_rsa_activite = impute_take_up(
                    target_probability = 1 - probabilite_de_non_recours,
                    eligible = eligible_rsa_socle_act,
                    weights = weight_familles,
                    )
                return period, recourant_rsa_activite

        class rsa_act_seul_recourant(Variable):
            column = BoolCol(default = True)
            label = u"Recourant au RSA activité si éligible."
            entity = Famille

            def function(famille, period, legislation):
                period = period.this_month
                rsa_socle_non_majore = famille('rsa_socle', period)
                rsa_socle_majore = famille('rsa_socle_majore', period)
                rsa_socle = max_(rsa_socle_non_majore, rsa_socle_majore)
                rsa_revenu_activite = famille('rsa_revenu_activite', period)
                rsa_forfait_logement = famille('rsa_forfait_logement', period)
                rsa_base_ressources = famille('rsa_base_ressources', period)
                weight_familles = famille('weight_familles', period)
                P = legislation(period).prestations.minima_sociaux.rsa

                eligible_rsa_socle = (rsa_socle - rsa_forfait_logement - rsa_base_ressources) > 0
                eligible_rsa = (
                    rsa_socle - rsa_forfait_logement - rsa_base_ressources + P.pente * rsa_revenu_activite
                    ) > 0
                eligible_rsa_act_seul = not_(eligible_rsa_socle) & (rsa_revenu_activite > 0) & eligible_rsa
                probabilite_de_non_recours = .68
                recourant_rsa_activite = impute_take_up(
                    target_probability = 1 - probabilite_de_non_recours,
                    eligible = eligible_rsa_act_seul,
                    weights = weight_familles,
                    )
                return period, recourant_rsa_activite

        class rsa_socle_seul_recourant(Variable):
            column = BoolCol(default = True)
            label = u"Recourant au RSA socle si éligible."
            entity = Famille

            def function(famille, period, legislation):
                period = period.this_month
                rsa_socle_non_majore = famille('rsa_socle', period)
                rsa_socle_majore = famille('rsa_socle_majore', period)
                rsa_socle = max_(rsa_socle_non_majore, rsa_socle_majore)
                rsa_forfait_logement = famille('rsa_forfait_logement', period)
                rsa_base_ressources = famille('rsa_base_ressources', period)
                rsa_revenu_activite = famille('rsa_revenu_activite', period)
                weight_familles = famille('weight_familles', period)
                eligible_rsa_socle = (rsa_socle - rsa_forfait_logement - rsa_base_ressources) > 0
                eligible_rsa_socle_seul = eligible_rsa_socle & not_(rsa_revenu_activite > 0)
                probabilite_de_non_recours = .36
                recourant_rsa = impute_take_up(
                    target_probability = 1 - probabilite_de_non_recours,
                    eligible = eligible_rsa_socle_seul,
                    weights = weight_familles,
                    )
                return period, recourant_rsa

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

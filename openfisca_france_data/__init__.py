# -*- coding: utf-8 -*-


import inspect
import logging
import os
import pkg_resources


from openfisca_core import reforms
from openfisca_core.variables import Variable

import openfisca_france

# Load input variables and output variables into entities
from .model import common, survey_variables  # noqa analysis:ignore


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
            'caah',
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


openfisca_france_tax_benefit_system = openfisca_france.FranceTaxBenefitSystem()
# The existence of either CountryTaxBenefitSystem or country_tax_benefit_system is mandatory
france_data_tax_benefit_system = country_tax_benefit_system = openfisca_france_data(openfisca_france_tax_benefit_system)


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

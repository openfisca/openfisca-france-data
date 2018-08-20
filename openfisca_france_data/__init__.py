# -*- coding: utf-8 -*-


from __future__ import division

import inspect
import logging
import os
import pkg_resources

import pandas as pd

from openfisca_core import reforms
# from openfisca_core.formulas import set_input_divide_by_period

import openfisca_france

# Load input variables and output variables into entities
from .model import common, survey_variables, id_variables  # noqa analysis:ignore
from .model.base import * # noqa  analysis:ignore


log = logging.getLogger(__name__)


def get_variables_from_module(module):
    variables = [
        getattr(module, item)
        for item in dir(module)
        if inspect.isclass(getattr(module, item))
        ]
    return [
        variable for variable in variables if issubclass(variable, Variable)  # noqa  analysis:ignore
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
    'aggregates',
    )

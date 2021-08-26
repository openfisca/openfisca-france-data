import inspect
import logging
import os
import pkg_resources
import pandas

from openfisca_core import reforms  # type: ignore

import openfisca_france  # type: ignore

# Load input variables and output variables into entities
from openfisca_france_data.model import common, survey_variables, id_variables  # noqa analysis:ignore
from openfisca_france_data.model.base import * # noqa  analysis:ignore


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

    data = pandas.DataFrame({
        'eligible': eligible,
        'weights': weights,
        'deja_recourant': recourant_last_period,
        })

    eligibles = data.loc[data.eligible == 1].copy()
    eligibles['recourant'] = eligibles.deja_recourant
    assert len(eligibles) > 0, "Aucun eligibles : impossible d'imputer le non recours"
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


def select_to_match_target(target_probability = None, target_mass = None, eligible = None, weights = None, take = None, seed = None):
    """
    Compute a vector of boolean for take_up according a target probability accross eligble population.
    If there is no eligible population, it returns False for the whole population.
    """
    if not(eligible.any()):
        print("No eligible observations : none of the observations will be selected. The target probability is not matched.")
        return eligible
    assert (target_probability is not None) or (target_mass is not None)
    if take is None:
        take = False
    if target_mass is not None:
        assert target_mass <= (eligible * weights).sum(), "target too high {}, {}".format(
            target_mass, (eligible * weights).sum())
        target_probability = target_mass / (eligible * weights).sum()

    assert (target_probability >= 0) and (target_probability <= 1)

    if target_probability == 0:
        return eligible * False
    elif target_probability == 1:
        return eligible * True

    data = pandas.DataFrame({
        'eligible': eligible,
        'weights': weights,
        'take': take,
        }).copy()

    eligibles = data.loc[data.eligible].copy()
    eligibles['selected'] = eligibles['take'].copy()
    initial_probability = eligibles.loc[eligibles['take'], 'weights'].sum() / eligibles.weights.sum()

    if target_probability > initial_probability:
        adjusted_target_probability = (target_probability - initial_probability) / (1 - initial_probability)
        s_data = eligibles.loc[~eligibles.selected].copy()
        s_data = s_data.sample(frac = adjusted_target_probability, replace = False, axis = 0, random_state = seed)
        eligibles.loc[eligibles.index.isin(s_data.index), 'selected'] = True
        eligibles_selected_indices = eligibles.query('eligible & selected').index
        data['selected'] = False
        data.loc[data.index.isin(eligibles_selected_indices), 'selected'] = True

    elif target_probability <= initial_probability:
        print("The target probability set ({}) is too low compared to the number of eligibles to take. Some individuals with take == True will be unselected to match the target probability.".format(target_probability))
        adjusted_target_probability = 1 - target_probability / initial_probability
        s_data = eligibles.loc[eligibles.selected].copy()
        s_data = s_data.sample(frac = adjusted_target_probability, replace = False, axis = 0, random_state = seed)
        eligibles_unselected_indices = s_data.index
        data['selected'] = data['take'] & data.eligible
        data.loc[data.index.isin(eligibles_unselected_indices), 'selected'] = False

    return data.selected.values



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

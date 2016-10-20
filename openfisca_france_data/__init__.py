# -*- coding: utf-8 -*-


import inspect
import os
import pkg_resources


from openfisca_core import reforms
from openfisca_core.variables import Variable

import openfisca_france

# Load input variables and output variables into entities
from .model import common, survey_variables # noqa analysis:ignore


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



openfisca_france_tax_benefit_system = openfisca_france.FranceTaxBenefitSystem()
france_data_tax_benefit_system = openfisca_france_data(openfisca_france_tax_benefit_system)

#TaxBenefitSystem = reforms.make_reform(
#    key = 'openfisca_france_data',
#    name = u"OpenFisca for survey data",
#    reference = openfisca_france_tax_benefit_system,
#    )
#
## Export reform classes to register variables in reform column_by_name dict.
#DatedVariable = TaxBenefitSystem.DatedVariable
#EntityToPersonColumn = TaxBenefitSystem.EntityToPersonColumn
#PersonToEntityColumn = TaxBenefitSystem.PersonToEntityColumn
#Variable = Variable


AGGREGATES_DEFAULT_VARS = [
    'cotsoc_noncontrib',
    'csg',
    'crds',
    'irpp',
    'ppe',
    'ppe_brute',
    'af',
    'af_base',
    'af_majo',
    'af_forf',
    'cf',
    'paje_base',
    'paje_naissance',
    'paje_clca',
    'paje_clmg',
    'ars',
    'aeeh',
    'asf',
    'aspa',
    'aah',
    'caah',
    'rsa',
    'rsa_act',
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


default_config_files_directory = pkg_resources.get_distribution('openfisca-survey-manager').location


COUNTRY_DIR = os.path.dirname(os.path.abspath(__file__))
FILTERING_VARS = ["champm"]
PLUGINS_DIR = os.path.join(COUNTRY_DIR, 'plugins')
WEIGHT = "wprm"
WEIGHT_INI = "wprm_init"

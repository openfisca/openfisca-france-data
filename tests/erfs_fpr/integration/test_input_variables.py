import logging

from openfisca_france_data import france_data_tax_benefit_system
from openfisca_france_data.erfs_fpr.get_survey_scenario import get_survey_scenario


log = logging.getLogger(__name__)

year = 2014
tax_benefit_system = france_data_tax_benefit_system

survey_scenario = get_survey_scenario(
    tax_benefit_system = tax_benefit_system,
    baseline_tax_benefit_system = tax_benefit_system,
    year = year,
    rebuild_input_data = False,
    )


checks_by_variable = {
    'salaire_de_base': {
        'min': 500e9
        }
    }


for variable in survey_scenario.used_as_input_variables:
    checks = checks_by_variable.get(variable)
    print(variable)
    minimum = checks.get('min') if checks is not None else None
    if minimum:
        assert survey_scenario.compute_aggregate(variable, period = 2014) >= minimum
    survey_scenario.summarize_variable(variable)


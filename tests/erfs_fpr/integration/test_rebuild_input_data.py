import logging

from openfisca_france_data import base_survey
from openfisca_france_data.erfs_fpr.get_survey_scenario import get_survey_scenario

log = logging.getLogger(__name__)


def test_rebuild_input_data(year = 2014):

    tax_benefit_system = base_survey.france_data_tax_benefit_system

    survey_scenario = get_survey_scenario(
        tax_benefit_system = tax_benefit_system,
        baseline_tax_benefit_system = tax_benefit_system,
        year = year,
        rebuild_input_data = True,
        )
    return survey_scenario


if __name__ == '__main__':
    import logging
    log = logging.getLogger(__name__)
    import sys
    logging.basicConfig(
        level = logging.DEBUG,
        filename = "rebuild_input_data_log.txt",
        # stream = sys.stdout
        )
    survey_scenario = test_rebuild_input_data()
    survey_scenario.summarize_variable('salaire_de_base', force_compute = True)
    survey_scenario.summarize_variable('salaire_imposable', force_compute = True)

# -*- coding: utf-8 -*-


import logging
import numpy

from openfisca_france_data import france_data_tax_benefit_system  # type: ignore
from openfisca_france_data.erfs_fpr.get_survey_scenario import (  # type: ignore
    get_survey_scenario,
    )
from openfisca_france_data.aggregates import Aggregates  # type: ignore

log = logging.getLogger(__name__)


def test_erfs_fpr_survey_simulation_aggregates(year = 2012, rebuild_input_data = False):
    numpy.seterr(all = 'raise')
    tax_benefit_system = france_data_tax_benefit_system

    survey_scenario = get_survey_scenario(
        tax_benefit_system = tax_benefit_system,
        baseline_tax_benefit_system = tax_benefit_system,
        year = year,
        rebuild_input_data = rebuild_input_data,
        )

    aggregates = Aggregates(survey_scenario = survey_scenario)

    return survey_scenario, aggregates


def test_erfs_fpr_aggregates_reform(year = 2012, rebuild_input_data = False):
    tax_benefit_system = france_data_tax_benefit_system

    survey_scenario = get_survey_scenario(
        reform = 'plf2015',
        baseline_tax_benefit_system = tax_benefit_system,
        year = year,
        rebuild_input_data = rebuild_input_data,
        )
    aggregates = Aggregates(survey_scenario = survey_scenario)
    base_data_frame = aggregates.compute_aggregates()
    difference_data_frame = aggregates.compute_difference()

    return aggregates, base_data_frame, difference_data_frame


if __name__ == '__main__':
    import logging
    log = logging.getLogger(__name__)
    import sys
    logging.basicConfig(level = logging.DEBUG, stream = sys.stdout)
    # aggregates_data_frame, difference_data_frame,
    survey_scenario, aggregates = test_erfs_fpr_survey_simulation_aggregates(
        year = 2014, rebuild_input_data = True)

    # aggregates, base_data_frame, difference_data_frame = test_erfs_fpr_aggregates_reform()


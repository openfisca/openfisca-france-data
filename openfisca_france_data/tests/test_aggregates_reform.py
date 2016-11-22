# -*- coding: utf-8 -*-


from openfisca_france_data.input_data_builders import get_input_data_frame
from openfisca_france_data.surveys import SurveyScenario
from openfisca_france_data.tests import base
from openfisca_plugin_aggregates.aggregates import Aggregates


def create_survey_scenario(data_year = 2009, year = 2013, reform = None):
    assert year is not None
    assert data_year is not None
    input_data_frame = get_input_data_frame(data_year)
    survey_scenario = SurveyScenario().init_from_data_frame(
        input_data_frame = input_data_frame,
        tax_benefit_system = reform,
        reference_tax_benefit_system = base.france_data_tax_benefit_system,
        year = year,
        )

    return survey_scenario


def test_aggregates_reform(data_year = 2009, year = 2013, reform = None):
    '''
    test aggregates value with data
    :param year: year of data and simulation to test agregates
    :param reform: optional argument, put an openfisca_france.refoms object, default None
    '''
    assert year is not None
    survey_scenario = create_survey_scenario(data_year = data_year, year = year, reform = reform)
    aggregates = Aggregates(survey_scenario = survey_scenario)
    base_data_frame = aggregates.compute_aggregates()

    return aggregates, base_data_frame


if __name__ == '__main__':
    from openfisca_france.reforms import plf2015
    reform = plf2015.build_reform(base.france_data_tax_benefit_system)

    import logging
    log = logging.getLogger(__name__)
    import sys
    logging.basicConfig(level = logging.INFO, stream = sys.stdout)
    aggregates, base_data_frame = test_aggregates_reform(data_year = 2009, year = 2013, reform = reform)

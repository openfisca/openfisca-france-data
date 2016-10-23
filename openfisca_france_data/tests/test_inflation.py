# -*- coding: utf-8 -*-


import logging
import sys

from openfisca_france_data.erfs.scenario import ErfsSurveyScenario

log = logging.getLogger(__name__)


def test_inflation():
    year = 2009
    survey_scenario = ErfsSurveyScenario.create(year = year)
    survey_scenario.new_simulation()
    target_by_variable = dict(
        salaire_imposable = 1.2e08,
        )
    survey_scenario.inflate(target_by_variable = target_by_variable)


if __name__ == '__main__':
    logging.basicConfig(level = logging.INFO, stream = sys.stdout)
    test_inflation()

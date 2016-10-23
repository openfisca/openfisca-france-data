# -*- coding: utf-8 -*-


import pkg_resources
import os


from openfisca_survey_manager.calibration import Calibration
from openfisca_france_data.erfs.scenario import ErfsSurveyScenario


openfisca_france_data_location = pkg_resources.get_distribution('openfisca-france-data').location


def test_calibration():
    year = 2009
    survey_scenario = ErfsSurveyScenario().create(year = year)
    survey_scenario.initialize_weights()
    calibration = Calibration(survey_scenario)
    calibration.parameters['method'] = 'linear'
    log.info('initial_total_population: {} '.format(calibration.initial_total_population))
    calibration.total_population = calibration.initial_total_population * 1.123
    log.info('calibration.total_population: {} '.format(calibration.total_population))

    filename = os.path.join(
        openfisca_france_data_location,
        "openfisca_france_data",
        "calibrations",
        "calib_2006.csv"
        )
    calibration.set_inputs_margins_from_file(filename, 2006)
    calibration.set_parameters('invlo', 3)
    calibration.set_parameters('up', 3)
    calibration.set_parameters('method', 'logit')
    calibration.calibrate()


if __name__ == '__main__':
    import logging
    log = logging.getLogger(__name__)
    import sys
    logging.basicConfig(level = logging.INFO, stream = sys.stdout)
    test_calibration()

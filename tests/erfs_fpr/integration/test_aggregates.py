"""ERFS-FPR aggregates integrations tests."""

import configparser
import click
import logging
import numpy as np
import sys


from openfisca_france_data import france_data_tax_benefit_system
from openfisca_france_data.erfs_fpr.get_survey_scenario import get_survey_scenario
from openfisca_france_data.aggregates import Aggregates


log = logging.getLogger(__name__)



def test_erfs_fpr_survey_simulation_aggregates(year = 2014, rebuild_input_data = False):
    log.info(f'test_erfs_fpr_survey_simulation_aggregates for {year}...')
    np.seterr(all = 'raise')
    tax_benefit_system = france_data_tax_benefit_system

    survey_scenario = get_survey_scenario(
        tax_benefit_system = tax_benefit_system,
        year = year,
        rebuild_input_data = rebuild_input_data,
        )
    aggregates = Aggregates(survey_scenario = survey_scenario)

    return survey_scenario, aggregates


def test_erfs_fpr_aggregates_reform():
    """Tests aggregates value with data.

    :param year: year of data and simulation to test agregates
    :param reform: optional argument, put an openfisca_france.refoms object, default None
    """
    tax_benefit_system = france_data_tax_benefit_system
    year = 2014
    survey_scenario = get_survey_scenario(
        reform = 'plf2015',
        baseline_tax_benefit_system = tax_benefit_system,
        year = year,
        rebuild_input_data = False,
        )
    aggregates = Aggregates(survey_scenario = survey_scenario)
    base_data_frame = aggregates.compute_aggregates()
    difference_data_frame = aggregates.compute_difference()

    return aggregates, base_data_frame, difference_data_frame


@click.command()
@click.option('-y', '--year', 'year', default = 2016, help = "ERFS-FPR year", show_default = True,
    type = int, required = True)
@click.option('-c', '--configfile', default = None,
    help = 'raw_data.ini path to read years to process.', show_default = True)
@click.option('-v', '--verbose', default = False,
    help = 'print debug information', show_default = True)
def main(year, configfile = None, verbose = False):
    if verbose:
        logging.basicConfig(level = logging.DEBUG, stream = sys.stdout)
    else:
        logging.basicConfig(level = logging.INFO, stream = sys.stdout)

    years = []
    if configfile is not None:
        try:
            config = configparser.ConfigParser()
            config.read(configfile)
            for key in config['erfs_fpr']:
                if key.isnumeric():
                    years.append(int(key))
                    log.info(f"Adding year {int(key)}")
        except KeyError:
            years = [year]
            log.warning(f"File {configfile} not found, switchin to default {years}")
    else:
        years = [year]
    for year in years:
        survey_scenario, aggregates = test_erfs_fpr_survey_simulation_aggregates(
            year = year,
            rebuild_input_data = False,
            )
        survey_scenario._set_used_as_input_variables_by_entity()
        df = aggregates.compute_aggregates(actual = True)
        df.to_csv(f'aggregates{year}.csv')


if __name__ == '__main__':
    main()

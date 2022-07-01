"""ERFS-FPR aggregates integrations tests."""

import configparser
import click
import logging
import numpy as np
import pandas as pd
import sys
import gc


from openfisca_france_data import france_data_tax_benefit_system
from openfisca_france_data.erfs_fpr.get_survey_scenario import get_survey_scenario
from openfisca_france_data.aggregates import FranceAggregates as Aggregates


log = logging.getLogger(__name__)
logging.basicConfig(level = logging.INFO, stream = sys.stdout,
    format='%(asctime)s - %(name)-12s: %(levelname)s %(module)s - %(funcName)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


def test_erfs_fpr_survey_simulation_aggregates(year = 2014, rebuild_input_data = False):
    log.info(f'test_erfs_fpr_survey_simulation_aggregates for {year}...')
    np.seterr(all = 'raise')
    tax_benefit_system = france_data_tax_benefit_system

    survey_scenario = get_survey_scenario(
        tax_benefit_system = tax_benefit_system,
        year = year,
        rebuild_input_data = rebuild_input_data,
        use_marginal_tax_rate = True,
        variation_factor = 0.03,
        varying_variable = 'salaire_de_base',
        )
    aggregates = Aggregates(survey_scenario = survey_scenario)

    if False:
        mtr_rd = survey_scenario.compute_marginal_tax_rate(target_variable = 'revenu_disponible', period = year, use_baseline = True)
        print("Rev Disp: Mean = {}; Zero = {}; Positive = {}; Total = {};".format(mtr_rd.mean(), sum(mtr_rd == 0), sum(mtr_rd > 0), mtr_rd.size))
        np.quantile(mtr_rd, q = np.arange(0, 1.1, .1))

        vv1 = survey_scenario.simulation.calculate_add('salaire_de_base', period = year)
        vv2 = survey_scenario._modified_simulation.calculate_add('salaire_de_base', period = year)

        tv1 = survey_scenario.simulation.calculate_add('revenu_disponible', period = year)
        tv2 = survey_scenario._modified_simulation.calculate_add('revenu_disponible', period = year)

        np.quantile(mtr_rd, q = np.arange(0, 1.1, .1))

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
@click.option('-y', '--year', 'year', default = 2018, help = "ERFS-FPR year", show_default = True,
    type = int, required = True)
@click.option('-c', '--configfile', default = None,
    help = 'raw_data.ini path to read years to process.', show_default = True)
@click.option('-v', '--verbose', default = False,
    help = 'print debug information', show_default = True)
def main(year, configfile = None, verbose = False):
    """Computes aggregates."""
    if verbose:
        logging.basicConfig(level = logging.DEBUG, stream = sys.stdout)

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
        # aggregates.to_csv(f'aggregates{year}.csv')
        # print(aggregates.to_markdown())
        # aggregates.to_html(f'aggregates{year}.html')

        mtr_rd = survey_scenario.compute_marginal_tax_rate(target_variable = 'revenu_disponible', period = year, use_baseline = True)
        print("Rev Disp: Mean = {}; Zero = {}; Positive = {}; Total = {};".format(mtr_rd.mean(), sum(mtr_rd == 0), sum(mtr_rd > 0), mtr_rd.size))
        # np.quantile(mtr_rd, q = np.arange(0, 1.1, .1))

        # vv1 = survey_scenario.simulation.calculate_add('salaire_de_base', period = year)
        # vv2 = survey_scenario._modified_simulation.calculate_add('salaire_de_base', period = year)

        # tv1 = survey_scenario.simulation.calculate_add('revenu_disponible', period = year)
        # tv2 = survey_scenario._modified_simulation.calculate_add('revenu_disponible', period = year)

        vars_to_export = [
            'salaire_de_base',
            'revenu_disponible',
            'revenus_nets_du_travail',
            'revenus_nets_du_capital',
            'pensions_nettes',
            'impots_directs',
            'prestations_sociales',
            'ppe'
            ]

        print("Computing baseline data frame")
        dtbl = survey_scenario.create_data_frame_by_entity(vars_to_export, use_modified=False)
        print("Saving to disk")
        dtbl.to_csv("dt_baseline.csv")

        print("Computing reform data frame")
        dtrf = survey_scenario.create_data_frame_by_entity(vars_to_export, use_modified=True)
        print("Saving to disk")
        dtrf.to_csv("dt_reforme.csv")

        print("All done!")

        # dt = pd.DataFrame()
        # gc.collect()

        # for v in vars_to_export:
        #     dt = pd.DataFrame()
        #     gc.collect()
            
        #     print("Getting values of variable {}".format(v))
        #     print("Baseline")
        #     baseline = survey_scenario.simulation.calculate_add(v, period = year)
        #     print("Done")
        #     print("Reforme")
        #     reforme = survey_scenario._modified_simulation.calculate_add(v, period = year)
        #     print("Done")

        #     varname_bl = v + '_bl'
        #     varname_rf = v + '_rf'

        #     dt[varname_bl] = baseline
        #     dt[varname_rf] = reforme

        #     print("Writing to disk")
        #     dt.to_csv("comp_mtr_{}_{}.csv".format(v, year))
        #     gc.collect()





if __name__ == '__main__':
    log.info("Starting...")
    main()
    log.info("THE END!")

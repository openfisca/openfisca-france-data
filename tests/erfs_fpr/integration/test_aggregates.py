"""ERFS-FPR aggregates integrations tests."""

import configparser
import click
import logging
import numpy as np
import pandas as pd
import sys
import gc
import os


from openfisca_france_data import france_data_tax_benefit_system
from openfisca_france_data.erfs_fpr.get_survey_scenario import get_survey_scenario
from openfisca_france_data.aggregates import FranceAggregates as Aggregates


log = logging.getLogger(__name__)
logging.basicConfig(level = logging.INFO, stream = sys.stdout,
    format='%(asctime)s - %(name)-12s: %(levelname)s %(module)s - %(funcName)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


def test_erfs_fpr_survey_simulation_aggregates(year = 2014, rebuild_input_data = False, use_marginal_tax_rate = True, variation_factor = 0.03, varying_variable = 'salaire_de_base'):
    log.info(f'test_erfs_fpr_survey_simulation_aggregates for {year}...')
    np.seterr(all = 'raise')
    tax_benefit_system = france_data_tax_benefit_system

    survey_scenario = get_survey_scenario(
        tax_benefit_system = tax_benefit_system,
        year = year,
        rebuild_input_data = rebuild_input_data,
        use_marginal_tax_rate = use_marginal_tax_rate,
        variation_factor = variation_factor,
        varying_variable = varying_variable,
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

    # marginal tax rate parameters
    varying_variable = 'salaire_de_base'
    target_variable = 'revenu_disponible'
    relative_variation = 0.03

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
        survey_scenario, _ = test_erfs_fpr_survey_simulation_aggregates(
            year = year,
            rebuild_input_data = False,
            use_marginal_tax_rate = True,
            variation_factor = relative_variation,
            varying_variable = varying_variable
            )
        survey_scenario._set_used_as_input_variables_by_entity()

        mtr_rd = survey_scenario.compute_marginal_tax_rate(target_variable = target_variable, period = year, use_baseline = True)
        print("Rev Disp: Mean = {}; Zero = {}; Positive = {}; Total = {};".format(mtr_rd.mean(), sum(mtr_rd == 0), sum(mtr_rd > 0), mtr_rd.size))
        gc.collect()

        var_level = "b+1"

        # salaire_de_base ne bouge pas :
        # ppe, rev_cap, pens_nettes
        # exclues dans les décompositions suivantes, pour l'instant

        if var_level == "basic":
            vars_to_export = [
                'salaire_de_base',
                'revenu_disponible',
                'niveau_de_vie',
                'revenus_nets_du_travail',
                'revenus_nets_du_capital',
                'pensions_nettes',
                'impots_directs',
                'prestations_sociales',
                # 'ppe',
                'wprm',
                ]
        elif var_level == "b+1":
            vars_to_export = [
                'salaire_de_base',
                'revenu_disponible',
                'niveau_de_vie',
                'revenus_nets_du_travail',
                'salaire_net',
                'rpns_imposables',
                'csg_imposable_non_salarie',
                'crds_non_salarie',
                # 'revenus_nets_du_capital',
                # 'pensions_nettes',
                'impots_directs',
                'taxe_habitation',
                'irpp_economique',
                'prelevement_forfaitaire_liberatoire',
                'prelevement_forfaitaire_unique_ir',
                'ir_pv_immo',
                'isf_ifi',
                'prestations_sociales',
                'prestations_familiales',
                'minima_sociaux',
                'aides_logement',
                'reduction_loyer_solidarite',
                'covid_aide_exceptionnelle_famille_montant',
                'covid_aide_exceptionnelle_tpe_montant',
                # 'ppe'
                'wprm',
                ]

        print("Computing baseline data frame")
        dtbl = survey_scenario.create_data_frame_by_entity(vars_to_export, index=True, use_modified=False, merge=True)
        print("Saving to disk")
        dtbl.to_csv("dt_baseline.csv")
        gc.collect()

        print("Computing reform data frame")
        dtrf = survey_scenario.create_data_frame_by_entity(vars_to_export, index=True, use_modified=True, merge=True)
        print("Saving to disk")
        dtrf.to_csv("dt_reform.csv")
        gc.collect()

        print("Launching R script..")

        # 'vsc' option necessary to indicate right path to R; the number afterwards is the individual ID for the cas types
        os.system('echo 0070 | sudo -S Rscript ~/Analysis/Debug/MTR-Components_Python.R vsc 42 {} {} {}'.format(varying_variable, target_variable, relative_variation))

        print("All done!")


if __name__ == '__main__':
    log.info("Starting...")
    main()
    log.info("THE END!")

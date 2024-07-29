"""ERFS-FPR aggregates integrations tests."""

import configparser
import click
import logging
import numpy as np
import pandas as pd
import sys
import gc

from openfisca_france_data import france_data_tax_benefit_system
from openfisca_france_data.erfs_fpr import REFERENCE_YEAR
from openfisca_france_data.erfs_fpr.get_survey_scenario import get_survey_scenario
from openfisca_france_data.aggregates import FranceAggregates as Aggregates
from openfisca_france_data.config import config

log = logging.getLogger(__name__)
logging.basicConfig(level = logging.INFO, stream = sys.stdout,
    format='%(asctime)s - %(name)-12s: %(levelname)s %(module)s - %(funcName)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def test_erfs_fpr_survey_simulation_aggregates(year = REFERENCE_YEAR, rebuild_input_data = False, use_marginal_tax_rate = True, variation_factor = 0.03, varying_variable = 'salaire_de_base'):
    log.info(f'test_erfs_fpr_survey_simulation_aggregates for {year}...')
    np.seterr(all = 'raise')
    tax_benefit_system = france_data_tax_benefit_system
    survey_name = 'openfisca_erfs_fpr_' + str(year)
    survey_scenario = get_survey_scenario(
        tax_benefit_system = tax_benefit_system,
        year = year,
        rebuild_input_data = rebuild_input_data,
        use_marginal_tax_rate = use_marginal_tax_rate,
        variation_factor = variation_factor,
        varying_variable = varying_variable,
        survey_name = survey_name,
        )
    aggregates_taxipp = Aggregates(survey_scenario = survey_scenario, target_source = 'taxipp')
    aggregates_ines = Aggregates(survey_scenario = survey_scenario, target_source = 'ines')
    aggregates_france_entiere = Aggregates(survey_scenario = survey_scenario, target_source = 'france_entiere')

    if False:
        mtr_rd = survey_scenario.compute_marginal_tax_rate(target_variable = 'revenu_disponible', period = year, use_baseline = True)
        print("Rev Disp: Mean = {}; Zero = {}; Positive = {}; Total = {};".format(mtr_rd.mean(), sum(mtr_rd == 0), sum(mtr_rd > 0), mtr_rd.size))
        np.quantile(mtr_rd, q = np.arange(0, 1.1, .1))

        vv1 = survey_scenario.simulation.calculate_add('salaire_de_base', period = year)
        vv2 = survey_scenario._modified_simulation.calculate_add('salaire_de_base', period = year)

        tv1 = survey_scenario.simulation.calculate_add('revenu_disponible', period = year)
        tv2 = survey_scenario._modified_simulation.calculate_add('revenu_disponible', period = year)

        np.quantile(mtr_rd, q = np.arange(0, 1.1, .1))

    return survey_scenario, aggregates_taxipp.get_data_frame(), aggregates_ines.get_data_frame(), aggregates_france_entiere.get_data_frame()


def test_erfs_fpr_aggregates_reform():
    """Tests aggregates value with data.

    :param year: year of data and simulation to test agregates
    :param reform: optional argument, put an openfisca_france_data.refoms.old_openfisca_france_reforms object, default None
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
@click.option('-y', '--year', 'year', default = REFERENCE_YEAR, help = "ERFS-FPR year", show_default = True,
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
        log.warning(f"Reading years to process from {configfile}, ignoring 'year' input parameter")
        try:
            config = configparser.ConfigParser()
            config.read(configfile)
            for key in config['erfs_fpr']:
                if key.isnumeric():
                    years.append(int(key))
                    log.info(f"Adding year {int(key)}")
        except KeyError:
            years = [year]
            log.warning(f"Key 'erfs_fpr' not found in {configfile}, switching back to year {year}")
    else:
        years = [year]

    for year in years:
        survey_scenario, aggregates_taxipp, aggregates_ines, aggregates_france_entiere = test_erfs_fpr_survey_simulation_aggregates(
            year = year,
            rebuild_input_data = False,
            use_marginal_tax_rate = True,
            variation_factor = relative_variation,
            varying_variable = varying_variable
            )

        df = pd.concat({
            "ines": aggregates_ines,
            "france_entiere": aggregates_france_entiere,
            "taxipp": aggregates_taxipp
            })
        df.to_csv(f'aggregates_erfs_fpr_{year}.csv')

        continue
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
        # dtbl = survey_scenario.create_data_frame_by_entity(vars_to_export, index=True, use_modified=False, merge=True)
        dtbl = survey_scenario.create_data_frame_by_entity(vars_to_export, index=True, merge=True)
        print("Saving to disk")
        dtbl.to_csv(f"dt_baseline_erfs_fpr_{year}.csv")
        gc.collect()

        print("Computing reform data frame")
        # dtrf = survey_scenario.create_data_frame_by_entity(vars_to_export, index=True, use_modified=True, merge=True)
        dtrf = survey_scenario.create_data_frame_by_entity(vars_to_export, index=True, merge=True)
        print("Saving to disk")
        dtrf.to_csv(f"dt_reform_erfs_fpr_{year}.csv")
        gc.collect()

        print("Launching R script..")

        # 'vsc' option necessary to indicate right path to R; the number afterwards is the individual ID for the cas types
        # Note BCO : this code won't work outside a specific env
        # os.system('echo 0070 | sudo -S Rscript ~/Analysis/Debug/MTR-Components_Python.R vsc 42 {} {} {}'.format(varying_variable, target_variable, relative_variation))

        print("All done!")


if __name__ == '__main__':
    log.info("Starting...")
    main()
    log.info("THE END!")

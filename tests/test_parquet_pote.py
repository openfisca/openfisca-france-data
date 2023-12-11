import unittest
import pandas as pd
import os
import logging
import random
import gc
import warnings
from time import time
from multiprocessing import Pool
import pytest

from openfisca_core import periods
from openfisca_survey_manager.survey_collections import SurveyCollection
from openfisca_survey_manager.scripts.build_collection import add_survey_to_collection
from openfisca_survey_manager.scripts.build_collection import build_survey_collection
from openfisca_survey_manager.scenarios.abstract_scenario import AbstractSurveyScenario
from openfisca_france_data import france_data_tax_benefit_system
from openfisca_survey_manager.surveys import NoMoreDataError

tax_benefit_system = france_data_tax_benefit_system
logger = logging.getLogger(__name__)
# Suppress warnings
warnings.filterwarnings("ignore")


class TestParquetPote(unittest.TestCase):
    data_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "test_parquet_pote"
        )
    os.makedirs(data_dir, exist_ok=True)
    collection_name = "test_parquet_collection"
    survey_name = "test_parquet_survey"
    nombre_de_foyers = 60_000_000

    def test_write_fake_pote(self):
        self.nombre_de_foyers = 4
        # key = 'individu',
        individus = pd.DataFrame(
            {
                "foyer_fiscal_id": [3, 0, 0, 1, 2],
                "famille_id": [3, 0, 0, 1, 2],
                "menage_id": [3, 0, 0, 1, 2],
                "age": [26, 77, 37, 80, 33],
                "salaire_de_base": [12_000, 40000, 50000, 0, 10000],
                "retraite_imposable": [0, 0, 0, 10_000, 0],
                "famille_role_index": [0, 0, 1, 0, 0],
                "foyer_fiscal_role_index": [0, 0, 1, 0, 0],
                "menage_role_index": [0, 0, 1, 0, 0],
                "date_naissance": [
                    "1994-01-01",
                    "1943-01-01",
                    "1983-01-01",
                    "2000-01-01",
                    "1987-01-01",
                    ],
                }
            )
        individus.to_parquet(
            os.path.join(self.data_dir, "individu.parquet"), index=False
            )
        # key = 'foyer_fiscal',
        foyers = pd.DataFrame(
            {
                "foyer_fiscal_id": [3, 0, 1, 2],
                "revenus_capitaux_prelevement_forfaitaire_unique_ir": [0, 50_000, 0, 0],
                }
            )
        foyers.to_parquet(
            os.path.join(self.data_dir, "foyer_fiscal.parquet"), index=False
            )

    def write_big_fake_pote(self):
        start = time()
        logger.debug(f"Writing big fake pote with {self.nombre_de_foyers} foyers")
        foyer_fiscal_ids = list(range(self.nombre_de_foyers))
        revenus = [random.randint(0, 100_000) for _ in range(self.nombre_de_foyers)]
        zeros = [0 for _ in range(self.nombre_de_foyers)]
        individus = pd.DataFrame(
            {
                "foyer_fiscal_id": foyer_fiscal_ids,
                "famille_id": foyer_fiscal_ids,
                "menage_id": foyer_fiscal_ids,
                "age": [random.randint(18, 100) for _ in range(self.nombre_de_foyers)],
                "salaire_de_base": revenus,
                "retraite_imposable": revenus,
                "famille_role_index": zeros,
                "foyer_fiscal_role_index": zeros,
                "menage_role_index": zeros,
                # "date_naissance": [
                #     f"{random.randint(1920, 2000)}-01-01" for _ in range(self.nombre_de_foyers)
                #     ],
                }
            )
        individus.to_parquet(
            os.path.join(self.data_dir, "individu.parquet"), index=False
            )
        del individus
        # key = 'foyer_fiscal',
        foyers = pd.DataFrame(
            {
                "foyer_fiscal_id": foyer_fiscal_ids,
                "revenus_capitaux_prelevement_forfaitaire_unique_ir": revenus,
                }
            )
        foyers.to_parquet(
            os.path.join(self.data_dir, "foyer_fiscal.parquet"), index=False
            )
        del foyers
        logger.debug(f"Writing big fake pote done in {time() - start:.2f} seconds.")

    @pytest.mark.order(after="test_write_fake_pote")
    def test_add_collection(self):
        # Create a file config.ini in the current directory
        config = os.path.join(
            self.data_dir,
            "config.ini",
            )
        with open(config, "w") as f:
            f.write(
                f"""
[collections]
collections_directory = {self.data_dir}
{self.collection_name} = {self.data_dir}/{self.collection_name}.json

[data]
output_directory = {self.data_dir}
tmp_directory = /tmp
"""
                )
        # Create a file test_parquet_collection.json in the current directory
        json_file = os.path.join(
            self.data_dir,
            "test_parquet_collection.json",
            )
        with open(json_file, "w") as f:
            f.write(
                """
{
    "label": "Test parquet collection",
    "name": "test_parquet_collection",
    "surveys": {
    }
}
"""
                )

        survey_collection = SurveyCollection(
            name=self.collection_name,
            config_files_directory="./tests/",
            json_file_path="./tests/test_parquet_collection.json",
            )
        survey_file_path = os.path.join(self.data_dir, self.collection_name)
        add_survey_to_collection(
            survey_name=self.survey_name,
            survey_collection=survey_collection,
            parquet_files=[survey_file_path],
            )
        ordered_dict = survey_collection.to_json()
        logger.warning(ordered_dict)
        assert self.survey_name in list(ordered_dict["surveys"].keys())

    @pytest.mark.order(after="test_add_collection")
    def test_build_collection(self):
        collection_name = self.collection_name
        data_directory_path_by_survey_suffix = {
            "2020": os.path.join(self.data_dir),
            }
        build_survey_collection(
            collection_name=collection_name,
            data_directory_path_by_survey_suffix=data_directory_path_by_survey_suffix,
            replace_metadata=False,
            replace_data=False,
            source_format="parquet",
            config_files_directory=self.data_dir,
            )


    def process_one_batch(self, survey_scenario, period, batch_size, batch_index):
        start = time()
        try:
            results = {
                "salaire_imposable": [],
                "irpp_economique": [],
                "csg_deductible_salaire": [],
                "revenus_capitaux_prelevement_forfaitaire_unique_ir": [],
                }
            data = {
                "collection": "test_parquet_collection",
                "survey": "test_parquet_collection_2020",
                "input_data_table_by_entity_by_period": {
                    period: {
                        "foyer_fiscal": "foyer_fiscal",
                        "individu": "individu",
                        "batch_size": batch_size,
                        "batch_index": batch_index,
                        }
                    },
                "config_files_directory": self.data_dir,
                }
            survey_scenario.init_from_data(data=data)

            simulation = survey_scenario.simulations["baseline"]
            sim_res = (
                simulation.calculate("irpp_economique", period.this_year)
                .flatten()
                .tolist()
                )
            results["irpp_economique"] += sim_res
            sim_res = (
                simulation.calculate("salaire_imposable", period).flatten().tolist()
                )
            results["salaire_imposable"] += sim_res
            sim_res = (
                simulation.calculate("csg_deductible_salaire", period)
                .flatten()
                .tolist()
                )
            results["csg_deductible_salaire"] += sim_res
            sim_res = (
                simulation.calculate(
                    "revenus_capitaux_prelevement_forfaitaire_unique_ir", period
                    )
                .flatten()
                .tolist()
                )
            results["revenus_capitaux_prelevement_forfaitaire_unique_ir"] += sim_res

            df_tmp = pd.DataFrame(results)
            df_tmp.to_parquet(
                os.path.join(self.data_dir, f"/tmp/results-{batch_index}.parquet"),
                index=False,
                )
        except NoMoreDataError:
            logger.debug(f"No more data for {batch_index}")
        finally:
            # Free memory
            del results
            del simulation
            gc.collect()
            logger.debug(f"------------------- batch {batch_index} done in { time() - start:.2f} seconds -------------------")

    @pytest.mark.order(after="test_build_collection")
    def test_load_parquet(self):
        temps_debut = time()
        # Create survey scenario
        survey_scenario = AbstractSurveyScenario()
        survey_scenario.set_tax_benefit_systems(dict(baseline=tax_benefit_system))
        survey_scenario.period = 2020
        survey_scenario.used_as_input_variables = [
            "revenus_capitaux_prelevement_forfaitaire_unique_ir",
            "salaire_imposable",
            ]
        survey_scenario.collection = self.collection_name
        period = periods.period("2020-01")

        batch_size = 20_000
        total_batch = (self.nombre_de_foyers // batch_size) + 10
        logger.debug(f"Lancement en paralèlle de {total_batch=} process !")
        # Create a Pool with 4 processes
        with Pool(4) as p:
            results = p.starmap(self.process_one_batch, [(survey_scenario, period, batch_size, batch_index) for batch_index in range(total_batch)])
        logger.debug(f"Temps total : {(time() - temps_debut)/60:.2f} minutes pour {self.nombre_de_foyers} foyers.")
        results = pd.read_parquet(
            os.path.join(self.data_dir, "/tmp/results-*.parquet")
            )
        logger.debug(f"Nombre d'éléments : {len(results)=}")
        assert len(results["salaire_imposable"]) == self.nombre_de_foyers
        logger.debug(f"Temps total : {(time() - temps_debut)/60:.2f} minutes pour {self.nombre_de_foyers} foyers.")


    def test_clean(self):
        os.remove(os.path.join(self.data_dir, "individu.parquet"))
        os.remove(os.path.join(self.data_dir, "foyer_fiscal.parquet"))


if __name__ == "__main__":
    t = TestParquetPote()
    # Create a console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)  # Set level to DEBUG

    # Create a formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    # Add the formatter to the console handler
    console_handler.setFormatter(formatter)

    # Add the console handler to the logger
    logger.addHandler(console_handler)
    logger.setLevel(logging.DEBUG)
    for handler in logger.handlers:
        handler.setLevel(logging.DEBUG)
    # t.test_write_fake_pote()
    # t.write_big_fake_pote()
    # t.test_add_collection()
    # t.test_build_collection()
    t.test_load_parquet()
    # t.test_clean()
    logger.info("Done")

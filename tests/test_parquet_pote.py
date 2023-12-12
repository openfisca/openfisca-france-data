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
import pyarrow.parquet as pq

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
    nombre_de_foyers = 4
    nombre_d_individus = 5
    batch_size = 1

    def test_write_fake_pote(self):
        self.nombre_de_foyers = 4
        self.nombre_d_individus = 5
        # test if folder exist and delete it if it does, then create it
        if os.path.exists(os.path.join( "/tmp","results-individus" )):
            os.system(f"rm -rf {os.path.join( '/tmp','results-individus' )}")
        os.makedirs(os.path.join( "/tmp","results-individus" ), exist_ok=True)
        if os.path.exists(os.path.join( "/tmp","results-foyer_fiscal" )):
            os.system(f"rm -rf {os.path.join( '/tmp','results-foyer_fiscal' )}")
        os.makedirs(os.path.join( "/tmp","results-foyer_fiscal" ), exist_ok=True)
        # key = 'individu',
        individus = pd.DataFrame(
            {
                "foyer_fiscal_id": [0, 1, 1, 2, 3],
                "famille_id": [0, 1, 1, 2, 3],
                "menage_id": [0, 1, 1, 2, 3],
                "age": [26, 77, 37, 80, 33],
                "salaire_de_base": [22_000, 10_000, 40_000, 0, 30_000],  # 112 000
                "retraite_imposable": [0, 0, 0, 10_000, 0],
                "famille_role_index": [0, 0, 1, 0, 0],
                "foyer_fiscal_role_index": [0, 0, 1, 0, 0],
                "menage_role_index": [0, 0, 1, 0, 0],
                "date_naissance": [
                    "1994-01-01",
                    "1943-01-01",
                    "1983-01-01",
                    "1980-01-01",
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
                "foyer_fiscal_id": [0,1, 2, 3],
                "revenus_capitaux_prelevement_forfaitaire_unique_ir": [0, 0, 0, 0], # 50 000
                }
            )
        foyers.to_parquet(
            os.path.join(self.data_dir, "foyer_fiscal.parquet"), index=False
            )

    def write_big_fake_pote(self):
        self.nombre_de_foyers = 1_000_000
        self.nombre_d_individus = self.nombre_de_foyers
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
            config_files_directory=self.data_dir,
            json_file_path= os.path.join(self.data_dir, "test_parquet_collection.json"),
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


    def process_one_batch(self, batch_size=None, batch_index=0):
        logger.debug(f"------------------- batch {batch_size=} {batch_index=} -------------------")
        start = time()
        survey_scenario, period = self._prepare_scenario()
        try:
            simulation = None
            results = {
                "individu": {
                    "salaire_imposable": [],
                    "salaire_de_base": [],
                    "csg_deductible_salaire": [],
                },
                "foyer_fiscal": {
                    "irpp_economique": [],
                    "revenus_capitaux_prelevement_forfaitaire_unique_ir": [],
                    "nbptr": [],
                    "maries_ou_pacses": [],
                    "rbg": [],
                }
            }
            data = {
                "collection": "test_parquet_collection",
                "survey": "test_parquet_collection_2020",
                "used_as_input_variables": [
                    "revenus_capitaux_prelevement_forfaitaire_unique_ir",
                    "salaire_imposable",

                    ],
                "input_data_table_by_entity_by_period": {
                    period: {
                        "foyer_fiscal": "foyer_fiscal",
                        "individu": "individu",
                        'batch_entity': 'foyer_fiscal',
                        'batch_entity_key': 'foyer_fiscal_id',
                        'filtered_entity': 'individu',
                        'filtered_entity_on_key': 'foyer_fiscal_id',
                        }
                    },
                "config_files_directory": self.data_dir,
                }
            if batch_size:
                data["input_data_table_by_entity_by_period"][period]["batch_size"] = batch_size
                data["input_data_table_by_entity_by_period"][period]["batch_index"] = batch_index
            logger.debug(f"batch {batch_index} : {data=}")
            survey_scenario.init_from_data(data=data)

            simulation = survey_scenario.simulations["baseline"]
            sim_res = (
                simulation.calculate("irpp_economique", period.this_year)
                .flatten()
                .tolist()
                )
            results["foyer_fiscal"]["irpp_economique"] += sim_res

            sim_res = (
                simulation.calculate("salaire_imposable", period).flatten().tolist()
                )
            results["individu"]["salaire_imposable"] += sim_res

            sim_res = (
                simulation.calculate("salaire_de_base", period).flatten().tolist()
                )
            results["individu"]["salaire_de_base"] += sim_res

            sim_res = (
                simulation.calculate("nbptr", period.this_year).flatten().tolist()
                )
            results["foyer_fiscal"]["nbptr"] += sim_res

            sim_res = (
                simulation.calculate("rbg", period.this_year).flatten().tolist()
                )
            results["foyer_fiscal"]["rbg"] += sim_res

            sim_res = (
                simulation.calculate("maries_ou_pacses", period.this_year).flatten().tolist()
                )
            results["foyer_fiscal"]["maries_ou_pacses"] += sim_res

            sim_res = (
                simulation.calculate("csg_deductible_salaire", period)
                .flatten()
                .tolist()
                )
            results["individu"]["csg_deductible_salaire"] += sim_res
            sim_res = (
                simulation.calculate(
                    "revenus_capitaux_prelevement_forfaitaire_unique_ir", period
                    )
                .flatten()
                .tolist()
                )
            results["foyer_fiscal"]["revenus_capitaux_prelevement_forfaitaire_unique_ir"] += sim_res

            df_ind = pd.DataFrame(results["individu"])
            df_ind.to_parquet(
                os.path.join(self.data_dir, f"/tmp/results-individus/{batch_index}.parquet"),
                index=False,
                )
            df_foy = pd.DataFrame(results["foyer_fiscal"])
            df_foy.to_parquet(
                os.path.join(self.data_dir, f"/tmp/results-foyer_fiscal/{batch_index}.parquet"),
                index=False,
                )
        except NoMoreDataError:
            logger.debug(f"No more data for {batch_index}")
        except Exception as e:
            logger.error(f"Error for {batch_index}")
            raise e
        finally:
            # Free memory
            del results
            del simulation
            gc.collect()
            logger.debug(f"------------------- batch {batch_index} done in { time() - start:.2f} seconds -------------------")

    def _prepare_scenario(self):
        # Create survey scenario
        survey_scenario = AbstractSurveyScenario()
        survey_scenario.set_tax_benefit_systems(dict(baseline=tax_benefit_system))
        survey_scenario.period = 2020
        survey_scenario.used_as_input_variables = [
            "revenus_capitaux_prelevement_forfaitaire_unique_ir",
            "salaire_de_base",
            ]
        survey_scenario.collection = self.collection_name
        period = periods.period("2020-01")
        return survey_scenario, period

    def _verify_results(self):
        df_ind = pq.ParquetDataset("/tmp/results-individus/", use_legacy_dataset=False).read().to_pandas()
        df_foy = pq.ParquetDataset("/tmp/results-foyer_fiscal/", use_legacy_dataset=False).read().to_pandas()
        self.assertEqual(len(df_ind["salaire_imposable"]), self.nombre_d_individus)
        self.assertEqual(len(df_foy["irpp_economique"]), self.nombre_de_foyers)
        self.assertAlmostEqual(df_foy["revenus_capitaux_prelevement_forfaitaire_unique_ir"].sum(), 50_000, delta=1)
        self.assertAlmostEqual(df_ind["salaire_de_base"].sum(), 112_000, delta=1)
        self.assertAlmostEqual(df_ind["salaire_imposable"].sum(), 96_328, delta=1)
        self.assertAlmostEqual(df_foy["irpp_economique"].sum(), -15_509, delta=1)


    @pytest.mark.order(after="test_build_collection")
    def test_load_parquet_monolithic(self):
        logger.debug("test_load_parquet_monolithic")
        # Create survey scenario
        self.process_one_batch()
        self._verify_results()

    @pytest.mark.order(after="test_build_collection")
    def load_parquet_batch_multiprocessing(self):
        logger.debug("load_parquet_batch_multiprocessing")
        temps_debut = time()
        # Create survey scenario

        batch_size = self.batch_size
        total_batch = (self.nombre_de_foyers // batch_size) + 1
        logger.debug(f"Lancement en paralèlle de {total_batch=} process !")
        # Create a Pool with 4 processes
        with Pool(1) as p:
            results = p.starmap(self.process_one_batch, [(batch_size, batch_index) for batch_index in range(total_batch)])
        logger.debug(f"Temps total : {(time() - temps_debut)/60:.2f} minutes pour {self.nombre_de_foyers} foyers.")
        self._verify_results()

    @pytest.mark.order(after="test_build_collection")
    def load_parquet_batch(self):
        logger.debug("load_parquet_batch")
        temps_debut = time()
        # Create survey scenario
        survey_scenario, period = self._prepare_scenario()
        batch_size = self.batch_size
        total_batch = (self.nombre_de_foyers // batch_size) + 1
        batch_index=0
        while batch_index < total_batch:
            self.process_one_batch(survey_scenario, period, batch_size, batch_index)
            batch_index += 1
        logger.debug(f"Temps total : {(time() - temps_debut)/60:.2f} minutes pour {self.nombre_de_foyers} foyers.")
        self._verify_results()

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
    t.test_write_fake_pote()
    # t.write_big_fake_pote()
    t.test_add_collection()
    t.test_build_collection()
    try:
        # t.load_parquet_batch()
        t.load_parquet_batch_multiprocessing()
        # t.test_load_parquet_monolithic()
    except Exception as e:
        logger.error(e)
    finally:
        df_ind = pq.ParquetDataset("/tmp/results-individus/", use_legacy_dataset=False).read().to_pandas()
        df_foy = pq.ParquetDataset("/tmp/results-foyer_fiscal/", use_legacy_dataset=False).read().to_pandas()
        print(df_ind)
        print(df_foy)
    # t.test_clean()
    logger.info("Done")

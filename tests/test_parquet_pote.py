import unittest
import pandas as pd
import os
import logging

from openfisca_core import periods
from openfisca_survey_manager.survey_collections import SurveyCollection
from openfisca_survey_manager.scripts.build_collection import add_survey_to_collection
from openfisca_survey_manager.scripts.build_collection import build_survey_collection
from openfisca_survey_manager.scenarios.abstract_scenario import AbstractSurveyScenario
from openfisca_france_data import france_data_tax_benefit_system
from openfisca_survey_manager.surveys import NoMoreDataError

tax_benefit_system = france_data_tax_benefit_system
logger = logging.getLogger(__name__)


class TestParquetPote(unittest.TestCase):
    data_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "test_parquet_pote"
        )
    os.makedirs(data_dir, exist_ok=True)
    collection_name = "test_parquet_collection"
    survey_name = "test_parquet_survey"

    def test_write_fake_pote(self):
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

    def test_load_parquet(self):
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
        results = {
            "salaire_imposable": [],
            "irpp_economique": [],
            "csg_deductible_salaire": [],
            "revenus_capitaux_prelevement_forfaitaire_unique_ir": [],
            }
        batch_size = 2
        batch_index = 0
        while True:
            try:
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
                logger.debug("------------------- Next batch -------------------")
                batch_index += 1
            except NoMoreDataError:
                logger.debug("No more data")
                break
        logger.debug(f"{results=}")
        # assert len(results["salaire_imposable"]) == 4
        # assert (
        #     results["salaire_imposable"]
        #     == input_data_frame_by_entity["salaire_imposable"]
        # ).all()
        # assert results["irpp_economique"] == [500.0, 1000.0, 1500.0, 2000.0]
        # assert results["salaire_imposable"] == [
        #     195.00001525878906,
        #     3.0,
        #     510.0000305175781,
        #     600.0,
        #     750.0,
        # ]

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
    print(logger.getEffectiveLevel())
    for handler in logger.handlers:
        print(handler.level)
    logger.info("INFO msg")
    logger.debug("DEBUG msg")
    logger.warning("WARNING msg")
    t.test_write_fake_pote()
    t.test_add_collection()
    t.test_build_collection()
    t.test_load_parquet()
    # t.test_clean()
    logger.info("Done")

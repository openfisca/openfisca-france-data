import unittest
import pandas as pd
import os
import logging

from openfisca_core import periods
from openfisca_survey_manager import (
    openfisca_survey_manager_location,
    default_config_files_directory,
)
from openfisca_survey_manager.survey_collections import SurveyCollection
from openfisca_survey_manager.scripts.build_collection import add_survey_to_collection
from openfisca_survey_manager.scripts.build_collection import build_survey_collection
from openfisca_survey_manager.scenarios.abstract_scenario import AbstractSurveyScenario

# from openfisca_survey_manager.tests import tax_benefit_system
from openfisca_france_data import france_data_tax_benefit_system
from openfisca_survey_manager.surveys import NoMoreDataError

tax_benefit_system = france_data_tax_benefit_system
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


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
                "id": [0, 1],
                "age": [77, 37],
                "salaire_imposable": [20000, 10000],
                "retraite_imposable": [0, 0],
            }
        )
        individus.to_parquet(
            os.path.join(self.data_dir, "individu.parquet"), index=False
        )
        # key = 'foyer_fiscal',
        foyers = pd.DataFrame(
            {
                "id": [0, 1],
                "nb_personnes": [2, 1],
                "nb_parents": [2, 1],
                "nb_enfants": [0, 0],
                "revenu_disponible": [30000, 10000],
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
        survey_name = "test_parquet_collection_2020"
        survey_collection = SurveyCollection.load(
            config_files_directory=self.data_dir,
            collection=self.collection_name,
        )
        survey = survey_collection.get_survey(survey_name)
        table = survey.get_values(table="foyer_fiscal", ignorecase=True)
        # assert len(table) == 4
        # assert (table.columns == ["household_id", "rent", "household_weight", "accommodation_size"]).all()
        # assert table.rent.sum() == 10300

        # Create survey scenario
        survey_scenario = AbstractSurveyScenario()
        input_data_frame_by_entity = table
        survey_scenario.set_tax_benefit_systems(dict(baseline=tax_benefit_system))
        survey_scenario.period = 2020
        survey_scenario.used_as_input_variables = ["salaire_imposable"]
        survey_scenario.collection = self.collection_name
        period = periods.period("2020-01")
        results = {
            "salaire_imposable": [],
            "irpp_economique": [],
            "csg_deductible_salaire": [],
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
                sim_res = simulation.calculate("income_tax", period).flatten().tolist()
                results["income_tax"] += sim_res
                logger.debug("XXXXXXXXXXXXXXXXXXXXXx Next batch XXXXXXXXXXXXXXXXXXXXXx")
                batch_index += 1
            except NoMoreDataError:
                logger.debug("No more data")
                break
        logger.debug(f"{results=}")
        assert len(results["salaire_imposable"]) == 4
        assert (
            results["salaire_imposable"]
            == input_data_frame_by_entity["salaire_imposable"]
        ).all()
        assert results["irpp_economique"] == [500.0, 1000.0, 1500.0, 2000.0]
        assert results["salaire_imposable"] == [
            195.00001525878906,
            3.0,
            510.0000305175781,
            600.0,
            750.0,
        ]

    def test_clean(self):
        os.remove(os.path.join(self.data_dir, "individu.parquet"))
        os.remove(os.path.join(self.data_dir, "foyer_fiscal.parquet"))


if __name__ == "__main__":
    t = TestParquetPote()
    t.test_write_fake_pote()
    t.test_add_collection()
    t.test_build_collection()
    t.test_load_parquet()
    # t.test_clean()
    logger.warning("Done")

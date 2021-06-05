# -*- coding: utf-8 -*-


import os
import pytest
import pandas

from openfisca_core.taxbenefitsystems import TaxBenefitSystem  # type: ignore
from openfisca_france_data import france_data_tax_benefit_system  # type: ignore
from openfisca_france_data.erfs_fpr.scenario import (  # type: ignore
    ErfsFprSurveyScenario,
    )

current_dir = os.path.dirname(os.path.realpath(__file__))

hdf5_file_realpath = os.path.join(
    current_dir,
    "fixtures",
    "erfs",
    "fake_openfisca_input_data.h5",
    )

csv_file_realpath = os.path.join(
    current_dir,
    "fixtures",
    "erfs",
    "fake_openfisca_input_data.csv",
    )


@pytest.fixture
def tax_benefit_system() -> TaxBenefitSystem:
    return france_data_tax_benefit_system


@pytest.fixture
def survey_scenario(tax_benefit_system: TaxBenefitSystem):
    def _survey_scenario(year: int) -> ErfsFprSurveyScenario:
        return ErfsFprSurveyScenario.create(
            tax_benefit_system = tax_benefit_system,
            year = year,
            )

    return _survey_scenario


@pytest.fixture
def fake_input_data():
    def _fake_input_data_frame(year: int) -> pandas.DataFrame:
        try:
            input_data_frame = pandas.read_hdf(hdf5_file_realpath, key = str(year))

        except Exception:
            input_data_frame = pandas.read_csv(csv_file_realpath)

        input_data_frame.rename(
            columns = dict(
                sali = "salaire_imposable",
                choi = "chomage_imposable",
                rsti = "retraite_imposable",
                ),
            inplace = True,
            )

        input_data_frame.loc[0, "salaire_imposable"] = 20000
        input_data_frame.loc[1, "salaire_imposable"] = 10000

        for idx in range(2, 6):
            input_data_frame.loc[idx] = input_data_frame.loc[1].copy()
            input_data_frame.loc[idx, "salaire_imposable"] = 0
            input_data_frame.loc[idx, "quifam"] = 2
            input_data_frame.loc[idx, "quifoy"] = 2
            input_data_frame.loc[idx, "quimen"] = 2

            if idx < 4:
                input_data_frame.loc[idx, "age"] = 10

            else:
                input_data_frame.loc[idx, "age"] = 24
                input_data_frame.loc[idx, "age"] = 24

        input_data_frame.reset_index(inplace = True)

        return input_data_frame

    return _fake_input_data_frame

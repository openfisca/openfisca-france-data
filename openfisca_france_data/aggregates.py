import collections
import logging
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pkg_resources


from openfisca_survey_manager.aggregates import AbstractAggregates
from openfisca_france_data import AGGREGATES_DEFAULT_VARS  # type: ignore


log = logging.getLogger(__name__)


class FranceAggregates(AbstractAggregates):
    labels = collections.OrderedDict((
        ('label', "Mesure"),
        ('entity', "Entité"),
        ('reform_amount', "Dépenses\n(millions d'€)"),
        ('reform_beneficiaries', "Bénéficiaires\n(milliers)"),
        ('baseline_amount', "Dépenses initiales\n(millions d'€)"),
        ('baseline_beneficiaries', "Bénéficiaires\ninitiaux\n(milliers)"),
        ('actual_amount', "Dépenses\nréelles\n(millions d'€)"),
        ('actual_beneficiaries', "Bénéficiaires\nréels\n(milliers)"),
        ('amount_absolute_difference', "Diff. absolue\nDépenses\n(millions d'€)"),
        ('beneficiaries_absolute_difference', "Diff absolue\nBénéficiaires\n(milliers)"),
        ('amount_relative_difference', "Diff. relative\nDépenses"),
        ('beneficiaries_relative_difference', "Diff. relative\nBénéficiaires"),
        ))
    aggregate_variables = AGGREGATES_DEFAULT_VARS
    target_source = None

    def __init__(self, survey_scenario = None, target_source = None):
        super().__init__(survey_scenario = survey_scenario)
        self.target_source = target_source

    def load_actual_data(self, year = None):
        target_source = self.target_source
        assert target_source in ["ines", "taxipp"], "les options possible pour source_cible sont ines ou taxipp"
        assert year is not None

        if target_source == "taxipp":
            taxipp_aggregates_file = Path(
                pkg_resources.get_distribution("openfisca-france_data").location,
                "openfisca_france_data",
                "assets",
                "aggregats",
                "taxipp",
                "agregats_tests_taxipp_2_0.xlsx"
                )
            df = (
                pd.read_excel(
                    taxipp_aggregates_file,
                    # "https://gitlab.com/ipp/partage-public-ipp/taxipp/-/blob/master/simulation/assets/agregats_tests_taxipp_2_0.xlsx",
                    # engine = 'openpyxl'
                    )
                .rename(columns = str.lower)
                .rename(columns = {"unnamed: 0": "description"})
                .dropna(subset = ["annee 2019", "annee 2018", "annee 2017", "annee 2016"], how = "all")
                )
            if f"annee {year}" not in df:
                return

            df = (
                df[["variable_openfisca", f"annee {year}"]]
                .dropna()
                .rename(columns = {
                    "variable_openfisca": "variable",
                    f"annee {year}": year,
                    })
                )

            beneficiaries = (
                df.loc[df.variable.str.startswith("nombre")]
                .set_index("variable")
                .rename(index = lambda x : x.replace("nombre_", ""))
                .rename(columns = {year: "actual_beneficiaries"})
                ) / self.beneficiaries_unit

            amounts = (
                df.loc[~df.variable.str.startswith("nombre")]
                .set_index("variable")
                .rename(columns = {year: "actual_amount"})
                ) / self.amount_unit

            result = amounts.merge(beneficiaries, on = "variable", how = "outer").drop("PAS SIMULE")

        elif target_source == "ines":
            ines_aggregates_file = Path(
                pkg_resources.get_distribution("openfisca-france_data").location,
                "openfisca_france_data",
                "assets",
                "aggregats",
                "ines",
                f"ines_{year}.json"
                )

            with open(ines_aggregates_file, 'r') as f:
                data = json.load(f)

            result = pd.DataFrame(data['data']).drop('notes', axis = 1)
            result['actual_beneficiaries'] = result. actual_beneficiaries / self.beneficiaries_unit
            result['actual_amount'] = result. actual_amount / self.amount_unit

            result = result[["variable","actual_amount","actual_beneficiaries"]].set_index("variable")

        return result

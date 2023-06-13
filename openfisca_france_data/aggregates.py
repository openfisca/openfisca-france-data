import collections
from datetime import datetime
import logging
import os
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

    def load_actual_data(self, year = None):
        assert year is not None
        taxipp_aggregates_file = Path(
            pkg_resources.get_distribution("openfisca-france-data").location,
            "openfisca_france_data",
            "assets",
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
        return result

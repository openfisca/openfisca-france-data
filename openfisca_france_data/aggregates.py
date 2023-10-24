import collections
import logging
import json
from pathlib import Path

import os
from datetime import datetime
import pandas as pd

from openfisca_survey_manager.aggregates import AbstractAggregates
from openfisca_france_data import openfisca_france_data_location, AGGREGATES_DEFAULT_VARS  # type: ignore


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

    def load_actual_data(self, period = None):
        target_source = self.target_source
        assert target_source in ["ines", "taxipp", "france_entiere"], "les options possible pour source_cible sont ines, taxipp ou france_entiere"
        assert period is not None

        if target_source == "taxipp":
            taxipp_aggregates_file = Path(
                openfisca_france_data_location,
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
            if f"annee {period}" not in df:
                return

            df = (
                df[["variable_openfisca", f"annee {period}"]]
                .dropna()
                .rename(columns = {
                    "variable_openfisca": "variable",
                    f"annee {period}": period,
                    })
                )

            beneficiaries = (
                df.loc[df.variable.str.startswith("nombre")]
                .set_index("variable")
                .rename(index = lambda x : x.replace("nombre_", ""))
                .rename(columns = {period: "actual_beneficiaries"})
                ) / self.beneficiaries_unit

            amounts = (
                df.loc[~df.variable.str.startswith("nombre")]
                .set_index("variable")
                .rename(columns = {period: "actual_amount"})
                ) / self.amount_unit

            result = amounts.merge(beneficiaries, on = "variable", how = "outer").drop("PAS SIMULE")

        elif target_source == "ines":
            ines_aggregates_file = Path(
                openfisca_france_data_location,
                "openfisca_france_data",
                "assets",
                "aggregats",
                "ines",
                f"ines_{period}.json"
                )

            with open(ines_aggregates_file, 'r') as f:
                data = json.load(f)

            result = pd.DataFrame(data['data']).drop('notes', axis = 1)
            result['actual_beneficiaries'] = result. actual_beneficiaries / self.beneficiaries_unit
            result['actual_amount'] = result. actual_amount / self.amount_unit

            result = result[["variable","actual_amount","actual_beneficiaries"]].set_index("variable")

        elif target_source == "france_entiere":
            ines_aggregates_file = Path(
                openfisca_france_data_location,
                "openfisca_france_data",
                "assets",
                "aggregats",
                "france_entiere",
                f"france_entiere_{period}.json"
                )

            with open(ines_aggregates_file, 'r') as f:
                data = json.load(f)

            result = pd.DataFrame(data['data']).drop(['source'], axis = 1)
            result['actual_beneficiaries'] = result. actual_beneficiaries / self.beneficiaries_unit
            result['actual_amount'] = result.actual_amount / self.amount_unit

            result = result[[
                "variable",
                "actual_amount",
                "actual_beneficiaries",
                ]].set_index("variable")

        return result

    def to_csv(self, path = None, absolute = True, amount = True, beneficiaries = True, default = 'actual',
            relative = True, target = "reform"):
        """Saves the table to csv."""
        assert path is not None

        if os.path.isdir(path):
            now = datetime.now()
            file_path = os.path.join(path, 'Aggregates_%s_%s_%s.%s' % (self.target_source, self.period, now.strftime('%d-%m-%Y'), "csv"))
        else:
            file_path = path

        df = self.get_data_frame(
            absolute = absolute,
            amount = amount,
            beneficiaries = beneficiaries,
            default = default,
            relative = relative,
            target = target,
            )
        df.to_csv(file_path, index = False, header = True)

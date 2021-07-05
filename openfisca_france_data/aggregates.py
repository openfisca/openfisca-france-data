import collections
from datetime import datetime
import logging
import os

import numpy as np
import pandas as pd

try:
    from ipp_macro_series_parser.config import Config  # type: ignore
except ImportError:
    Config = None

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

        if not Config:
            log.info("No actual data available")
            return

        parser = Config()

        # Cotisations CSG -CRDS
        try:
            directory = os.path.join(
                parser.get('data', 'prelevements_sociaux_directory'),
                'clean',
                )
            csg_crds_amounts = pd.read_csv(
                os.path.join(directory, 'recette_csg_crds.csv'),
                index_col = 0
                ).rename(
                    dict(
                        recette_csg = 'csg',
                        recette_crds = 'crds',
                        )
                    ) / 1e6
            csg_by_type_amounts = pd.read_csv(
                os.path.join(directory, 'recette_csg_by_type.csv'),
                index_col = 0,
                ).drop(
                    ['source']
                    ).astype(float) / 1e6
            assiette_csg_by_type_amounts = pd.read_csv(
                os.path.join(directory, 'assiette_csg_by_type.csv'),
                index_col = 0,
                ) / 1e6
        except Exception:
            assiette_csg_by_type_amounts = None
            csg_by_type_amounts = None
            csg_crds_amounts = None
            pass
        # Prestations sociales
        directory = os.path.join(
            parser.get('data', 'prestations_sociales_directory'),
            'clean',
            )
        amounts_csv = os.path.join(directory, 'historique_depenses.csv')
        beneficiaries_csv = os.path.join(directory, 'historique_beneficiaires.csv')
        prestations_sociales_amounts = pd.read_csv(amounts_csv, index_col = 0)
        prestations_sociales_beneficiaries = pd.read_csv(beneficiaries_csv, index_col = 0)
        # Minimum vieillesses
        minimum_vieillesse_beneficiaries_csv = os.path.join(
            directory, 'historique_beneficiaires_minimum_vieillesse.csv')
        if os.path.exists(minimum_vieillesse_beneficiaries_csv):
            minimum_vieillesse_beneficiaries = pd.read_csv(minimum_vieillesse_beneficiaries_csv, index_col = 0)

        amounts = pd.concat(
            [
                assiette_csg_by_type_amounts,
                csg_by_type_amounts,
                csg_crds_amounts,
                prestations_sociales_amounts,
                ],
            sort = True,
            )
        beneficiaries = pd.concat(
            [minimum_vieillesse_beneficiaries, prestations_sociales_beneficiaries],
            sort = True,
            )

        return pd.DataFrame(data = {
            "actual_amount": amounts[str(year)],
            "actual_beneficiaries": beneficiaries[str(year)],
            })

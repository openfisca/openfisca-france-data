# -*- coding: utf-8 -*-


from typing import Union

from openfisca_core.reforms import Reform  # type: ignore
from openfisca_core.taxbenefitsystems import TaxBenefitSystem  # type: ignore

from openfisca_france_data.erfs_fpr.scenario import ErfsFprSurveyScenario
from openfisca_france_data import france_data_tax_benefit_system


def get_survey_scenario(
        year = 2012,
        rebuild_input_data = False,
        tax_benefit_system = None,
        baseline_tax_benefit_system = None,
        data = None,
        reform = None
        ):
    '''Helper pour créer un :class:`ErfsFprSurveyScenario`.

    :param year:                        L'année des données de l'enquête.
    :param rebuild_input_data:          Si l'on doit formatter les données (raw) ou pas.
    :param tax_benefit_system:          Le :class:`TaxBenefitSystem` déjà réformé.
    :param baseline_tax_benefit_system: Le :class:`TaxBenefitSystem` au droit courant.
    :param data:                        Les données de l'enquête.
    :param reform:                      Une réforme à appliquer à *france_data_tax_benefit_system*.
    '''
    tax_benefit_system: TaxBenefitSystem = get_tax_benefit_system(
        default_tax_benefit_system = france_data_tax_benefit_system,
        tax_benefit_system = tax_benefit_system,
        reform = reform,
        )

    baseline_tax_benefit_system: TaxBenefitSystem = get_baseline_tax_benefit_system(
        default_tax_benefit_system = tax_benefit_system,
        tax_benefit_system = baseline_tax_benefit_system,
        )

    survey_scenario = ErfsFprSurveyScenario.create(
        tax_benefit_system = tax_benefit_system,
        baseline_tax_benefit_system = baseline_tax_benefit_system,
        year = year,
        )

    # S'il n'y a pas de données, on sait où les trouver.
    if data is None:
        data = dict(
            input_data_table = dict(),
            input_data_survey_prefix = 'openfisca_erfs_fpr_data',
            )

    # Les données peuvent venir en différents formats :
    #
    #  * Pandas' DataFrame
    #  * CSV
    #  * HDF5
    #  * Etc.
    #
    #  .. seealso:: :func:`ErfsFprSurveyScenario.init_from_data`
    survey_scenario.init_from_data(
        data = data,
        rebuild_input_data = rebuild_input_data,
        )
    return survey_scenario


def get_tax_benefit_system(
        default_tax_benefit_system: TaxBenefitSystem,
        tax_benefit_system: Union[TaxBenefitSystem, None],
        reform: Union[Reform, None],
        ) -> TaxBenefitSystem:

    if isinstance(tax_benefit_system, TaxBenefitSystem):
        return tax_benefit_system

    if not isinstance(default_tax_benefit_system, TaxBenefitSystem):
        raise(TypeError("'default_tax_benefit_system' doit être du type 'TaxBenefitSystem"))

    if isinstance(reform, Reform):
        return reform(default_tax_benefit_system)

    return default_tax_benefit_system


def get_baseline_tax_benefit_system(
        default_tax_benefit_system: Union[TaxBenefitSystem, None],
        tax_benefit_system: Union[TaxBenefitSystem, None],
        ) -> TaxBenefitSystem:
    if isinstance(tax_benefit_system, TaxBenefitSystem):
        return tax_benefit_system

    if not isinstance(default_tax_benefit_system, TaxBenefitSystem):
        raise(TypeError("'default_tax_benefit_system' doit être du type 'TaxBenefitSystem"))

    return default_tax_benefit_system

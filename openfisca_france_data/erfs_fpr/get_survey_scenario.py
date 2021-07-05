from typing import Any, Optional

from multipledispatch import dispatch  # type: ignore

from openfisca_core.reforms import Reform  # type: ignore
from openfisca_core.taxbenefitsystems import TaxBenefitSystem  # type: ignore

from openfisca_france_data.erfs_fpr.scenario import ErfsFprSurveyScenario
from openfisca_france_data import france_data_tax_benefit_system


def get_survey_scenario(
        year: int = 2014,
        rebuild_input_data: bool = False,
        tax_benefit_system: Optional[TaxBenefitSystem] = None,
        baseline_tax_benefit_system: Optional[TaxBenefitSystem] = None,
        data: Any = None,  # Plusiers formats possibles.
        reform: Optional[Reform] = None,
        use_marginal_tax_rate: bool = False,
        variation_factor: float = 0.03,
        varying_variable: str = None,
        ) -> ErfsFprSurveyScenario:
    """Helper pour créer un `ErfsFprSurveyScenario`.

    :param year:                        L'année des données de l'enquête.
    :param rebuild_input_data:          Si l'on doit formatter les données (raw) ou pas.
    :param tax_benefit_system:          Le `TaxBenefitSystem` déjà réformé.
    :param baseline_tax_benefit_system: Le `TaxBenefitSystem` au droit courant.
    :param data:                        Les données de l'enquête.
    :param reform:                      Une réforme à appliquer à *france_data_tax_benefit_system*.
    """
    tax_benefit_system = get_tax_benefit_system(
        tax_benefit_system,
        reform,
        )

    baseline_tax_benefit_system = get_baseline_tax_benefit_system(
        baseline_tax_benefit_system,
        )

    if not use_marginal_tax_rate:
        survey_scenario = ErfsFprSurveyScenario.create(
            tax_benefit_system = tax_benefit_system,
            baseline_tax_benefit_system = baseline_tax_benefit_system,
            year = year,
            )
    else:
        assert varying_variable is not None, "You need to specify the varying variable."
        survey_scenario = ErfsFprSurveyScenario.create(
            tax_benefit_system = tax_benefit_system,
            baseline_tax_benefit_system = baseline_tax_benefit_system,
            year = year,
            )
        survey_scenario.variation_factor = variation_factor
        survey_scenario.varying_variable = varying_variable

    # S'il n'y a pas de données, on sait où les trouver.
    if data is None:
        input_data_table_by_entity = dict(
            individu = f"individu_{year}",
            menage = f"menage_{year}",
            )

        input_data_table_by_entity_by_period = dict()
        input_data_table_by_entity_by_period[year] = input_data_table_by_entity

        data = dict(
            input_data_table_by_entity_by_period = input_data_table_by_entity_by_period,
            # input_data_survey_prefix = "openfisca_erfs_fpr_data",
            survey = "input"
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
        use_marginal_tax_rate = use_marginal_tax_rate,
        )

    return survey_scenario


# Appelé quand *tax_benefit_system* est un :class:`TaxBenefitSystem`
@dispatch(TaxBenefitSystem, object)  # noqa: F811
def get_tax_benefit_system(
        tax_benefit_system: TaxBenefitSystem,
        reform: Optional[None],
        ) -> TaxBenefitSystem:
    return tax_benefit_system


# Appelé quand *tax_benefit_system* est `None`, mais *reform* est une :class:`Reform`
@dispatch(object, Reform)  # noqa: F811
def get_tax_benefit_system(
        tax_benefit_system: None,
        reform: Reform,
        ) -> TaxBenefitSystem:
    return reform(france_data_tax_benefit_system)


# Appelé quand *tax_benefit_system* et *reform* sont `None`
@dispatch(object, object)  # noqa: F811
def get_tax_benefit_system(
        tax_benefit_system: None,
        reform: None,
        ) -> TaxBenefitSystem:
    return france_data_tax_benefit_system


# Appelé quand *tax_benefit_system* est un :class:`TaxBenefitSystem`
@dispatch(TaxBenefitSystem)  # noqa: F811
def get_baseline_tax_benefit_system(
        tax_benefit_system: TaxBenefitSystem,
        ) -> TaxBenefitSystem:
    return tax_benefit_system


# Appelé quand *tax_benefit_system* est `None`
@dispatch(object)  # noqa: F811
def get_baseline_tax_benefit_system(
        tax_benefit_system: None,
        ) -> TaxBenefitSystem:
    return france_data_tax_benefit_system

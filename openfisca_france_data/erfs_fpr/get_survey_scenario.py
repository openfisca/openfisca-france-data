from typing import Any, Optional

from multipledispatch import dispatch  # type: ignore

from openfisca_core.model_api import Variable, ADD, YEAR
from openfisca_core.reforms import Reform  # type: ignore
from openfisca_core.taxbenefitsystems import TaxBenefitSystem  # type: ignore

from openfisca_france.entities import Individu, FoyerFiscal, Menage
from openfisca_france_data.erfs_fpr.scenario import ErfsFprSurveyScenario
from openfisca_france_data import france_data_tax_benefit_system

from openfisca_survey_manager import default_config_files_directory

from openfisca_france_data.model.id_variables import (
    idmen_original,
    noindiv,
    )

variables_converted_to_annual = [
    "salaire_imposable",
    "chomage_imposable",
    "retraite_imposable",
    "salaire_net",
    "chomage_net",
    "retraite_nette",
    "ppa",
    ]


menage_projected_variables = [

]


class erfs_fpr_plugin(Reform):
    name = "ERFS-FPR ids plugin"

    def apply(self):

        for variable in variables_converted_to_annual:
            class_name =  f"{variable}_annuel"
            label = f"{variable} sur l'année entière"

            def annual_formula_creator(variable):
                def formula(individu, period):
                    result = individu(variable, period, options = [ADD])
                    return result

                formula.__name__ = 'formula'

                return formula

            variable_instance = type(class_name, (Variable,), dict(
                value_type = float,
                entity = self.variables[variable].entity,
                label = label,
                definition_period = YEAR,
                formula = annual_formula_creator(variable),
                ))

            self.add_variable(variable_instance)
            del variable_instance

        for variable in menage_projected_variables:
            class_name =  f"{variable}_menage"
            label = f"{variable} agrégée à l'échelle du ménage"

            def projection_formula_creator(variable):
                def formula(menage, period):
                    result_i = menage.members.foyer_fiscal(variable, period, options = [ADD])
                    result = menage.sum(result_i, role = FoyerFiscal.DECLARANT_PRINCIPAL)
                    return result

                formula.__name__ = 'formula'

                return formula

            variable_instance = type(class_name, (Variable,), dict(
                value_type = float,
                entity = Menage,
                label = label,
                definition_period = YEAR,
                formula = projection_formula_creator(variable),
                ))

            self.add_variable(variable_instance)
            del variable_instance


        self.add_variable(idmen_original)
        self.add_variable(noindiv)


def get_survey_scenario(
        year: int = None,
        rebuild_input_data: bool = False,
        tax_benefit_system: Optional[TaxBenefitSystem] = None,
        baseline_tax_benefit_system: Optional[TaxBenefitSystem] = None,
        data: Any = None,  # Plusiers formats possibles.
        reform: Optional[Reform] = None,
        use_marginal_tax_rate: bool = False,
        variation_factor: float = 0.03,
        varying_variable: str = None,
        survey_name: str = "input",
        config_files_directory : str = default_config_files_directory,
        ) -> ErfsFprSurveyScenario:
    """Helper pour créer un `ErfsFprSurveyScenario`.

    :param year:                        L'année des données de l'enquête.
    :param rebuild_input_data:          Si l'on doit formatter les données (raw) ou pas.
    :param tax_benefit_system:          Le `TaxBenefitSystem` déjà réformé.
    :param baseline_tax_benefit_system: Le `TaxBenefitSystem` au droit courant.
    :param data:                        Les données de l'enquête.
    :param reform:                      Une réforme à appliquer à *france_data_tax_benefit_system*.
    """
    assert year is not None
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
            period = year,
            )
    else:
        assert varying_variable is not None, "You need to specify the varying variable."
        survey_scenario = ErfsFprSurveyScenario.create(
            tax_benefit_system = tax_benefit_system,
            baseline_tax_benefit_system = baseline_tax_benefit_system,
            period = year,
            )
        # taux marginaux !!
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
            survey = survey_name
            )
        data["config_files_directory"] = config_files_directory
        

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
    return reform(erfs_fpr_plugin(france_data_tax_benefit_system))


# Appelé quand *tax_benefit_system* et *reform* sont `None`
@dispatch(object, object)  # noqa: F811
def get_tax_benefit_system(
        tax_benefit_system: None,
        reform: None,
        ) -> TaxBenefitSystem:
    return erfs_fpr_plugin(france_data_tax_benefit_system)


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
    return erfs_fpr_plugin(france_data_tax_benefit_system)

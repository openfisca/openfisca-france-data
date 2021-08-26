import logging
import pandas

from typing import Optional

from openfisca_core import periods  # type: ignore
from openfisca_core.model_api import Enum  # type: ignore
from openfisca_core.taxbenefitsystems import TaxBenefitSystem  # type: ignore
from openfisca_france_data import base_survey as base  # type: ignore
from openfisca_survey_manager.scenarios import AbstractSurveyScenario  # type: ignore

log = logging.getLogger(__name__)


class AbstractErfsSurveyScenario(AbstractSurveyScenario):
    """
    Parties communes entre ERFS et ERFS PFR

    Note : beaucoup de mix entre milléssime, à nettoyer à un moment donné
    """

    id_variable_by_entity_key = dict(
        famille = "idfam",
        foyer_fiscal = "idfoy",
        menage = "idmen",
        )

    filtering_variable_by_entity = dict(
        famille = "menage_ordinaire_familles",
        foyer_fiscal = "menage_ordinaire_foyers_fiscaux",
        individu = "menage_ordinaire_individus",
        menage = "menage_ordinaire",
        )

    role_variable_by_entity_key = dict(
        famille = "quifam",
        foyer_fiscal = "quifoy",
        menage = "quimen",
        )

    weight_variable_by_entity = dict(
        menage = "wprm",
        famille = "weight_familles",
        foyer_fiscal = "weight_foyers",
        individu = "weight_individus",
        )

    def build_input_data_from_test_case(self, test_case_scenario):
        for axe in test_case_scenario["axes"][0]:
            axe["name"] = "salaire_imposable_pour_inversion"

        tax_benefit_system = self.tax_benefit_system

        simulation = (
            tax_benefit_system
            .new_scenario()
            .init_single_entity(**test_case_scenario)
            .new_simulation()
            )

        array_by_variable = dict()
        period = periods.period(str(self.year))

        for variable in self.used_as_input_variables:
            array_by_variable[variable] = simulation.calculate_add(
                variable,
                period = period,
                )

        for ident in ["idmen", "idfoy", "idfam"]:
            array_by_variable[ident] = range(axe["count"])

        input_data_frame = pandas.DataFrame(array_by_variable)

        for qui in ["quimen", "quifoy", "quifam"]:
            input_data_frame[qui] = 0

        return input_data_frame

    @classmethod
    def create(
            cls,
            tax_benefit_system: Optional[TaxBenefitSystem] = None,
            baseline_tax_benefit_system: Optional[TaxBenefitSystem] = None,
            input_data_type = None,
            reform = None,
            reform_key = None,
            year: int = None,
            ):

        assert year is not None
        assert not ((reform is not None) and (reform_key is not None))

        reform_is_provided = (reform is not None) or (reform_key is not None)
        # With booleans != is xor
        # See https://stackoverflow.com/questions/432842/how-do-you-get-the-logical-xor-of-two-variables-in-python # noqa: E501
        assert reform_is_provided != (tax_benefit_system is not None)

        if reform_is_provided:
            assert baseline_tax_benefit_system is not None

        if reform_key is not None:
            reform = base.get_cached_reform(
                reform_key = reform_key,
                tax_benefit_system = baseline_tax_benefit_system,
                )

        if reform is not None:
            tax_benefit_system = reform

        if input_data_type is not None:
            survey_scenario = cls(input_data_type = input_data_type, year = year)

        else:
            survey_scenario = cls(year = year)

        survey_scenario.set_tax_benefit_systems(
            tax_benefit_system = tax_benefit_system,
            baseline_tax_benefit_system = baseline_tax_benefit_system,
            )

        survey_scenario.year = year

        return survey_scenario

    def init_from_test_case(self, test_case_scenario = None):
        assert test_case_scenario is not None
        input_data_frame = self.build_input_data_from_test_case(test_case_scenario)
        self.init_from_data_frame(input_data_frame = input_data_frame)
        self.new_simulation()

        if self.baseline_tax_benefit_system is not None:
            self.new_simulation(use_baseline = True)

    def custom_initialize(self, simulation):
        input_variables = [
            "categorie_salarie",
            "contrat_de_travail",
            "effectif_entreprise",
            "heures_remunerees_volume",
            # 'hsup',
            "pensions_alimentaires_percues",
            ]

        computed_variables_used_as_input =  [
            # 'chomage_brut',
            "chomage_imposable",
            "retraite_brute",
            "retraite_imposable",
            "salaire_de_base",
            ]

        three_year_span_variables = input_variables + computed_variables_used_as_input

        simulation_period = periods.period(self.year)
        for variable in three_year_span_variables:
            assert variable in self.used_as_input_variables, \
                f"{variable} is not a in the input_varaibles to be used {self.used_as_input_variables}"  # noqa: E501

            if self.tax_benefit_system.variables[variable].value_type == Enum:
                permanent_value = simulation.calculate(
                    variable,
                    period = periods.period(self.year).first_month,
                    )
            else:
                permanent_value = simulation.calculate_add(
                    variable,
                    period = self.year,
                    )

            for offset in [-1, -2]:
                try:
                    simulation.set_input(
                        variable,
                        simulation_period.offset(offset),
                        permanent_value
                        )
                except ValueError as e:
                    log.debug(f"Dealing with: {e}")
                    if sum(simulation.calculate_add(variable, simulation_period.offset(offset))) != sum(permanent_value):
                        use_baseline = self.baseline_simulation == simulation
                        simulation.delete_arrays(variable, simulation_period.offset(offset))
                        simulation.set_input(
                            variable,
                            simulation_period.offset(offset),
                            permanent_value
                            )


    def custom_input_data_frame(self, input_data_frame, **kwargs):
        if "loyer" in input_data_frame:
            input_data_frame["loyer"] = 12 * input_data_frame.loyer

        if "categorie_salarie" in input_data_frame:
            log.debug("Setting categorie_salarie to 0 and 1 only")
            input_data_frame.loc[
                input_data_frame.categorie_salarie.isin(range(2, 7)),
                "categorie_salarie",
                ] = 1

        for variable in ["quifam", "quifoy", "quimen"]:
            if variable in input_data_frame:
                log.debug(input_data_frame[variable].value_counts(dropna = False))

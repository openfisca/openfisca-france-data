from openfisca_core.taxbenefitsystems import TaxBenefitSystem
from openfisca_core import periods
from openfisca_survey_manager.scenarios.abstract_scenario import AbstractSurveyScenario
from openfisca_survey_manager.survey_collections import SurveyCollection
from openfisca_france_data.pote.annualisation_variables import AnnualisationVariablesIR
import openfisca_france
import numpy as np

openfisca_france_tax_benefit_system = openfisca_france.FranceTaxBenefitSystem()
var_create_in_custom_input_data_frame = ["caseL", "caseN","caseP","caseF","caseW","caseS","caseG","caseT", "nbR", "jeune_veuf", "depcom_foyer"]
# variables créées dans le custom_input_data_frame ci dessous à rajouter dans les used_as_input_variables du survey_scenario

class PoteSurveyScenario(AbstractSurveyScenario):

    def __init__(
        self,
        config_files_directory,
        annee_donnees: int = 2022,
        period: int = 2022,
        rebuild_input_data: bool = False, # pour l'instant il n'y a pas de builder propre
        init_from_data : bool = True,
        baseline_tax_benefit_system: TaxBenefitSystem = AnnualisationVariablesIR(openfisca_france_tax_benefit_system),
        used_as_input_variables = None,
        data = None,
        collection: str = "pote",
        survey_name: str = None,
        batch_size: int = None,
        batch_index: int = 0,
        filter_by = None, # [(f'foyer_fiscal_id', 'in', [i for i in range(batch_size*batch_index,(batch_size*batch_index) + batch_size)])]
        do_custom_input_data_frame: bool = True,
    ):
        self.collection = collection
        self.annee_donnees = annee_donnees
        self.period = period
        self.tax_benefit_systems = {'baseline':baseline_tax_benefit_system}
        self.do_custom_input_data_frame = do_custom_input_data_frame

        assert not ((batch_size is not None) and (filter_by is not None)), "Il faut choisir entre une simulation par batch et un filter_by"

        if survey_name is None:
            survey_name = f"{collection}_{annee_donnees}"

        if data is None:
            survey_collection = SurveyCollection.load(
                collection = collection,
                config_files_directory = config_files_directory
                )
            survey = survey_collection.get_survey(survey_name)

            data = {"input_data_table_by_entity_by_period":{}, "survey":survey_name}
            data["config_files_directory"] = config_files_directory
            data["custom_input_data_frame"] = self.custom_input_data_frame
            if batch_size is not None:
                assert batch_index is not None, "Pour faire la simulation sur un morceau des données il faut définir batch_index"
                data["input_data_table_by_entity_by_period"][int(self.annee_donnees)] = {
                    'batch_size':batch_size,
                    'batch_index':batch_index,
                    'batch_entity':'foyer_fiscal',
                    'batch_entity_key':'foyer_fiscal_id',
                    'filtered_entity':'individu',
                    'filtered_entity_on_key':'foyer_fiscal_id',
                }
            elif filter_by is not None:
                data["input_data_table_by_entity_by_period"][int(self.annee_donnees)] = {'filter_by':filter_by}
            else:
                data["input_data_table_by_entity_by_period"][int(self.annee_donnees)] = {}

            if used_as_input_variables is None:
                input_variable = list()
            for table_name, table in survey.tables.items():
                current_year = table_name[-4:]
                if current_year.isnumeric():
                    current_year = int(current_year)
                    entity = table_name[:-5]
                    if current_year == self.annee_donnees:
                        data["input_data_table_by_entity_by_period"][current_year][
                            entity
                        ] = table_name
                if used_as_input_variables is None:
                    input_variable += table["variables"]
        self.data = data
        if used_as_input_variables is None:
            variables_in_tax_benefit_system = list(openfisca_france_tax_benefit_system.variables.keys())
            var_to_keep = list(set(variables_in_tax_benefit_system) & set(input_variable))
            self.used_as_input_variables = var_to_keep + var_create_in_custom_input_data_frame
        else:
            self.used_as_input_variables = used_as_input_variables
        if init_from_data:
            self.simulations = dict()
            self.init_from_data(
                data=data,
                rebuild_input_data=rebuild_input_data,
            )
    def init_from_data(self, rebuild_input_data=False, data=None):
        if rebuild_input_data:
            print("Rebuild input data is not implemented yet")

        self.simulation = dict()
        period = periods.period(self.annee_donnees)

        for prefix, tax_benefit_system in self.tax_benefit_systems.items():
            self.new_simulation(
                simulation_name=prefix,
                data = self.data,
            )

    def custom_input_data_frame(self, input_data_frame, period, entity = None):
        if self.do_custom_input_data_frame:
            if entity == 'foyer_fiscal':
            ## gestions des cases demi part supplémentaires
                for case in ['L', 'N', 'P', 'F', 'W', 'S', 'G', 'T']:
                    if f"case{case}" in input_data_frame.columns:
                        input_data_frame[f"case{case}"] = np.where(input_data_frame[f"z{case.lower()}"] == case, True, False)
                        input_data_frame.drop([f"z{case.lower()}"], axis = 1, inplace = True)
                if "zr" in input_data_frame.columns:
                    input_data_frame["nbR"] = input_data_frame.zr
                    input_data_frame.drop(["zr"],axis = 1, inplace = True)
                if "zz" in input_data_frame.columns:
                    input_data_frame["jeune_veuf"] = np.where(input_data_frame.zz == "Z", True, False) # jeune_veuf = deces du conjoint dans l'annee des revenus
                    input_data_frame.drop(["zz"],axis = 1, inplace = True)
                if "iddep" in input_data_frame.columns:
                    input_data_frame.rename(columns = {'iddep':'depcom_foyer'},inplace = True)

                input_data_frame["foyer_fiscal_id"] = range(len(input_data_frame))

from openfisca_survey_manager.survey_collections import SurveyCollection
from openfisca_france_data.pote.input_data_builder.step_00_variables_pote import create_pote_openfisca_variables_list
from openfisca_france_data.pote.input_data_builder.step_01_create_individus import build_individus
from openfisca_france_data.pote.input_data_builder.step_02_a_create_table_presimulation import create_table_foyer_fiscal_preparation
from openfisca_france_data.pote.input_data_builder.step_02_b_simulation_credits_reductions import simulation_preparation_credits_reductions
from openfisca_france_data.pote.input_data_builder.step_02_c_create_table_foyer_fiscal import create_table_foyer_fiscal
from openfisca_france_data.pote.input_data_builder.analyse_variables import liens_variables
import logging
import os
import shutil

year = 2022
chunk_size = 1000000
nrange = 42
config_files_directory = "C:/Users/Public/Documents/TRAVAIL/Pote_openfisca/.config/openfisca-survey-manager/"

survey = SurveyCollection(name = 'raw_pote', config_files_directory = config_files_directory)
raw_data_directory = survey.config.get('data','raw_pote')
output_path = survey.config.get('data','output_directory')
tmp_directory = survey.config.get('data','tmp_directory')
pote_colonne_file_path = survey.config.get('openfisca_france_data_pote','pote_colonne_file_path')
errors_path = survey.config.get('openfisca_france_data_pote','errors_path')
logging.basicConfig(filename=f"{errors_path}builder_log.log", encoding = 'utf-8')
# if os.path.exists(tmp_directory):
#     shutil.rmtree(tmp_directory)
# os.mkdir(tmp_directory)

if not os.path.exists(os.path.join(output_path,"foyer_fiscal")):
    os.mkdir(os.path.join(output_path,"foyer_fiscal"))
if not os.path.exists(os.path.join(output_path,"individu")):
    os.mkdir(os.path.join(output_path,"individu"))

variables_individu, variables_foyer_fiscal = create_pote_openfisca_variables_list(year, errors_path, pote_colonne_file_path)

variables_to_compute, enfants_tot, dictionnaire_enfant_parents, dictionnaire_parent_enfants = liens_variables(year)

build_individus(year, chunk_size, variables_individu, config_files_directory, raw_data_directory, output_path, errors_path, nrange)
create_table_foyer_fiscal_preparation(raw_data_directory, year, output_path, config_files_directory, variables_to_compute, dictionnaire_parent_enfants, tmp_directory)
simulation_preparation_credits_reductions(config_files_directory, variables_to_compute, dictionnaire_parent_enfants, tmp_directory)
create_table_foyer_fiscal(raw_data_directory, variables_foyer_fiscal, year, output_path, config_files_directory, variables_to_compute, dictionnaire_parent_enfants, tmp_directory)

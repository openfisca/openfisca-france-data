from openfisca_france_data.pote.survey_scenario import PoteSurveyScenario
import pyarrow.parquet as pq
import gc
import os
import shutil


def simulation_preparation_credits_reductions(config_files_directory, variables_to_compute, dictionnaire_parent_enfants, tmp_directory):
    print("Etape 2 - b Simulation des cases de crédits et réductions d'impot")
    tmp_tmp_directory = f"{tmp_directory}temp_simulations_intermediaires/"
    if not os.path.exists(tmp_directory):
        os.mkdir(tmp_directory)
    length = 40185996 # nombre de ligne de POTE, TODO : à améliorer
    for variable_to_compute in variables_to_compute[1:]:
        print(f"Etape 2 - b Simulation de : {variable_to_compute}")
        if os.path.exists(tmp_tmp_directory):
            shutil.rmtree(tmp_tmp_directory)
        os.mkdir(tmp_tmp_directory)
        # if len(dictionnaire_parent_enfants[variable_to_compute]) < 30:
        #     batch_size = 5000000
        # elif (len(dictionnaire_parent_enfants[variable_to_compute]) >= 30) and (len(dictionnaire_parent_enfants[variable_to_compute]) < 60):
        #     batch_size = 1000000
        # else:
        #     batch_size = 500000
        filter_size = 5000000
        print(f"batch size : {filter_size}")
        for i in range((length//filter_size) + 1):
            filter_by = [(f'foyer_fiscal_id', 'in', [j for j in range(filter_size*i,(filter_size*i) + filter_size)])]
            survey_scenario = PoteSurveyScenario(config_files_directory = config_files_directory,
                                                collection = "pote",
                                                survey_name = f"pote-{variable_to_compute}",
                                                filter_by = filter_by,
                                                do_custom_input_data_frame = False)
            df = survey_scenario.simulations['baseline'].create_data_frame_by_entity([variable_to_compute],period = 2021)['foyer_fiscal']
            df[[variable_to_compute]].to_parquet(f"{tmp_tmp_directory}{variable_to_compute}_{i}.parquet")
            del survey_scenario
            del df
            gc.collect()
        all = pq.read_table(tmp_tmp_directory)
        #print(f"Enregistrement table {variable_to_compute}, nombre de lignes : {len(all)}")
        pq.write_table(all,f"{tmp_directory}{variable_to_compute}.parquet")
        shutil.rmtree(tmp_tmp_directory)

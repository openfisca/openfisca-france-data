import pyarrow.parquet as pq
import gc
import os
import shutil
from openfisca_france_data.pote.survey_scenario import PoteSurveyScenario

def simulation_preparation_credits_reductions(year,config_files_directory, variables_to_compute, dictionnaire_parent_enfants, tmp_directory, pote_length, log):
    '''
    Il s'agit de calculer les variables qui sont des sommes de cases fiscales appelées qu'une seule fois. C'est notamment le cas de variables de réductions et crédits d'impôts
    Ce sont les variables intermédiaires issues de ces simulations qui seront utilisées comme variable d'entrée des simulations avec POTE
    '''

    log.info("----- Etape 2 - b Simulation des cases de crédits et réductions d'impot -----")
    tmp_tmp_directory = os.path.join(tmp_directory,"temp_simulations_intermediaires")
    if not os.path.exists(tmp_directory):
        os.mkdir(tmp_directory)
    for variable_to_compute in variables_to_compute:
        log.info(f" - Simulation de : {variable_to_compute}")
        if os.path.exists(tmp_tmp_directory):
            shutil.rmtree(tmp_tmp_directory)
        os.mkdir(tmp_tmp_directory)
        filter_size = 5_000_000
        for i in range((pote_length//filter_size) + 1):
            filter_by = [(f'foyer_fiscal_id', 'in', [j for j in range(filter_size*i,(filter_size*i) + filter_size)])]
            survey_scenario = PoteSurveyScenario(config_files_directory = config_files_directory,
                                                 annee_donnees = year,
                                                 period = year,
                                                 collection = "pote",
                                                 survey_name = f"pote-{variable_to_compute}",
                                                 filter_by = filter_by,
                                                 do_custom_input_data_frame = False)
            df = survey_scenario.simulations['baseline'].create_data_frame_by_entity([variable_to_compute],period = year)['foyer_fiscal']
            df[[variable_to_compute]].to_parquet(os.path.join(tmp_tmp_directory,f"{variable_to_compute}_{i}.parquet"))
            del survey_scenario
            del df
            gc.collect()
        all = pq.read_table(tmp_tmp_directory)
        pq.write_table(all,os.path.join(tmp_directory,f"{variable_to_compute}.parquet"))
        shutil.rmtree(tmp_tmp_directory)

    log.info("----- Fin de l'Etape 2 - b -----")

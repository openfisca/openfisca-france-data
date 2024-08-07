
import os
import pyarrow.parquet as pq
import gc
from openfisca_survey_manager.survey_collections import SurveyCollection
from openfisca_survey_manager.surveys import Survey

individus_columns = ["foyer_fiscal_id","foyer_fiscal_role_index","famille_id","menage_id","famille_role_index","menage_role_index"]

def create_table_foyer_fiscal_preparation(raw_data_directory, year, output_path, config_files_directory, variables_to_compute, dictionnaire_parent_enfants, tmp_directory, log):
    '''
    Création de table de variables foyer fiscal pour réaliser des simulations intermédiaires (étape 2b) afin de réduire le nombre de colones dans les tables d'entrée
    '''

    log.info("----- Etape 2 - a Préparation des tables intermédiaires foyer fiscal -----")

    tmp_output_path = os.path.join(tmp_directory,"tmp_foyer_fiscal")
    if not os.path.exists(tmp_output_path):
        os.mkdir(tmp_output_path)

    survey_collection = SurveyCollection.load(collection = "pote", config_files_directory=config_files_directory)
    final_ind_parquet_file =  f"{tmp_output_path}/individu-preparation.parquet"
    table_individus = pq.read_table(f"{output_path}individu/", columns = individus_columns)
    pq.write_table(table_individus, final_ind_parquet_file)
    del table_individus
    gc.collect()
    a = 0
    for variable_to_compute in variables_to_compute:
        a = a +1
        log.info(f" - round {a} sur {len(variables_to_compute)}, variable {variable_to_compute}")
        columns_list = ["foyer_fiscal_id"]
        inputs = dictionnaire_parent_enfants[variable_to_compute]
        i = 0
        create_ids = True
        for input in inputs:
            col = "z" + input[1:]
            file_path = f"{raw_data_directory}pote_{col}.parquet"
            if os.path.exists(file_path):
                columns_list.append(input)
                if i == 0:
                    final_table =  pq.read_table(file_path)
                    final_table = final_table.rename_columns([input])
                    if create_ids:
                        final_table = final_table.append_column("foyer_fiscal_id", [[x for x in range(final_table.num_rows)]])
                        ids = final_table.column(1)
                        create_ids = False
                    else: final_table = final_table.append_column("foyer_fiscal_id", ids)
                    i = 1
                else:
                    table = pq.read_table(file_path)
                    final_table = final_table.append_column(input,table.column(0).combine_chunks())
        final_parquet_file =  f"{tmp_output_path}/foyer_fiscal-{variable_to_compute}.parquet"
        pq.write_table(final_table, final_parquet_file)
        del final_table
        gc.collect()
        survey = Survey(
            name = f"pote-{variable_to_compute}",
            label = None,
            survey_collection = survey_collection,
            parquet_file_path = tmp_directory
            )
        survey.parquet_file_path = output_path
        survey.tables[f"foyer_fiscal_{year}"] = {
            "source_format":"parquet",
            "variables":columns_list,
            "parquet_file":final_parquet_file,
        }
        survey.tables[f"individu_{year}"] = {
            "source_format":"parquet",
            "variables":individus_columns,
            "parquet_file":final_ind_parquet_file,
            }
        survey_collection.surveys = [kept_survey for kept_survey in survey_collection.surveys if kept_survey.name != f"pote-{variable_to_compute}"]
        survey_collection.surveys.append(survey)
        collections_directory = survey_collection.config.get('collections', 'collections_directory')
        collection_json_path = os.path.join(collections_directory, "pote.json")
        survey_collection.dump(json_file_path=collection_json_path)

    log.info("----- Fin de l'Etape 2 - a -----")

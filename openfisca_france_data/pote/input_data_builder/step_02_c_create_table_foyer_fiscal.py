

print("Importing modules...")
import collections
import os
import pandas as pd
from os.path import exists
from openfisca_survey_manager.tables import Table
from openfisca_survey_manager.survey_collections import SurveyCollection
import pyarrow.parquet as pq
import pyarrow as pa
import gc
import tracemalloc
from openfisca_france_data.pote.input_data_builder.analyse_variables import liens_variables

tracemalloc.start()

non_nul = pd.read_json("C:/Users/Public/Documents/donnees_brutes/POTE/parquet_columns/2021/columns_stats_desc.json")

def create_table_foyer_fiscal(raw_data_directory, variables_foyer_fiscal, year, output_path, config_files_directory, variables_to_compute, dictionnaire_parent_enfants, tmp_directory):
    print("Etape 2 - c : Création de la table foyer fiscal d'input")
    columns_list = ["foyer_fiscal_id"]#list()
    i = 0
    create_ids = True
    for variable_to_compute in variables_to_compute:
        print(f"***** variable {variable_to_compute} *****")
        file_path = f"{tmp_directory}{variable_to_compute}.parquet"
        if exists(file_path):
            columns_list.append(variable_to_compute)
            if i == 0:
                final_table =  pq.read_table(file_path)
                if create_ids:
                    final_table = final_table.append_column("foyer_fiscal_id", [[x for x in range(final_table.num_rows)]])
                    ids = final_table.column(1)
                    create_ids = False
                else: final_table = final_table.append_column("foyer_fiscal_id", ids)
                i = 1
            else:
                table = pq.read_table(file_path)
                final_table = final_table.append_column(variable_to_compute,table.column(0))

    variables_a_enlever = []
    for var in variables_to_compute:
        variables_a_enlever += dictionnaire_parent_enfants[var]
    
    columns_demi_part = {"zl":None, "zn":None, "zp":None, "zf":None, "zw":None, "zs":None, "zg":None,"zt":None,"zr":None,"zz":None,"iddep":None} # "dadokz":None,
    variables_foyer_fiscal.update(columns_demi_part)
    final_parquet_files = list()
    first_col = final_table.column_names[0]
    for openfisca_var, cerfa in variables_foyer_fiscal.items():
        if openfisca_var not in variables_a_enlever:
            if cerfa is not None:
                col = "z" + cerfa[1:]
            else:
                col = openfisca_var
            file_path = f"{raw_data_directory}pote_{col}.parquet"
            if col == "zr":
                file_path = f"{raw_data_directory}pote_r.parquet"
            if exists(file_path):
                col2 = col
                if col == "zr":
                    col2 ="r"
                if non_nul[col2].nombre_na < (40185996 - 10000): ## pour l'isntant on trie car on n'arrive pas à tout prendre donc on prend que si concerne au moins 10000 personnes
                    print(f"colonne {col}")
                    columns_list.append(openfisca_var)

                    if i == 0:
                        first_col = col
                        final_table =  pq.read_table(file_path)
                        final_table = final_table.rename_columns([openfisca_var])
                        final_table = final_table.append_column("foyer_fiscal_id", [[x for x in range(final_table.num_rows)]])
                        i = 1
                    else:
                        table = pq.read_table(file_path)
                        final_table = final_table.append_column(openfisca_var,table.column(0))

                        #snapshot_avant = tracemalloc.take_snapshot()

                        pool = pa.default_memory_pool()
                        pool.release_unused()
                        print("*********")
                        print(f"Pool bytes {pool.bytes_allocated():,} max memory {pool.max_memory():,}")
                        i = i+1
                        if pool.bytes_allocated() > 40_000_000_000:
                            print("*** Saving to disk ***")
                            final_parquet_file =  f"{output_path}foyer_fiscal/foyer_fiscal-from-{first_col}-to-{col}-{i}.parquet"
                            pq.write_table(final_table, final_parquet_file)
                            final_parquet_files += [final_parquet_file]
                            del final_table, table
                            gc.collect()
                            i = 0
                        print("************")
                print("=======================")
    print("*** Saving to disk ***")
    final_parquet_file =  f"{output_path}foyer_fiscal/foyer_fiscal-from-{first_col}-to-{col}-{i}.parquet"
    pq.write_table(final_table, final_parquet_file)
    final_parquet_files += [final_parquet_file]
    if len(final_parquet_files) == 1:
        final_parquet_files = final_parquet_files[0]

    survey_collection = SurveyCollection.load(collection = "pote", config_files_directory=config_files_directory)
    survey = survey_collection.get_survey(f"pote_{year}")
    survey.tables[f"foyer_fiscal_{year}"] = {
       "source_format":"parquet",
       "variables":columns_list,
       "parquet_file":final_parquet_files,
    }
    survey_collection.surveys = [kept_survey for kept_survey in survey_collection.surveys if kept_survey.name != f"pote_{year}"]
    survey_collection.surveys.append(survey)
    collections_directory = survey_collection.config.get('collections', 'collections_directory')
    collection_json_path = os.path.join(collections_directory, "pote.json")
    survey_collection.dump(json_file_path=collection_json_path)

    # shutil.rmtree(tmp_directory)

import glob
import os
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq
import tracemalloc
from openfisca_survey_manager.survey_collections import SurveyCollection

tracemalloc.start()

def create_table_foyer_fiscal(raw_data_directory, variables_foyer_fiscal, year, output_path, config_files_directory, log):
    log.info("----- Etape 2 : Préparation de la table foyer fiscal d'input ------")
    columns_list = ["foyer_fiscal_id"]
    i = 0
    # columns_demi_part = {"zl":None, "zn":None, "zp":None, "zf":None, "zw":None, "zs":None, "zg":None,"zt":None,"zr":None,"zz":None,"iddep":None} # "dadokz":None,
    columns_demi_part = {"caseL":"zl", "caseN":"zn", "caseP":"zp", "caseF":"zf", "caseW":"zw", "caseS":"zs", "caseG":"zg","caseT":"zt","nbR":"r"} #,"iddep":None
    variables_foyer_fiscal.update(columns_demi_part)
    raw_pote_tables = glob.glob(os.path.join(raw_data_directory,"*.parquet"))
    dict_col_tables = {}
    for table in raw_pote_tables:
        columns = pq.read_schema(table).names
        for column in columns:
            if column in dict_col_tables.keys():
                print(f"ATTENTION : La colonne {column} apparait plusieurs fois dans POTE")
            dict_col_tables[column] = table
    for openfisca_var, cerfa in variables_foyer_fiscal.items():
        if cerfa is not None:
            if len(cerfa)==4:
                col = "Z" + cerfa[1:]
            else:
                col = cerfa
        else:
            col = openfisca_var
        if col in dict_col_tables.keys():
            file_path = dict_col_tables[col]
            columns_list.append(openfisca_var)
            final_table =  pq.read_table(file_path, columns = [col])
            final_table = final_table.rename_columns([openfisca_var])
            if openfisca_var in ["caseL","caseN", "caseP", "caseF", "caseW", "caseS", "caseG", "caseT"]:
                case = openfisca_var[4]
                final_table = final_table.set_column(0,openfisca_var,pc.equal(final_table[openfisca_var], case))
            final_parquet_file =  os.path.join(output_path,f"foyer_fiscal/{openfisca_var}.parquet")
            pq.write_table(final_table, final_parquet_file)
            if i == 0:
                foyer_fiscaux_ids = pa.array([x for x in range(final_table.num_rows)])
                pq.write_table(pa.Table.from_arrays([foyer_fiscaux_ids], names = ["foyer_fiscal_id"]), f"{output_path}foyer_fiscal/foyer_fiscal_id.parquet")
                i = 1

    survey_collection = SurveyCollection.load(collection = "pote", config_files_directory=config_files_directory)
    survey = survey_collection.get_survey(f"pote_{year}")
    survey.tables[f"foyer_fiscal_{year}"] = {
       "source_format":"parquet",
       "variables":columns_list,
       "parquet_file":f"{output_path}foyer_fiscal/",
    }
    survey_collection.surveys = [kept_survey for kept_survey in survey_collection.surveys if kept_survey.name != f"pote_{year}"]
    survey_collection.surveys.append(survey)
    collections_directory = survey_collection.config.get('collections', 'collections_directory')
    collection_json_path = os.path.join(collections_directory, "pote.json")
    survey_collection.dump(json_file_path=collection_json_path)

    log.info("----- Fin de l'Etape 2 -----")

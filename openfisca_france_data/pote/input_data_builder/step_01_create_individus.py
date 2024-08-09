import pandas as pd
from os.path import exists
import os
from pyarrow.parquet import ParquetFile
import pyarrow as pa
import numpy as np
from openfisca_survey_manager.surveys import Survey
from openfisca_survey_manager.survey_collections import SurveyCollection

def build_individus(year, chunk_size, variables_individu,config_files_directory, raw_data_directory, output_path, errors_path, nrange, log):
    '''
    Création d'une table individu (une ligne par individu) à partir de POTE (une ligne par foyer fiscal)

    '''
    log.info("----- Etape 1 : construction de la base individus -----")

    columns = ["aged","agec", "mat", "f","h","r","j","n","g","i","nbfoy", "dnpa4c"]
    #f = nombre d'enfants mineur et g compris dans f nombre avec carte invalidite
    #h = nombre enfants résidence alternée et i compris dans h nb invalides
    #r = nombre de personnes invalides à charge
    #j = nombre enfant majeur celib
    #n = nombre enfant majeur marie / pacse
    #p = nb petits enfants rattachés alternance
    #dnpa4c : annnees de naissances de tous les pacs (y compris les majeurs par ex)


    columns_iter = dict()
    for col in columns:
        pf = ParquetFile(f"{raw_data_directory}pote_{col}.parquet")
        columns_iter[col] = pf.iter_batches(batch_size = chunk_size)

    # récupération des colonnes de POTE qui sont dans les cerfa d'openfisca france
    columns_revenus_iter = dict()
    for openfisca_var, cerfa in variables_individu.items():
        for c in cerfa:
            col = "z" + c[1:]
            if exists(f"{raw_data_directory}pote_{col}.parquet"):
                pf = ParquetFile(f"{raw_data_directory}pote_{col}.parquet")
                columns_revenus_iter[c] = pf.iter_batches(batch_size = chunk_size)

    mat_na = list() # liste des foyers avec une situation matrimoniale manquante
    date_naiss_decl_na = list() # liste des foyers avec la date de naissance du déclarant manquante
    incoherence_date_naiss_1 = list() # liste des foyers célibataire / divorcé / veuf avec une date de naissance du conjoint --> Peut être des cas de divorce / décès ??
    incoherence_date_naiss_2 = list() # liste des foyers marié / pacsés sans date naissance du conjoint
    pb_pacs = {"g":list(),
               "i":list(),
               "f":list(),
               "h":list(),
               "j":list(),
               "n":list(),
               "r":list()}
    incoherence_revenus = list()

    # script par batch par limite de la capacité sur le CASD
    for i in range(nrange):
        log.info(f" - Début du round {i} sur {nrange - 1}")
        df = pd.DataFrame()
        for col in columns:
            first_rows = next(columns_iter[col])
            df_col = pa.Table.from_batches([first_rows]).to_pandas()
            df[col] = df_col

     # 1) création des individus déclarants et conjoint si existant
        df["foyer_fiscal_id"] = [j + i * chunk_size for j in range(len(df))]
        df_indiv = df[["foyer_fiscal_id","mat","aged",'agec']]
        ## tests
        mat_na = mat_na + list(df_indiv.loc[df_indiv['mat'].isna()].foyer_fiscal_id)
        date_naiss_decl_na = date_naiss_decl_na + list(df_indiv.loc[df_indiv['aged'].isna()].foyer_fiscal_id)
        incoherence_date_naiss_1 = incoherence_date_naiss_1 + list(df_indiv.loc[(df_indiv['mat'].isin(['C','D','V'])) & (df_indiv['agec'].notna())].foyer_fiscal_id)
        incoherence_date_naiss_2 = incoherence_date_naiss_2 + list(df_indiv.loc[(df_indiv['mat'].isin(['M','O'])) & (df_indiv['agec'].isna())].foyer_fiscal_id)

        df_indiv = pd.melt(df_indiv, id_vars=["foyer_fiscal_id","mat"], value_vars=["aged","agec"], var_name="var_age", value_name="date_naissance")
        df_indiv.drop(df_indiv[df_indiv["date_naissance"].isna()].index,inplace = True)
        df_indiv["foyer_fiscal_role_index"] = np.where(df_indiv.var_age == "aged",0,1)
        df_indiv.sort_values(['foyer_fiscal_id',"foyer_fiscal_role_index"], inplace = True)
        df_indiv.drop("var_age",axis = 1,inplace = True)
        df_indiv["statut_marital"] = np.where(df_indiv['mat'] == 'M',1,0)
        df_indiv["statut_marital"] = np.where(df_indiv['mat'] == 'C',2,df_indiv["statut_marital"])
        df_indiv["statut_marital"] = np.where(df_indiv['mat'] == 'D',3,df_indiv["statut_marital"])
        df_indiv["statut_marital"] = np.where(df_indiv['mat'] == 'V',4,df_indiv["statut_marital"])
        df_indiv["statut_marital"] = np.where(df_indiv['mat'] == 'O',5,df_indiv["statut_marital"])
        df_indiv["rang"] = df_indiv.sort_values(by=["foyer_fiscal_id","foyer_fiscal_role_index"]).groupby("foyer_fiscal_id").cumcount()

    # 2) création du nombre d'individus pac
        df_pac = df[["foyer_fiscal_id","dnpa4c"]].copy()
        nb_pac_max = max([round(len(i)/5) if i is not None else 0 for i in df_pac.dnpa4c])
        value_vars = []
        for n in range(1,(nb_pac_max + 1)):
            start = 5*(n-1)
            stop = 5*n
            df_pac[f"pac{n}"] = [i[start:stop] if (i is not None ) else "" for i in df_pac.dnpa4c]
            value_vars += [f"pac{n}"]
        df_pac = pd.melt(df_pac, id_vars=["foyer_fiscal_id"], value_vars=value_vars, var_name="pac", value_name="date_naissance")
        df_pac = df_pac.loc[df_pac["date_naissance"] != ""]
        df_pac["rang"] = df_pac.sort_values(by=["foyer_fiscal_id","date_naissance"]).groupby("foyer_fiscal_id").cumcount() + 2
        df_pac["case"] = [i[0] for i in df_pac.date_naissance]
        df_pac["date_naissance"] = [int(i[1:5]) for i in df_pac.date_naissance]
        df_pac["foyer_fiscal_role_index"] = 2
        df_pac["garde_alternee"] = np.where(df_pac.case.isin(["H","I"]),True,False)
        df_pac["invalidite"] = np.where(df_pac.case.isin(["G","I"]),True,False)
        df_pac["handicap"] = np.where(df_pac["case"] == "G",True,False)
        df_pac["handicap"] = np.where((df_pac["case"] == "F") * (df_pac["date_naissance"] <= year - 19),True,df_pac["handicap"])
        df_pac.drop(["pac"], axis = 1, inplace = True)
        df_pac['case'] = [str.lower(i) for i in df_pac.case]

        ## tests
        test = pd.DataFrame(df_pac.groupby(["foyer_fiscal_id","case"])["date_naissance"].count())
        test.reset_index(inplace = True)
        for c in["g","i","f", "h", "j", "n", "r"]:
            test2 = test.loc[test["case"] == c]
            test2 = pd.merge(test2,df.loc[df[str.lower(c)].isna() == False][["foyer_fiscal_id", str.lower(c)]], on = "foyer_fiscal_id")
            test2['test'] = test2[c] - test2["date_naissance"]
            pb_pacs[c] = pb_pacs[c] + list(test2.loc[test2['test'] != 0].foyer_fiscal_id)
        del test
        del test2

        df_indiv["garde_alternee"] = False
        df_indiv["invalidite"] = False
        df_indiv["handicap"] = False

        df_indiv = pd.concat([df_indiv,df_pac])

    # 3) récupération des variables de revenus individuels pour les individus identifiés dans l'étape précédente
        revenus_individu = pd.DataFrame()
        for openfisca_var, cerfa in variables_individu.items():
            table_temp = pd.DataFrame()
            rang = 0
            value_vars = list()
            for c in cerfa:
                if c in list(columns_revenus_iter.keys()):
                    selected_rows = next(columns_revenus_iter[c])
                    df_col = pa.Table.from_batches([selected_rows]).to_pandas()
                    table_temp[str(rang)] = df_col.fillna(0)
                    value_vars += str(rang)
                    rang +=1
            table_temp["foyer_fiscal_id"] = [j + i * chunk_size for j in range(len(df))]
            table_temp =  pd.melt(table_temp, id_vars=["foyer_fiscal_id"], value_vars=value_vars, var_name="rang", value_name=openfisca_var)
            if len(revenus_individu) == 0:
                revenus_individu = table_temp
                revenus_individu['tot'] = abs(revenus_individu[openfisca_var])
            else:
                revenus_individu = pd.merge(revenus_individu, table_temp, on = ["foyer_fiscal_id", "rang"], how = "outer")
                revenus_individu['tot'] = abs(revenus_individu[openfisca_var].fillna(0)) + revenus_individu['tot'].fillna(0)
        revenus_individu['rang'] = revenus_individu.rang.astype(int)
        revenus_individu = revenus_individu.loc[(revenus_individu.tot > 0) | (revenus_individu.rang == 0)].drop("tot", axis = 1)

        ## tests
        test_revenus = pd.DataFrame()
        test_revenus["indiv"] = df_indiv.sort_values("foyer_fiscal_id").groupby("foyer_fiscal_id").rang.max()
        test_revenus["revenus"] = revenus_individu.sort_values("foyer_fiscal_id").groupby("foyer_fiscal_id").rang.max()
        incoherence_revenus = incoherence_revenus + list(test_revenus.loc[test_revenus.indiv<test_revenus.revenus].index)

        revenus_individu = pd.merge(df_indiv, revenus_individu,on = ["foyer_fiscal_id", "rang"], how = 'left').fillna(0)
        revenus_individu = revenus_individu.drop('rang', axis = 1)

        revenus_individu["date_naissance"] = revenus_individu["date_naissance"].astype('int')
        revenus_individu["date_naissance"] = np.where((revenus_individu["date_naissance"] > 1900) & (revenus_individu["date_naissance"] <2022),revenus_individu["date_naissance"],1975)
        revenus_individu["date_naissance"] = pd.to_datetime(
            pd.DataFrame({"year":revenus_individu["date_naissance"],
            'month':"01",
            "day":"01",
            })
        )
        revenus_individu.drop(["mat","case"], axis = 1, inplace = True )

        revenus_individu['famille_id'] = revenus_individu.foyer_fiscal_id
        revenus_individu['menage_id'] = revenus_individu.foyer_fiscal_id
        revenus_individu['famille_role_index'] = revenus_individu.foyer_fiscal_role_index
        revenus_individu['menage_role_index'] = revenus_individu.foyer_fiscal_role_index

        revenus_individu.to_parquet(f"{output_path}individu/individu_{i}.parquet")

        if i == nrange - 1:
            columns = revenus_individu.columns

    survey = Survey(
        name =  f"pote_{year}",
        label = None,
        parquet_file_path = output_path
        )
    survey.tables[f"individu_{year}"] = {
        "source_format":"parquet",
        "variables":[c for c in columns],
        "parquet_file":f"{output_path}individu/",
        }
    survey_collection = SurveyCollection(name = 'pote', config_files_directory = config_files_directory)
    collections_directory = survey_collection.config.get('collections', 'collections_directory')
    collection_json_path = os.path.join(collections_directory, "pote.json")
    if os.path.exists(collection_json_path):
        survey_collection = SurveyCollection.load(collection = 'pote', config_files_directory = config_files_directory)
    survey_collection.surveys = [kept_survey for kept_survey in survey_collection.surveys if kept_survey.name != f"pote_{year}"]
    survey_collection.surveys.append(survey)
    survey_collection.dump(json_file_path=collection_json_path)

    log.info("----- Fin de l'Etape 1 -----")
    # errors_ids = {
    #     'mat_na':[mat_na], # un peu crade on met dans une liste pour exporter en json via pandas (donc avec meme nombre d'élements) car le paquet json par sur le casd so far
    #     'date_naiss_decl_na':[date_naiss_decl_na],
    #     'incoherence_date_naiss_1':[incoherence_date_naiss_1],
    #     'incoherence_date_naiss_2':[incoherence_date_naiss_2],
    #     'pb_pacs':[pb_pacs],
    #     'incoherence_revenus':[incoherence_revenus]
    # }
    # logging.warning(f"{len(mat_na)} foyers n'ont pas de situation matrimoniale de renseignée")
    # logging.warning(f"{len(date_naiss_decl_na)} foyers n'ont pas de date de naissance pour le déclarant")
    # logging.warning(f"{len(incoherence_date_naiss_1)} foyers ont une date de naissance du conjoint renseignée à tord")
    # logging.warning(f"{len(incoherence_date_naiss_2)} foyers ont une date de naissance du conjoint manquante à tord")
    # for c, ids in pb_pacs.items():
    #     logging.warning(f"{len(ids)} foyers ont une incohérence dans leur nombre de pacs {c}")
    # logging.warning(f"{len(incoherence_revenus)} foyers ont une incohérence entre le nombre de personnes et les revenus déclarés")
    # pd.DataFrame(errors_ids).to_json(f"{errors_path}errors_create_individus.json")

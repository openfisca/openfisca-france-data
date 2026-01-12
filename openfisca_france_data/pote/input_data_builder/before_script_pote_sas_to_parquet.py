"""
Ce script converti le fichier SAS de POTE en format parquet dans deux structures distinctes : 
- Environs 3 000 fichiers parquets qui contiennent chacun toutes les colonnes mais seulement 100 000 lignes
- Un fichier par colonne avec toutes les lignes.
- Un fichier Excel de statistiques descriptives des colonnes.
"""
import pandas as pd
import json
import gc
import glob
import os
import pyarrow.parquet as pq
import pyarrow.compute as pc

def pote_sas_to_parquet(year, sas_pote_path, chunks_path, columns_path):

    sas_file = f"{os.path.join(sas_pote_path,year)},pote_diff_{year}.sas7bdat"

    chunks_path = os.path.join(chunks_path, year)
    columns_path = os.path.join(columns_path, year)
    taille_chunk = 100_000

    dfi = pd.read_sas(
        sas_file, chunksize=taille_chunk, encoding="iso8859-15", iterator=True
    )

    # 1) on fait des chunks au format parquet de la table complète en SAS.
    i = 0
    for chunk in dfi:
        chunk.columns = [c.lower() for c in chunk.columns.to_list()]
        chunk.drop(["fip18_c"], axis=1, inplace=True)
        chunk.to_parquet(f"{chunks_path}/pote_{i}.parquet")
        del chunk
        gc.collect()

    # 2) On lit tous les chunks pour faire une table parquet par colonne
    parquet_file = glob.glob(os.path.join(chunks_path, "*.parquet"))

    dfv = pq.ParquetDataset(parquet_file)

    column_names = list()
    for col in dfv.schema:
        column_names.append(col.name)

    stats = dict()

    for col in column_names:
        print(col)
        datas = dfv.read([col])
        stats[col] = {
            'nombre_na' : datas.column(col).null_count,
            'dtype' : str(datas.column(col).type)
        }
        if datas.column(col).type in ("double", "integer"):
            stats[col]['somme'] = pc.sum(datas.column(col)).as_py()
        pq.write_table(datas,f"{columns_path}/pote_{col}.parquet")

    with open(os.path.join(columns_path,"columns_stats_desc.json"), "w") as outfile:
        json.dump(stats, outfile)

    stats_corr = pd.DataFrame(stats)
    stats_corr.transpose().to_excel(os.path.join(columns_path,"columns_stats_desc.xlsx"))

import shutil
from pathlib import Path

import pandas as pd
from tqdm import tqdm
import json
import gc
import glob
import os
import pyarrow.parquet as pq
import pyarrow.compute as pc

year = "2022"
SAS_FILE = (
    r"\\casd.fr\casdfs\Projets\LEXIMPA\Data\POTE_POTE_"
    + year
    + "\pote_diff_"
    + year
    + ".sas7bdat"
)
CHUNKS_OUT_PATH = (r"C:\Users\Public\Documents\donnees_brutes\POTE/chunks/" + year)
ARROW_OUT_PATH = (r"C:\Users\Public\Documents\donnees_brutes\POTE/parquet_columns/" + year)
taille_chunk = 100_000

dfi = pd.read_sas(
    SAS_FILE, chunksize=taille_chunk, encoding="iso8859-15", iterator=True
)

dd_values = None
i = 0

# 1) on fait des chunks au format parquet de la table complète en SAS.
for chunk in tqdm(dfi):
    columns = [c.lower() for c in chunk.columns.to_list()]
    chunk.columns = [c.lower() for c in chunk.columns.to_list()]
    chunk.drop(["fip18_c"], axis=1, inplace=True)
    chunk.to_parquet(f"{CHUNKS_OUT_PATH}/pote_{i}.parquet")
    del chunk
    gc.collect()

# 2) On lit tous les chunks pour faire une table parquet par colonne
parquet_file = glob.glob(os.path.join(CHUNKS_OUT_PATH, "*.parquet"))

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
    pq.write_table(datas,f"{ARROW_OUT_PATH}/pote_{col}.parquet")

with open(f"{ARROW_OUT_PATH}/columns_stats_desc.json", "w") as outfile:
    json.dump(stats_corr, outfile)

stats_corr = pd.DataFrame(stats_corr)
stats_corr.transpose().to_excel(f"{ARROW_OUT_PATH}/columns_stats_desc.xlsx")

"""
Ce script transforme la base de données POTE qui est au format SAS en format parquet, plus facile à manier
"""

import click
import gc
import json
import os
import pyreadstat

from openfisca_france_data.utils import build_cerfa_fields_by_variable

def pote_sas_to_parquet(year, sas_pote_directory, parquet_directory, create_labels = False, ncols = 70, additional_variables = []):
    """
    Docstring for pote_sas_to_parquet
    
    :param year: Millésime de Pote
    :param sas_pote_path: Chemin de la base pote en SAS
    :param parquet_path: Chemin où enregistrer la base pote en parquet créée
    :param create_labels: bool, Si True recrée la liste des variables dans la base SAS
    :param ncols: Nombre max de colonnes à charger en même temps
    """
    labels_path = os.path.join(parquet_directory, "metadata")
    sas_file = f"{os.path.join(sas_pote_directory,year)},pote_diff_{year}.sas7bdat"
    if create_labels:
        if not os.path.exists(labels_path):
            os.makedirs(labels_path)
        metadata = pyreadstat.read.sas7bdat(filename_path = sas_file)
        col_labels = metadata[1].column_names_to_labels
        with open(os.path.join(labels_path, "labels.json"), "w", newline='',encoding='utf-8') as f:
            json.dump(col_labels, f, ensure_ascii=False, indent=4)
    else:
        with open(os.path.join(labels_path, "labels.json"),"r",encoding='utf-8') as f:
            col_labels=json.load(f)
    
    cerfa = build_cerfa_fields_by_variable(year = year)
    openfisca_cerfa_list = set()
    for k,v in cerfa.items():
        openfisca_cerfa_list = (openfisca_cerfa_list | set([vv[1:] for vv in v]))

    # on ajoute les cases qui ne sont pas renseignées cerfa dans openfisca-france
    list_col += ["aged", "agec", "mat", "f", "h", "r", "j", "n", "g", "i", "nbfoy", "dnpa4c", "r", "zl", "zn", "zp", "zf", "zw", "zs", "zg", "zt", "zz", "iddep"]
    list_col += additional_variables
    for var in list_col:
        assert col_labels.get(var, None) is not None, f"{var} not in col_labels"
    
    del cerfa
    del openfisca_cerfa_list
    del col_labels

    for i in range(1,len(list_col)//ncols + 1):
        print(f"Round {i} / {len(list_col)//ncols + 1}")
        table, metadata = pyreadstat.read_sas7bdat(filename_path = sas_file, usecols=list_col[i*ncols:(i+1)*ncols])
        table.to_parquet(os.path.join(parquet_directory,f"pote_2023_{i}.parquet"))
        with open(os.path.join(labels_path, f"labels_pote_{i}.json"),"w",newline='',encoding='utf-8') as f:
            json.dump(metadata.column_names_to_labels, f, ensure_ascii=False,indent=4)
        del table
        del metadata
        gc.collect()


@click.command()
@click.option(
    "-y",
    "--year",
    default=2023,
    show_default=True,
    type=int,
)
@click.option(
    "-sas",
    "--sas_pote_directory",
    show_default=True,
    type=str,
)
@click.option(
    "-parquet",
    "--parquet_directory",
    type=str,
)
@click.option(
    "-labels",
    "--create_labels",
    default=False,
    show_default=True,
    type=bool,
)
@click.option(
    "-ncols",
    "--ncols",
    default=70,
    show_default=True,
    type=int,
)
@click.option(
    "-vars",
    "--additional_variables",
    default=[],
    show_default=True,
    type=list,
)
def main(year, sas_pote_directory, parquet_directory, create_labels = False, ncols = 70, additional_variables = []):
    pote_sas_to_parquet(year, sas_pote_directory, parquet_directory, create_labels, ncols, additional_variables)

if __name__ == "__main__":
    main()
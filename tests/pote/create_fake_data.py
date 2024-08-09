from openfisca_france_data.utils import build_cerfa_fields_by_variable
import random
import numpy as np
import pandas as pd
import os
import click
import glob
import json
import pyarrow.parquet as pq
import pyarrow.compute as pc

cwd = os.getcwd()

default_output_path = os.path.join(os.path.join(cwd,"fake_data"),"raw")

def create_fake_data(year = 2022, data_length = 100, output_path = default_output_path):
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    # on recupere toutes les cases fiscales de l'annee de simulation
    cases_openfisca = build_cerfa_fields_by_variable(year = year)
    cases_fiscales = list()
    for values in cases_openfisca.values():
        cases_fiscales += values

    # on les trie en fonction de leur nom pour tirer des cases dans chaques catégories pour éviter d'avoir trop de colonnes
    grouped_cases = dict()
    for i in range(10):
        grouped_cases[f"f{i}"] = [c for c in cases_fiscales if c.startswith(f"f{i}")]
    grouped_cases["others"] = [c for c in cases_fiscales if not c[1] in [str(r) for r in range(10)]]

    for cases in grouped_cases.values():
        # if len(cases) > 30:
        #     cases = cases[0:30]
        for case in cases:
            array = pd.DataFrame({ case: np.random.uniform(10000,50000,data_length) * (np.random.random(data_length) < random.random())})
            # on créé un array avec un nombre aléatoire de valeurs non nulles suivant une loi uniforme en 10000 et 50000
            array.to_parquet(f"{output_path}/pote_z{case[1:]}.parquet")

    nb_celib_sans_enfants = round(data_length / 3)
    nb_celib_enfants = round(data_length / 6)
    nb_couple_sans_enfants = round(data_length / 6)
    nb_couple_enfants = data_length - (nb_celib_sans_enfants + nb_celib_enfants + nb_couple_sans_enfants)

    case_enfants = ['F', 'G', 'H', 'I']
    # Enfant à charge
    ## F = enfant non mariés de moins de 18 ans ou handicapé quelque soit l'âge
    ### G = dont enfant titulaire de la carte d'invalidité
    # Enfant à charge en garde alternée
    ## H = enfant non mariés de moins de 18 ans ou handicapé quelque soit l'âge
    ### I = dont enfant titulaire de la carte d'invalidité

    # R = Autre personne invalide vivant sous votre toit
    # J = rattachement d'un enfant majeur célibataire sans enfant
    # N = nombre d'enfants mariés / pacsés et non mariés chargé de famille

    # creation des foyers de célibataire
    ## sans enfants
    df_celib_sans_enfants = pd.DataFrame({'mat': np.full(nb_celib_sans_enfants, "C"),
                                                         'aged': np.random.randint(high = year - 18, low = year - 90, size=nb_celib_sans_enfants),
                                                         'nbfoy': np.full(nb_celib_sans_enfants, 1)})
    ## avec enfants
    df_celib_enfants = pd.DataFrame({'mat': np.full(nb_celib_enfants, "C"),
                                     'aged': np.random.randint(high = year - 18, low = year - 90, size=nb_celib_enfants),
                                     'dnpa4c': [random.choice(case_enfants) + str(random.randint(a=year-17, b=year-1)) for i in range(nb_celib_enfants)],
                                     'nbfoy': np.full(nb_celib_enfants, 2)})
    for c in case_enfants:
        df_celib_enfants[c.lower()] = [ 1 if col[0] == c else 0 for col in df_celib_enfants.dnpa4c]
    # creation des foyers maries/pacses
    ## sans enfants
    df_couple_sans_enfants = pd.DataFrame({'mat': np.full(nb_couple_sans_enfants, "M"),
                                           'aged': np.random.randint(high = year - 18, low = year - 90, size=nb_couple_sans_enfants),
                                           'agec': np.random.randint(high = year - 18, low = year - 90, size=nb_couple_sans_enfants),
                                           'nbfoy': np.full(nb_couple_sans_enfants, 2)})

    ## avec enfants
    df_couple_enfants = pd.DataFrame({'mat': np.full(nb_couple_enfants, "M"),
                                      'aged': np.random.randint(high = year - 18, low = year - 90, size=nb_couple_enfants),
                                      'agec': np.random.randint(high = year - 18, low = year - 90, size=nb_couple_enfants),
                                      'dnpa4c': [random.choice(case_enfants) + str(random.randint(a=year-17, b=year-1)) + random.choice(case_enfants) + str(random.randint(a=year-17, b=year-1)) for i in range(nb_couple_enfants)],
                                      'nbfoy': np.full(nb_couple_enfants, 4)})

    for c in case_enfants:
        df_couple_enfants[c.lower()] = [int(col[0] == c) + int(col[5] == c) for col in df_couple_enfants.dnpa4c]

    df = pd.concat([df_celib_sans_enfants,df_celib_enfants], axis = 0)
    df = pd.concat([df,df_couple_sans_enfants], axis = 0)
    df = pd.concat([df,df_couple_enfants], axis = 0)

    df['r'] = 0
    df['j'] = 0
    df['n'] = 0

    for c in df.columns:
        df[[c]].to_parquet(f"{output_path}/pote_{c}.parquet")

    # Création d'une table de stats de nombre de valeurs non nulles
    parquet_file = glob.glob(os.path.join(output_path, "*.parquet"))
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

    with open(f"{output_path}/columns_stats_desc.json", "w") as outfile:
        json.dump(stats, outfile)

@click.command()
@click.option('-y', '--year', 'year', default = 2022, help = "POTE year", show_default = True,
    type = int)
@click.option('-l', '--length', 'data_length', default = 100, help = "data length", show_default = True,
    type = int)
@click.option('-p', '--path', 'output_path', default=default_output_path, help = "output data path", show_default = True)
def main(year = 2022, data_length = 100, output_path=default_output_path):
    create_fake_data(year, data_length, output_path)

if __name__ == '__main__':
    main()

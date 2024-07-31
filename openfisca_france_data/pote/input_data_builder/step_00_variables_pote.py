from openfisca_france_data.utils import build_cerfa_fields_by_variable
import pandas as pd
import logging

def create_pote_openfisca_variables_list(year, errors_path, pote_colonne_file_path):
    logging.warning("Récupération des colonnes en commun entre Pote et Openfisca")
    dict_variables_cerfa_field = build_cerfa_fields_by_variable(year = year)

    variables_cerfa_field = list()
    for var_list in list(dict_variables_cerfa_field.values()):
        variables_cerfa_field += var_list
    pd.DataFrame({'liste_var': variables_cerfa_field}).to_csv(f"{errors_path}cerfa_openfisca.csv")
    doublons = dict([(n,variables_cerfa_field.count(n)) for n in set(variables_cerfa_field)])
    doublons = list({k:v for (k,v) in doublons.items() if v>1}.keys())
    assert len(doublons) == 0, f"Il y a des doublons dans les cases cerfa d'openfisca france : {doublons}"

    del doublons 

    colonnes_pote_2021 = pd.read_csv(pote_colonne_file_path,sep =",",encoding = "latin_1")
    colonnes_pote_2021 = ["f" + str.lower(c[1:]) for c in colonnes_pote_2021.NAME if str.lower(c).startswith('z')]

    var_to_keep = list(set(colonnes_pote_2021) & set(variables_cerfa_field))
    logging.warning(f"Parmi les {len(colonnes_pote_2021)} variables de pote, {len(var_to_keep)} ont été trouvées dans openfisca")
    var_not_in_openfisca = [c for c in colonnes_pote_2021 if c not in variables_cerfa_field]
    pd.DataFrame({'liste_var': var_not_in_openfisca}).to_csv(f"{errors_path}cerfa_manquants_openfisca.csv")

    variables_foyer_fiscal = dict()
    variables_individu = dict()
    for openfisca_var, cerfa in dict_variables_cerfa_field.items():
        if len(cerfa) == 1:
            variables_foyer_fiscal[openfisca_var] = cerfa[0]
        else:
            variables_individu[openfisca_var] = cerfa
    return variables_individu, variables_foyer_fiscal
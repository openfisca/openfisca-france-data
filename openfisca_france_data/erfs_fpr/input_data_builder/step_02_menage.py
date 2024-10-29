"""Constructin des variables ménages."""


import logging
import pandas as pd

from openfisca_survey_manager.temporary import temporary_store_decorator


log = logging.getLogger(__name__)


@temporary_store_decorator(file_name = 'erfs_fpr')
def build_variables_menage(temporary_store = None, year = None):
    menages = temporary_store[f'menages_{year}']

    if "loyer" in menages.columns:
        menages['loyer'] = menages['loyer'] * 12
    else:
        menages['loyer'] = 500 # attention solution temporaire pour test, car pas de loyer à partir de 2021

    if year == 2018:
        menages['statut_occupation_logement'] = menages['so'].copy()

    if year >= 2019:  # SO ne fonctionne pas en 2019 bcp de 0 = non-renseigné, logT présent en 2021
        menages['statut_occupation_logement'] = menages['logt'].copy()
        menages.loc[(menages.statut_occupation_logement == 9), 'statut_occupation_logement'] = 4 # il y a une valeur manquante on la met locataure 

    if year >= 2018 and year < 2021:
        menages['zone_apl'] = 3
        menages.loc[menages['tau2010'] == 10,'zone_apl'] = 1 #Commune appartenant à l'aire urbaine de Paris
        menages.loc[menages['tau2010'] == 9,'zone_apl'] = 2 #Commune appartenant à une aire urbaine de 500 000 à 9 999 999 habitants
        #menages.loc[menages['tau2010'] == 8,'zone_apl'] = 2
        # pour l'instant on met tout le monde à 2 mais à améliorer, peut être en fonction de la taille de l'aire urbaine ?
        menages.loc[(menages.statut_occupation_logement == 7), 'statut_occupation_logement'] = 2
        menages['logement_conventionne'] = False
        menages.loc[menages['statut_occupation_logement'] == 3 ,'logement_conventionne'] = True
        temporary_store['menages_{}'.format(year)] = menages
    
    # tau2010 est remplacé par tuu2020 en 2021 (attention pas les mêmes modalités)
    if year >= 2021:
        menages['zone_apl'] = 3
        menages.loc[menages['tuu2020'] == 8,'zone_apl'] = 1 #Commune appartenant à l'aire urbaine de Paris
        menages.loc[menages['tuu2020'] == 7,'zone_apl'] = 2 #Commune appartenant à une aire urbaine de 200 000 à 9 999 999 habitants (attention pas de tranche commençant à 500 000)
        menages.loc[(menages.statut_occupation_logement == 7), 'statut_occupation_logement'] = 2
        menages['logement_conventionne'] = False
        menages.loc[menages['statut_occupation_logement'] == 3 ,'logement_conventionne'] = True
        temporary_store['menages_{}'.format(year)] = menages


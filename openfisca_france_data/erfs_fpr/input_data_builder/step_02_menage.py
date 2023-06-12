"""Constructin des variables ménages."""


import logging
import pandas as pd

from openfisca_survey_manager.temporary import temporary_store_decorator


log = logging.getLogger(__name__)


@temporary_store_decorator(file_name = 'erfs_fpr')
def build_variables_menage(temporary_store = None, year = None):
    if year == 2018:
        menages = temporary_store[f'menages_{year}']
        menages['statut_occupation_logement'] = menages['so'].copy()

    if year == 2019:  # SO ne fonctionne pas en 2019 bcp de 0 = non-renseigné
        menages = temporary_store[f'menages_{year}']
        menages['statut_occupation_logement'] = menages['logt'].copy()

    if year >= 2018:
        menages['zone_apl'] = 2
        # pour l'instant on met tout le monde à 2 mais à améliorer, peut être en fonction de la taille de l'aire urbaine ?
        menages.loc[(menages.statut_occupation_logement == 7), 'statut_occupation_logement'] = 2
        temporary_store['menages_{}'.format(year)] = menages

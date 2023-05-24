import logging
import pandas as pd


from openfisca_survey_manager.temporary import temporary_store_decorator  # type: ignore

log = logging.getLogger(__name__)


@temporary_store_decorator(file_name = 'erfs_fpr')
def build_variables_menage(temporary_store = None, year = None):
    if year >= 2018:
        menages = temporary_store['menages_{}'.format(year)]
        menages['zone_apl'] = 2
        # pour l'instant on met tout le monde à 2 mais à améliorer, peut être en fonction de la taille de l'aire urbaine ?
        menages['statut_occupation_logement'] = menages['so'].copy()
        menages.loc[(menages.statut_occupation_logement == 7),'statut_occupation_logement'] = 2
        temporary_store['menages_{}'.format(year)] = menages

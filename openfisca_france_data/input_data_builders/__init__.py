# -*- coding: utf-8 -*-


from openfisca_france_data import default_config_files_directory as config_files_directory
from openfisca_survey_manager.survey_collections import SurveyCollection


def get_input_data_frame(year):
    openfisca_survey_collection = SurveyCollection.load(
        collection = "openfisca", config_files_directory = config_files_directory)
    openfisca_survey = openfisca_survey_collection.get_survey("openfisca_data_{}".format(year))
    input_data_frame = openfisca_survey.get_values(table = "input").reset_index(drop = True)
    input_data_frame.rename(
        columns = dict(
            alr = 'pensions_alimentaires_percues',
            choi = 'chomage_imposable',
            cho_ld = 'chomeur_longue_duree',
            fra = 'frais_reels',
            rsti = 'retraite_imposable',
            sali = 'salaire_imposable',
            ),
        inplace = True,
        )
    return input_data_frame

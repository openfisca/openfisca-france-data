# -*- coding: utf-8 -*-


from openfisca_france_data.surveys import AbstractErfsSurveyScenario
from openfisca_france_data import default_config_files_directory as config_files_directory

from openfisca_survey_manager.survey_collections import SurveyCollection


class ErfsSurveyScenario(AbstractErfsSurveyScenario):
    default_used_as_input_variables = [
        'age_en_mois',
        'age',
        'chomage_imposable',
        'hsup',
        'nbF',
        'nbG',
        'nbH',
        'nbI',
        'nbJ',
        'nbN',
        'nbR',
        'retraite_imposable',
        'salaire_imposable',
        'autonomie_financiere',
        ]

    @classmethod
    def create(cls, year = None, input_data_frame = None):
        assert year is not None
        openfisca_survey_collection = SurveyCollection.load(
            collection = "openfisca", config_files_directory = config_files_directory)
        openfisca_survey = openfisca_survey_collection.get_survey("openfisca_data_{}".format(year))
        if input_data_frame:
            input_data_frame = (input_data_frame
                .reset_index(drop = True)
                .rename(
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
                )
        else:
            input_data_frame = (openfisca_survey.get_values(table = "input")
                .reset_index(drop = True)
                .rename(
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
                )
        return cls().init_from_data_frame(
            input_data_frame = input_data_frame,
            year = year,
            )

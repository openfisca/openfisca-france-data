# -*- coding: utf-8 -*-


from openfisca_france_data.surveys import AbstractErfsSurveyScenario
from openfisca_france_data import default_config_files_directory as config_files_directory

from openfisca_survey_manager.survey_collections import SurveyCollection


class ErfsFprSurveyScenario(AbstractErfsSurveyScenario):
    default_used_as_input_variables = [
        'age_en_mois',
        'age',
        'autonomie_financiere',
        'chomage_imposable',
        'f4ba',
        'retraite_brute',
        'retraite_imposable',
        'salaire_imposable',
        'rag',
        'ric',
        'rnc',
        'taxe_habitation',
        ]

    @classmethod
    def build_input_data(cls, year = None):
        assert year is not None
        from openfisca_france_data.erfs_fpr.input_data_builder import build
        build(year = year)

    @classmethod
    def create(cls, year = None, rebuild_input_data = False):
        assert year is not None
        if rebuild_input_data:
            cls.build_input_data(year = year)
        openfisca_survey_collection = SurveyCollection.load(
            collection = "openfisca", config_files_directory = config_files_directory)
        openfisca_survey = openfisca_survey_collection.get_survey("openfisca_erfs_fpr_data_{}".format(year))
        input_data_frame = openfisca_survey.get_values(table = "input").reset_index(drop = True)
        return cls().init_from_data_frame(
            input_data_frame = input_data_frame,
            year = year,
            )

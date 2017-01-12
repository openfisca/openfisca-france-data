# -*- coding: utf-8 -*-


from openfisca_france_data.surveys import AbstractErfsSurveyScenario


class ErfsFprSurveyScenario(AbstractErfsSurveyScenario):
    default_used_as_input_variables = [
        'age_en_mois',
        'age',
        'autonomie_financiere',
        'chomage_brut',
        'chomage_imposable',
        'cotisation_sociale_mode_recouvrement',
        'f4ba',
        'retraite_brute',
        'retraite_imposable',
        'salaire_imposable_pour_inversion',  # 'salaire_imposable',
        'rag',
        'ric',
        'rnc',
        'taxe_habitation',
        ]
    input_data_survey_prefix = 'openfisca_erfs_fpr_data'
    collection = 'openfisca_erfs_fpr'

    @classmethod
    def build_input_data(cls, year = None):
        assert year is not None
        from openfisca_france_data.erfs_fpr.input_data_builder import build
        build(year = year)

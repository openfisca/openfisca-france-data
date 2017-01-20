# -*- coding: utf-8 -*-


from openfisca_france_data.surveys import AbstractErfsSurveyScenario


class ErfsFprSurveyScenario(AbstractErfsSurveyScenario):
    collection = 'openfisca_erfs_fpr'
    default_used_as_input_variables = [
        'age_en_mois',
        'age',
        'autonomie_financiere',
        'categorie_salarie',
        'chomage_brut',
        'chomage_imposable',
        'contrat_de_travail',
        'cotisation_sociale_mode_recouvrement',
        'effectif_entreprise',
        'f4ba',
        'heures_remunerees_volume',
        'pensions_alimentaires_percues',
        'rag',
        'retraite_brute',
        'retraite_imposable',
        'ric',
        'rnc',
        'salaire_imposable_pour_inversion',  # 'salaire_imposable',
        'taxe_habitation',
        ]
    # Might be used: hsup
    default_value_by_variable = dict(
        cotisation_sociale_mode_recouvrement = 1,
        # taux_incapacite = .50,
        )
    input_data_survey_prefix = 'openfisca_erfs_fpr_data'
    non_neutralizable_variables = [
        'champm',
        'idfam_original',
        'idfoy_original',
        'idmen_original',
        'statut_marital',
        'wprm_init',
        ]

    @classmethod
    def build_input_data(cls, year = None):
        assert year is not None
        from openfisca_france_data.erfs_fpr.input_data_builder import build
        build(year = year)

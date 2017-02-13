# -*- coding: utf-8 -*-


from openfisca_france_data.surveys import AbstractErfsSurveyScenario


class ErfsFprSurveyScenario(AbstractErfsSurveyScenario):
    collection = 'openfisca_erfs_fpr'
    used_as_input_variables = [
        'activite',
        'autonomie_financiere',
        'categorie_salarie',
        'chomage_brut',
        'chomage_imposable',
        'contrat_de_travail',
        'cotisation_sociale_mode_recouvrement',
        'date_naissance',
        'effectif_entreprise',
        'f4ba',
        'heures_remunerees_volume',
        'loyer',
        'pensions_alimentaires_percues',
        'rag',
        'retraite_brute',
        'retraite_imposable',
        'ric',
        'rnc',
        'statut_marital',
        'salaire_de_base',
        'statut_occupation_logement',
        'taxe_habitation',
        'zone_apl',
        ]
    # Might be used: hsup
    default_value_by_variable = dict(
        cotisation_sociale_mode_recouvrement = 2,
        # taux_incapacite = .50,
        )
    input_data_survey_prefix = 'openfisca_erfs_fpr_data'
    non_neutralizable_variables = [
        'champm',
        'idfam_original',
        'idfoy_original',
        'idmen_original',
        # 'rempli_obligation_scolaire',
        # 'ressortissant_eee',
        'wprm_init',
        ]

    @classmethod
    def build_input_data(cls, year = None):
        assert year is not None
        from openfisca_france_data.erfs_fpr.input_data_builder import build
        build(year = year)

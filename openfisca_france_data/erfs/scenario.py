from openfisca_france_data.surveys import AbstractErfsSurveyScenario


class ErfsSurveyScenario(AbstractErfsSurveyScenario):
    used_as_input_variables = [
        'activite',
        'age_en_mois',
        'age',
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
        'hsup',
        'loyer',
        'nbF',
        'nbG',
        'nbH',
        'nbI',
        'nbJ',
        'nbN',
        'nbR',
        'pensions_alimentaires_percues',
        'rag',
        'retraite_brute',
        'retraite_imposable',
        'ric',
        'rnc',
        'salaire_de_base',
        'salaire_imposable',
        'statut_marital',
        'statut_occupation_logement',
        'taxe_habitation',
        'zone_apl',
        ]

    def __init__(self, year: int) -> None:
        self.year = year

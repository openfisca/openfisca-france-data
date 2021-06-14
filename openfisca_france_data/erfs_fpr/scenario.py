from openfisca_france_data.surveys import AbstractErfsSurveyScenario


class ErfsFprSurveyScenario(AbstractErfsSurveyScenario):
    """Survey scenario spécialisé pour l'ERFS-FPR."""

    collection = "openfisca_erfs_fpr"

    # Les variables OpenFisca qu'on va utiliser avec les données en entrée.
    used_as_input_variables = [
        "activite",
        "autonomie_financiere",
        "categorie_salarie",
        "chomage_brut",
        "chomage_imposable",
        "contrat_de_travail",
        "cotisation_sociale_mode_recouvrement",
        "date_naissance",
        "effectif_entreprise",
        "f4ba",
        "heures_remunerees_volume",
        "loyer",
        "pensions_alimentaires_percues",
        "primes_fonction_publique",
        "rag",
        "retraite_brute",
        "retraite_imposable",
        "ric",
        "rnc",
        "statut_marital",
        "salaire_de_base",
        "statut_occupation_logement",
        "taxe_habitation",
        "traitement_indiciaire_brut",
        "zone_apl",
        ]

    # Might be used: hsup
    # Pour forcer quelques valeurs par défaut spécifiques.
    default_value_by_variable = dict(
        cotisation_sociale_mode_recouvrement = 2,
        # taux_incapacite = .50,
        )

    # En général, si les données contiennent les variables dont on a besoin, on les garde.
    #
    # Le cas échéant, on les neutralise à leur valeur par défaut, pour ne pas garder des
    # vecteurs des variables qu'on ne veut pas calculer.
    #
    # Ici c'est une exception : on déclare les variables qu'on ne veut pas neutraliser.
    non_neutralizable_variables = [
        "menage_ordinaire",
        "idfam_original",
        "idfoy_original",
        "idmen_original",
        # 'rempli_obligation_scolaire',
        # 'ressortissant_eee',
        "wprm_init",
        ]

    def __init__(self, year: int) -> None:
        self.year = year

    @classmethod
    def build_input_data(cls, year: int) -> None:
        # TODO: fix import, otherwise it is untestable.
        from openfisca_france_data.erfs_fpr.input_data_builder import build

        build(year = year)

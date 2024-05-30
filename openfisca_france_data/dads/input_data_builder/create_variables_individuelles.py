from openfisca_france_data.felin.input_data_builder.create_variables_individuelles import create_taux_csg_remplacement
from openfisca_france_data.common import (
    create_salaire_de_base,
    create_traitement_indiciaire_brut,
    create_revenus_remplacement_bruts,
    )


def create_individu_variables_brutes(
    individus,
    revenu_type = None,
    period = None,
    tax_benefit_system = None,
    ):
    """
    Crée les variables brutes de revenus:
      - salaire_de_base
      - traitement_indiciaire_brut
      - primes_fonction_publique
      - retraite_bruite
      - chomage_brut
    à partir des valeurs nettes ou imposables de ces revenus
    et d'autres information individuelles
    """
    assert revenu_type in ['imposable', 'net']
    assert period is not None
    assert tax_benefit_system is not None

    assert 'age' in individus.columns
    assert 'contrat_de_travail' in individus.columns
    assert 'heures_remunerees_volume' in individus.columns
    assert 'categorie_salarie' in individus.columns
    assert 'categorie_non_salarie' in individus.columns
    assert 'effectif_entreprise' in individus.columns

    # Temp

    created_variables = []

    create_salaire_de_base(individus, period = period, revenu_type = revenu_type, tax_benefit_system = tax_benefit_system)
    created_variables.append('salaire_de_base')

    create_traitement_indiciaire_brut(individus, period = period, revenu_type = revenu_type, tax_benefit_system = tax_benefit_system)
    created_variables.append('traitement_indiciaire_brut')
    created_variables.append('primes_fonction_publique')

    create_taux_csg_remplacement(individus, period, tax_benefit_system)
    created_variables.append('taux_csg_remplacement')

    create_revenus_remplacement_bruts(individus, period, tax_benefit_system, revenu_type = revenu_type)
    created_variables.append('chomage_brut')
    created_variables.append('retraite_brute')

    return created_variables

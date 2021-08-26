from openfisca_france_data.model.base import * # noqa  analysis:ignore


class menage_ordinaire(Variable):
    value_type = int
    is_period_size_independent = True
    default_value = True
    entity = Menage
    definition_period = YEAR

class menage_ordinaire_individus(Variable):
    value_type = int
    is_period_size_independent = True
    entity = Individu
    label = "L'individu est dans un ménage du champ ménage"
    definition_period = YEAR

    def formula(individu, period):
        return individu.menage('menage_ordinaire', period)


class menage_ordinaire_familles(Variable):
    value_type = int
    is_period_size_independent = True
    entity = Famille
    label = "Le premier parent de la famille est dans un ménage du champ ménage"
    definition_period = YEAR

    def formula(famille, period):
        return famille.demandeur('menage_ordinaire_individus', period)


class menage_ordinaire_foyers_fiscaux(Variable):
    value_type = int
    is_period_size_independent = True
    entity = FoyerFiscal
    label = "Le premier déclarant du foyer est dans un ménage du champ ménage"
    definition_period = YEAR

    def formula(foyer_fiscal, period):
        return foyer_fiscal.declarant_principal('menage_ordinaire_individus', period)


class weight_familles(Variable):
    is_period_size_independent = True
    value_type = float
    entity = Famille
    label = "Poids de la famille"
    definition_period = YEAR

    def formula(famille, period):
        return famille.demandeur('weight_individus', period)


class weight_foyers(Variable):
    is_period_size_independent = True
    value_type = float
    entity = FoyerFiscal
    label = "Poids du foyer fiscal"
    definition_period = YEAR

    def formula(foyer_fiscal, period):
        return foyer_fiscal.declarant_principal('weight_individus', period)


class weight_menages(Variable):
    is_period_size_independent = True
    value_type = float
    entity = Menage
    label = "Poids du ménage"
    definition_period = YEAR

    def formula(menage, period):
        return menage.personne_de_reference('weight_individus', period)



class wprm(Variable):
    default_value = 1.0
    is_period_size_independent = True
    value_type = float
    entity = Menage
    label = "Effectifs"
    definition_period = YEAR


class wprm_init(Variable):
    is_period_size_independent = True
    value_type = float
    entity = Menage
    label = "Effectifs"
    definition_period = YEAR


class weight_individus(Variable):
    is_period_size_independent = True
    value_type = float
    entity = Individu
    label = "Poids de l'individu"
    definition_period = YEAR

    def formula(individu, period):
        return individu.menage('wprm', period)

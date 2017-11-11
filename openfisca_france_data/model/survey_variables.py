# -*- coding: utf-8 -*-


from .base import * # noqa  analysis:ignore


class idmen_original(Variable):
    value_type = int
    is_period_size_independent = True
    entity = Menage
    label = u"Identifiant ménage, lien avec l'identifiant dérivé de l'ERF"
    definition_period = YEAR


class idfoy_original(Variable):
    value_type = int
    is_period_size_independent = True
    entity = FoyerFiscal
    label = u"Identifiant foyer, lien avec l'identifiant dérivé de l'ERF"
    definition_period = YEAR


class idfam_original(Variable):
    value_type = int
    is_period_size_independent = True
    entity = Famille
    label = u"Identifiant famille, lien avec l'identifiant dérivé de l'ERF"
    definition_period = YEAR


class menage_ordinaire(Variable):
    value_type = int
    is_period_size_independent = True
    entity = Menage
    definition_period = YEAR

class menage_ordinaire_individus(Variable):
    value_type = int
    is_period_size_independent = True
    entity = Individu
    label = u"L'individu est dans un ménage du champ ménage"
    definition_period = YEAR

    def formula(individu, period):
        return individu.menage('menage_ordinaire', period)


class menage_ordinaire_familles(Variable):
    value_type = int
    is_period_size_independent = True
    entity = Famille
    label = u"Le premier parent de la famille est dans un ménage du champ ménage"
    definition_period = YEAR

    def formula(famille, period):
        return famille.demandeur('menage_ordinaire_individus', period)


class menage_ordinaire_foyers_fiscaux(Variable):
    value_type = int
    is_period_size_independent = True
    entity = FoyerFiscal
    label = u"Le premier déclarant du foyer est dans un ménage du champ ménage"
    definition_period = YEAR

    def formula(foyer_fiscal, period):
        return foyer_fiscal.declarant_principal('menage_ordinaire_individus', period)


class weight_familles(Variable):
    is_period_size_independent = True
    value_type = float
    entity = Famille
    label = u"Poids de la famille"
    definition_period = YEAR

    def formula(famille, period):
        return famille.demandeur('weight_individus', period)


class weight_foyers(Variable):
    is_period_size_independent = True
    value_type = float
    entity = FoyerFiscal
    label = u"Poids du foyer fiscal"
    definition_period = YEAR

    def formula(foyer_fiscal, period):
        return foyer_fiscal.declarant_principal('weight_individus', period)


class wprm(Variable):
    column = PeriodSizeIndependentFloatCol(default = 1)
    entity = Menage
    label = u"Effectifs"
    definition_period = YEAR


class wprm_init(Variable):
    is_period_size_independent = True
    value_type = float
    entity = Menage
    label = u"Effectifs"
    definition_period = YEAR


class weight_individus(Variable):
    is_period_size_independent = True
    value_type = float
    entity = Individu
    label = u"Poids de l'individu"
    definition_period = YEAR

    def formula(individu, period):
        return individu.menage('wprm', period)


# -*- coding: utf-8 -*-


from .base import * # noqa  analysis:ignore


class idmen_original(Variable):
    column = PeriodSizeIndependentIntCol
    entity = Menage
    label = u"Identifiant ménage, lien avec l'identifiant dérivé de l'ERF"
    definition_period = YEAR


class idfoy_original(Variable):
    column = PeriodSizeIndependentIntCol
    entity = FoyerFiscal
    label = u"Identifiant foyer, lien avec l'identifiant dérivé de l'ERF"
    definition_period = YEAR


class idfam_original(Variable):
    column = PeriodSizeIndependentIntCol
    entity = Famille
    label = u"Identifiant famille, lien avec l'identifiant dérivé de l'ERF"
    definition_period = YEAR


class menage_ordinaire(Variable):
    column = PeriodSizeIndependentIntCol(default = True)
    entity = Menage
    definition_period = YEAR

class menage_ordinaire_individus(Variable):
    column = PeriodSizeIndependentIntCol
    entity = Individu
    label = u"L'individu est dans un ménage du champ ménage"
    definition_period = YEAR

    def formula(individu, period):
        return individu.menage('menage_ordinaire', period)


class menage_ordinaire_familles(Variable):
    column = PeriodSizeIndependentIntCol
    entity = Famille
    label = u"Le premier parent de la famille est dans un ménage du champ ménage"
    definition_period = YEAR

    def formula(famille, period):
        return famille.demandeur('menage_ordinaire_individus', period)


class menage_ordinaire_foyers_fiscaux(Variable):
    column = PeriodSizeIndependentIntCol
    entity = FoyerFiscal
    label = u"Le premier déclarant du foyer est dans un ménage du champ ménage"
    definition_period = YEAR

    def formula(foyer_fiscal, period):
        return foyer_fiscal.declarant_principal('menage_ordinaire_individus', period)


class weight_familles(Variable):
    column = PeriodSizeIndependentFloatCol
    entity = Famille
    label = u"Poids de la famille"
    definition_period = YEAR

    def formula(famille, period):
        return famille.demandeur('weight_individus', period)


class weight_foyers(Variable):
    column = PeriodSizeIndependentFloatCol
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
    column = PeriodSizeIndependentFloatCol
    entity = Menage
    label = u"Effectifs"
    definition_period = YEAR


class weight_individus(Variable):
    column = PeriodSizeIndependentFloatCol
    entity = Individu
    label = u"Poids de l'individu"
    definition_period = YEAR

    def formula(individu, period):
        return individu.menage('wprm', period)


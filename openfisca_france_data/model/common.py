# -*- coding: utf-8 -*-


from __future__ import division

from numpy import arange


try:
    from openfisca_survey_manager.statshelpers import weighted_quantiles
except ImportError:
    weighted_quantiles = None

try:
    from openfisca_survey_manager.statshelpers import mark_weighted_percentiles
except ImportError:
    mark_weighted_percentiles = None

from .base import *  # noqa analysis:ignore


class champm_individus(Variable):
    column = BoolCol
    entity = Individu
    label = u"L'individu est dans un ménage du champ ménage",

    def function(individu, period):
        return period, individu.menage('champm')


class champm_familles(Variable):
    column = BoolCol
    entity = Famille
    label = u"Le premier parent de la famille est dans un ménage du champ ménage",

    def function(famille, period):
        return period, famille.demandeur('champm_individus')


class champm_foyers_fiscaux(Variable):
    column = BoolCol
    entity = FoyerFiscal
    label = u"Le premier déclarant du foyer est dans un ménage du champ ménage"

    def function(foyer_fiscal, period):
        return period, foyer_fiscal.declarant_principal('champm_individus')


class decile(Variable):
    column = EnumCol(
        enum = Enum([
            u"Hors champ"
            u"1er décile",
            u"2nd décile",
            u"3e décile",
            u"4e décile",
            u"5e décile",
            u"6e décile",
            u"7e décile",
            u"8e décile",
            u"9e décile",
            u"10e décile"
            ])
        )
    entity = Menage
    label = u"Décile de niveau de vie disponible"

    def function(menage, period):
        champm = menage('champm', period)
        nivvie = menage('nivvie', period)
        wprm = menage('wprm', period)
        labels = arange(1, 11)
        method = 2
        if len(wprm) == 1:
            return period, wprm * 0
        decile, values = mark_weighted_percentiles(nivvie, labels, wprm * champm, method, return_quantiles = True)
        del values
        return period, decile * champm


class decile_net(Variable):
    column = EnumCol(
        enum = Enum([
            u"Hors champ"
            u"1er décile",
            u"2nd décile",
            u"3e décile",
            u"4e décile",
            u"5e décile",
            u"6e décile",
            u"7e décile",
            u"8e décile",
            u"9e décile",
            u"10e décile",
            ])
        )
    entity = Menage
    label = u"Décile de niveau de vie net"

    def function(menage, period):
        champm = menage('champm', period)
        nivvie_net = menage('nivvie_net', period)
        wprm = menage('wprm', period)
        labels = arange(1, 11)
        method = 2
        if len(wprm) == 1:
            return period, wprm * 0
        decile, values = mark_weighted_percentiles(nivvie_net, labels, wprm * champm, method, return_quantiles = True)
        return period, decile * champm


class pauvre40(Variable):
    column = EnumCol(
        enum = Enum([
            u"Ménage au dessus du seuil de pauvreté à 40%",
            u"Ménage en dessous du seuil de pauvreté à 40%",
            ])
        )
    entity = Menage
    label = u"Pauvreté monétaire au seuil de 40%"

    def function(menage, period):
        champm = menage('champm', period)
        nivvie = menage('nivvie', period)
        wprm = menage('wprm', period)
        labels = arange(1, 3)
        method = 2
        if len(wprm) == 1:
            return period, wprm * 0
        percentile, values = mark_weighted_percentiles(nivvie, labels, wprm * champm, method, return_quantiles = True)
        threshold = .4 * values[1]
        return period, (nivvie <= threshold) * champm


class pauvre50(Variable):
    column = EnumCol(
        enum = Enum([
            u"Ménage au dessus du seuil de pauvreté à 50%",
            u"Ménage en dessous du seuil de pauvreté à 50%",
            ])
        )
    entity = Menage
    label = u"Pauvreté monétaire au seuil de 50%"

    def function(menage, period):
        champm = menage('champm', period)
        nivvie = menage('nivvie', period)
        wprm = menage('wprm', period)
        labels = arange(1, 3)
        method = 2
        if len(wprm) == 1:
            return period, wprm * 0

        percentile, values = mark_weighted_percentiles(nivvie, labels, wprm * champm, method, return_quantiles = True)
        threshold = .5 * values[1]
        return period, (nivvie <= threshold) * champm


class pauvre60(Variable):
    column = EnumCol(
        enum = Enum([
            u"Ménage au dessus du seuil de pauvreté à 60%",
            u"Ménage en dessous du seuil de pauvreté à 60%",
            ])
        )
    entity = Menage
    label = u"Pauvreté monétaire au seuil de 60%"

    def function(menage, period):
        champm = menage('champm', period)
        nivvie = menage('nivvie', period)
        wprm = menage('wprm', period)
        labels = arange(1, 3)
        method = 2
        if len(wprm) == 1:
            return period, wprm * 0

        percentile, values = mark_weighted_percentiles(nivvie, labels, wprm * champm, method, return_quantiles = True)
        threshold = .6 * values[1]
        return period, (nivvie <= threshold) * champm


class decile_rfr(Variable):
    column = EnumCol(
        enum = Enum([
            u"Hors champ",
            u"1er décile",
            u"2nd décile",
            u"3e décile",
            u"4e décile",
            u"5e décile",
            u"6e décile",
            u"7e décile",
            u"8e décile",
            u"9e décile",
            u"10e décile"
            ])
        )
    entity = FoyerFiscal
    label = u"Décile de revenu fiscal de référence"

    def function(foyer_fiscal, period):
        period = period.this_year
        rfr = foyer_fiscal('rfr', period)
        weight_foyers = foyer_fiscal('weight_foyers', period)
        champm_foyers_fiscaux = foyer_fiscal('champm_foyers_fiscaux', period)
        labels = arange(1, 11)
        # Alternative method
        # method = 2
        # decile, values = mark_weighted_percentiles(niveau_de_vie, labels, pondmen, method, return_quantiles = True)
        decile, values = weighted_quantiles(rfr, labels, weight_foyers * champm_foyers_fiscaux, return_quantiles = True)
        return period, decile


class decile_rfr_par_part(Variable):
    column = EnumCol(
        enum = Enum([
            u"Hors champ",
            u"1er décile",
            u"2nd décile",
            u"3e décile",
            u"4e décile",
            u"5e décile",
            u"6e décile",
            u"7e décile",
            u"8e décile",
            u"9e décile",
            u"10e décile"
            ])
        )
    entity = FoyerFiscal
    label = u"Décile de revenu fiscal de référence par part fiscale"

    def function(foyer_fiscal, period):
        period = period.this_year
        rfr = foyer_fiscal('rfr', period)
        nbptr = foyer_fiscal('nbptr', period)
        weight_foyers = foyer_fiscal('weight_foyers', period)
        champm_foyers_fiscaux = foyer_fiscal('champm_foyers_fiscaux', period)
        labels = arange(1, 11)
        # Alternative method
        # method = 2
        # decile, values = mark_weighted_percentiles(niveau_de_vie, labels, pondmen, method, return_quantiles = True)
        decile, values = weighted_quantiles(
            rfr / nbptr, labels, weight_foyers * champm_foyers_fiscaux, return_quantiles = True)
        return period, decile


class weight_individus(Variable):
    column = FloatCol
    entity = Individu
    label = u"Poids de l'individu"

    def function(individu, period):
        return period, individu.menage('wprm', period)


class weight_familles(Variable):
    column = FloatCol
    entity = Famille
    label = u"Poids de la famille"

    def function(famille, period):
        return period, famille.demandeur('weight_individus')


class weight_foyers(Variable):
    column = FloatCol
    entity = FoyerFiscal
    label = u"Poids du foyer fiscal",

    def function(foyer_fiscal, period):
        return period, foyer_fiscal.declarant_principal('weight_individus', period)

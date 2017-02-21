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


class assiette_csg_salaire(Variable):
    column = FloatCol
    entity = Individu
    label = u"Assiette CSG salaires"

    def function(individu, period, legislation):
        period = period.this_month
        assiette_csg_abattue = individu('assiette_csg_abattue', period)
        assiette_csg_non_abattue = individu('assiette_csg_non_abattue', period)
        plafond_securite_sociale = individu('plafond_securite_sociale', period)
        abattement = legislation(period.start).prelevements_sociaux.contributions.csg.activite.deductible.abattement
        assiette = assiette_csg_abattue - abattement.calc(
            assiette_csg_abattue,
            factor = plafond_securite_sociale,
            round_base_decimals = 2,
            ) + assiette_csg_non_abattue
        return period, assiette


class assiette_csg_retraite(Variable):
    column = FloatCol
    entity = Individu
    label = u"Assiette CSG retraite"

    def function(individu, period, legislation):
        period = period.this_month
        retraite_brute = individu('retraite_brute', period)
        taux_csg_remplacement = individu('taux_csg_remplacement', period)
        return period, retraite_brute * (taux_csg_remplacement >= 2)


class assiette_csg_chomage(Variable):
    column = FloatCol
    entity = Individu
    label = u"Assiette CSG chomage"

    def function(individu, period, legislation):
        period = period.this_month
        chomage_brut = individu('chomage_brut', period)
        taux_csg_remplacement = individu('taux_csg_remplacement', period)
        return period, chomage_brut * (taux_csg_remplacement >= 2)


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
        menage_ordinaire = menage('menage_ordinaire', period)
        niveau_de_vie = menage('niveau_de_vie', period)
        wprm = menage('wprm', period)
        labels = arange(1, 11)
        method = 2
        if len(wprm) == 1:
            return period, wprm * 0
        decile, values = mark_weighted_percentiles(
            niveau_de_vie, labels, wprm * menage_ordinaire, method, return_quantiles = True)
        del values
        return period, decile * menage_ordinaire


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
        menage_ordinaire = menage('menage_ordinaire', period)
        niveau_de_vie_net = menage('niveau_de_vie_net', period)
        wprm = menage('wprm', period)
        labels = arange(1, 11)
        method = 2
        if len(wprm) == 1:
            return period, wprm * 0
        decile, values = mark_weighted_percentiles(niveau_de_vie_net, labels, wprm * menage_ordinaire, method, return_quantiles = True)
        return period, decile * menage_ordinaire


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
        menage_ordinaire_foyers_fiscaux = foyer_fiscal('menage_ordinaire_foyers_fiscaux', period)
        labels = arange(1, 11)
        # Alternative method
        # method = 2
        # decile, values = mark_weighted_percentiles(niveau_de_vie, labels, pondmen, method, return_quantiles = True)
        decile, values = weighted_quantiles(rfr, labels, weight_foyers * menage_ordinaire_foyers_fiscaux, return_quantiles = True)
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
        menage_ordinaire_foyers_fiscaux = foyer_fiscal('menage_ordinaire_foyers_fiscaux', period)
        labels = arange(1, 11)
        # Alternative method
        # method = 2
        # decile, values = mark_weighted_percentiles(niveau_de_vie, labels, pondmen, method, return_quantiles = True)
        decile, values = weighted_quantiles(
            rfr / nbptr, labels, weight_foyers * menage_ordinaire_foyers_fiscaux, return_quantiles = True)
        return period, decile


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
        menage_ordinaire = menage('menage_ordinaire', period)
        nivvie = menage('nivvie', period)
        wprm = menage('wprm', period)
        labels = arange(1, 3)
        method = 2
        if len(wprm) == 1:
            return period, wprm * 0
        percentile, values = mark_weighted_percentiles(nivvie, labels, wprm * menage_ordinaire, method, return_quantiles = True)
        threshold = .4 * values[1]
        return period, (nivvie <= threshold) * menage_ordinaire


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
        menage_ordinaire = menage('menage_ordinaire', period)
        nivvie = menage('nivvie', period)
        wprm = menage('wprm', period)
        labels = arange(1, 3)
        method = 2
        if len(wprm) == 1:
            return period, wprm * 0

        percentile, values = mark_weighted_percentiles(nivvie, labels, wprm * menage_ordinaire, method, return_quantiles = True)
        threshold = .5 * values[1]
        return period, (nivvie <= threshold) * menage_ordinaire


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
        menage_ordinaire = menage('menage_ordinaire', period)
        nivvie = menage('nivvie', period)
        wprm = menage('wprm', period)
        labels = arange(1, 3)
        method = 2
        if len(wprm) == 1:
            return period, wprm * 0

        percentile, values = mark_weighted_percentiles(nivvie, labels, wprm * menage_ordinaire, method, return_quantiles = True)
        threshold = .6 * values[1]
        return period, (nivvie <= threshold) * menage_ordinaire


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
    entity_class = Individus
    label = u"L'individu est dans un ménage du champ ménage",

    def function(self, simulation, period):
        champm_holder = simulation.calculate("champm", period)
        return period, self.cast_from_entity_to_roles(champm_holder, entity = 'menage')


class champm_familles(Variable):
    column = BoolCol
    entity_class = Familles
    label = u"Le premier parent de la famille est dans un ménage du champ ménage",

    def function(self, simulation, period):
        champm_individus = simulation.calculate('champm_individus', period)
        return period, self.filter_role(champm_individus, role = CHEF)


class champm_foyers_fiscaux(Variable):
    column = BoolCol
    entity_class = FoyersFiscaux
    label = u"Le premier déclarant du foyer est dans un ménage du champ ménage"

    def function(self, simulation, period):
        champm_individus = simulation.calculate('champm_individus', period)
        return period, self.filter_role(champm_individus, role = VOUS)


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

    entity_class = Menages
    label = u"Décile de niveau de vie disponible"

    def function(self, simulation, period):
        champm = simulation.calculate('champm', period)
        nivvie = simulation.calculate('nivvie', period)
        wprm = simulation.calculate('wprm', period)
        labels = arange(1, 11)
        method = 2
        if len(wprm) == 1:
            return period, wprm * 0
        decile, values = mark_weighted_percentiles(nivvie, labels, wprm * champm, method, return_quantiles = True)
        # print values
        # print len(values)
        # print (nivvie*champm).min()
        # print (nivvie*champm).max()
        # print decile.min()
        # print decile.max()
        # print (nivvie*(decile==1)*champm*wprm).sum()/( ((decile==1)*champm*wprm).sum() )
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
    entity_class = Menages
    label = u"Décile de niveau de vie net"

    def function(self, simulation, period):
        champm = simulation.calculate('champm', period)
        nivvie_net = simulation.calculate('nivvie_net', period)
        wprm = simulation.calculate('wprm', period)
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
    entity_class = Menages
    label = u"Pauvreté monétaire au seuil de 40%"

    def function(self, simulation, period):
        champm = simulation.calculate('champm', period)
        nivvie = simulation.calculate('nivvie', period)
        wprm = simulation.calculate('wprm', period)
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
    entity_class = Menages
    label = u"Pauvreté monétaire au seuil de 50%"

    def function(self, simulation, period):
        champm = simulation.calculate('champm', period)
        nivvie = simulation.calculate('nivvie', period)
        wprm = simulation.calculate('wprm', period)
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
    entity_class = Menages
    label = u"Pauvreté monétaire au seuil de 60%"

    def function(self, simulation, period):
        champm = simulation.calculate('champm', period)
        nivvie = simulation.calculate('nivvie', period)
        wprm = simulation.calculate('wprm', period)
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
    entity_class = FoyersFiscaux
    label = u"Décile de revenu fiscal de référence"

    def function(self, simulation, period):
        rfr = simulation.calculate('rfr', period)
        weight_foyers = simulation.calculate('weight_foyers', period)
        champm_foyers_fiscaux = simulation.calculate('champm_foyers_fiscaux', period)
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
    entity_class = FoyersFiscaux
    label = u"Décile de revenu fiscal de référence par part fiscale"

    def function(self, simulation, period):
        rfr = simulation.calculate('rfr', period)
        nbptr = simulation.calculate('nbptr', period)
        weight_foyers = simulation.calculate('weight_foyers', period)
        champm_foyers_fiscaux = simulation.calculate('champm_foyers_fiscaux', period)
        labels = arange(1, 11)
        # Alternative method
        # method = 2
        # decile, values = mark_weighted_percentiles(niveau_de_vie, labels, pondmen, method, return_quantiles = True)
        decile, values = weighted_quantiles(
            rfr / nbptr, labels, weight_foyers * champm_foyers_fiscaux, return_quantiles = True)
        return period, decile


class weight_individus(Variable):
    column = FloatCol
    entity_class = Individus
    label = u"Poids de l'individu"

    def function(self, simulation, period):
        wprm_holder = simulation.calculate('wprm', period)
        return period, self.cast_from_entity_to_roles(wprm_holder, entity = 'menage')


class weight_familles(Variable):
    column = FloatCol
    entity_class = Familles
    label = u"Poids de la famille"

    def function(self, simulation, period):
        weight_individus_holder = simulation.calculate('weight_individus', period)
        return period, self.filter_role(weight_individus_holder, entity = "famille", role = CHEF)


class weight_foyers(Variable):
    column = FloatCol
    entity_class = FoyersFiscaux
    label = u"Poids du foyer fiscal",

    def function(self, simulation, period):
        weight_individus_holder = simulation.calculate('weight_individus', period)
        return period, self.filter_role(weight_individus_holder, entity = "foyer_fiscal", role = VOUS)

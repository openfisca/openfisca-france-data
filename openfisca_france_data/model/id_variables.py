# -*- coding: utf-8 -*-


from .base import *  # noqa  analysis:ignore


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

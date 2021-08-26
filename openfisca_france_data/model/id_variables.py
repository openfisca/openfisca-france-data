from .base import * # noqa  analysis:ignore


class idmen_original(Variable):
    value_type = int
    is_period_size_independent = True
    entity = Menage
    label = "Identifiant ménage, lien avec l'identifiant dérivé de l'ERF"
    definition_period = YEAR


class idfoy_original(Variable):
    value_type = int
    is_period_size_independent = True
    entity = FoyerFiscal
    label = "Identifiant foyer, lien avec l'identifiant dérivé de l'ERF"
    definition_period = YEAR


class idfam_original(Variable):
    value_type = int
    is_period_size_independent = True
    entity = Famille
    label = "Identifiant famille, lien avec l'identifiant dérivé de l'ERF"
    definition_period = YEAR

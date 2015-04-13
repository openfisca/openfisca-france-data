# -*- coding: utf-8 -*-


# OpenFisca -- A versatile microsimulation software
# By: OpenFisca Team <contact@openfisca.fr>
#
# Copyright (C) 2011, 2012, 2013, 2014, 2015 OpenFisca Team
# https://github.com/openfisca
#
# This file is part of OpenFisca.
#
# OpenFisca is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# OpenFisca is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from __future__ import division

import logging

from ..base import *  # noqa analysis:ignore


log = logging.getLogger(__name__)


@reference_formula
class taille_entreprise(SimpleFormulaColumn):
    reference = openfisca_france_tax_benefit_system.column_by_name['taille_entreprise']

    def function(self, simulation, period):
        # Pour mémoire
        # 0 : "Non pertinent"
        # 1 : "Moins de 10 salariés"
        # 2 : "De 10 à 19 salariés"
        # 3 : "De 20 à 199 salariés"
        # 4 : "Plus de 200 salariés"
        nbsala = simulation.calculate('nbsala', period)
        return period, 0 + 1 * (nbsala >= 1) + 1 * (nbsala >= 4) + 1 * (nbsala >= 5) + 1 * (nbsala >= 7)


@reference_formula
class type_sal(SimpleFormulaColumn):
    reference = openfisca_france_tax_benefit_system.column_by_name['type_sal']

    def function(self, simulation, period):
        cadre = simulation.calculate('cadre', period)
        chpub = simulation.calculate('chpub', period)
        titc = simulation.calculate('titc', period)
        statut = simulation.calculate('statut', period)

        cadre = (statut == 8) * (chpub > 3) * cadre
        # noncadre = (statut ==8)*(chpub>3)*not_(cadre)

        # etat_stag = (chpub==1)*(titc == 1)
        etat_tit = (chpub == 1) * (titc == 2)
        etat_cont = (chpub == 1) * (titc == 3)

        militaire = 0  # TODO:

        # colloc_stag = (chpub==2)*(titc == 1)
        colloc_tit = (chpub == 2) * (titc == 2)
        colloc_cont = (chpub == 2) * (titc == 3)

        # hosp_stag = (chpub==2)*(titc == 1)
        hosp_tit = (chpub == 2) * (titc == 2)
        hosp_cont = (chpub == 2) * (titc == 3)

        contract = (colloc_cont + hosp_cont + etat_cont) > 1

        return period, 0 + 1 * cadre + 2 * etat_tit + 3 * militaire + 4 * colloc_tit + 5 * hosp_tit + 6 * contract


# @reference_formula
# class rstbrut(SimpleFormulaColumn):
#     reference = openfisca_france_tax_benefit_system.column_by_name['rstbrut']
#
#     def function(self, simulation, period):
#         rst = simulation.calculate('rst', period)
#         return period, rst
#
#
# @reference_formula
# class salaire_de_base(SimpleFormulaColumn):
#     reference = openfisca_france_tax_benefit_system.column_by_name['salaire_de_base']
#
#     def function(self, simulation, period):
#         sal = simulation.calculate('sal', period)
#         return period, sal

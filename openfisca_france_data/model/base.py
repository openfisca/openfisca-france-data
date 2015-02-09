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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


from openfisca_core.columns import BoolCol, EnumCol, FloatCol, IntCol
from openfisca_core.enumerations import Enum
from openfisca_core.formulas import SimpleFormulaColumn
from openfisca_france_data import reference_tax_benefit_system, SurveyTaxBenefitSystem
from openfisca_france.entities import Familles, FoyersFiscaux, Individus, Menages


__all__ = [
    'BoolCol',
    'CHEF',
    'ENFS',
    'Enum',
    'EnumCol',
    'Familles',
    'FloatCol',
    'FoyersFiscaux',
    'Individus',
    'IntCol',
    'Menages',
    'PART',
    'QUIFAM',
    'QUIFOY',
    'reference_tax_benefit_system',
    'SimpleFormulaColumn',
    'SurveyTaxBenefitSystem',
    'VOUS',
    ]


QUIFAM = Enum(['chef', 'part', 'enf1', 'enf2', 'enf3', 'enf4', 'enf5', 'enf6', 'enf7', 'enf8', 'enf9'])
QUIFOY = Enum(['vous', 'conj', 'pac1', 'pac2', 'pac3', 'pac4', 'pac5', 'pac6', 'pac7', 'pac8', 'pac9'])

CHEF = QUIFAM['chef']
ENFS = [QUIFAM['enf{}'.format(i)] for i in range(1, 10)]

PART = QUIFAM['part']
VOUS = QUIFOY['vous']
#

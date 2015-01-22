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


# TODO switch to to average tax rates

from __future__ import division

import copy

import logging

from openfisca_core import reforms
from openfisca.france import entities

from openfisca_france_data.model.input_variables.survey_variables import add_survey_columns_to_entities


log = logging.getLogger(__name__)


def build_reform(tax_benefit_system):
    # Update legislation
    reference_legislation_json = tax_benefit_system.legislation_json
    survey_legislation_json = copy.deepcopy(reference_legislation_json)

    # Update formulas
    survey_entity_class_by_key_plural = reforms.clone_entity_classes(entities.entity_class_by_key_plural)
    SurveyIndividus = survey_entity_class_by_key_plural['indvidus']

    del SurveyIndividus.column_by_name['birth']
    SurveyIndividus.column_by_name['agem'].formula_class = None
    SurveyIndividus.column_by_name['age'].formula_class = None

    add_survey_columns_to_entities(survey_entity_class_by_key_plural)

    from openfisca_france_data.model.model import add_survey_formulas_to_entities
    add_survey_formulas_to_entities(survey_entity_class_by_key_plural)

    return reforms.Reform(
        entity_class_by_key_plural = survey_entity_class_by_key_plural,
        legislation_json = survey_legislation_json,
        name = u'openfisca_survey',
        reference = tax_benefit_system,
        )

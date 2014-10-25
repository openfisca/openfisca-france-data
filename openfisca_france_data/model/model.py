# -*- coding: utf-8 -*-


# OpenFisca -- A versatile microsimulation software
# By: OpenFisca Team <contact@openfisca.fr>
#
# Copyright (C) 2011, 2012, 2013, 2014 OpenFisca Team
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


# TODO: actualiser la date des end (c'est souvent 2014 ou 2015)


from functools import partial


from openfisca_core.columns import EnumCol, FloatCol, IntCol
from openfisca_core.enumerations import Enum
from openfisca_core.formulas import (
    build_alternative_formula,
    build_dated_formula,
    build_select_formula,
    build_simple_formula,
    )
from openfisca_france import entities


build_alternative_formula = partial(
    build_alternative_formula,
    entity_class_by_symbol = entities.entity_class_by_symbol,
    )
build_dated_formula = partial(
    build_dated_formula,
    entity_class_by_symbol = entities.entity_class_by_symbol,
    )
build_select_formula = partial(
    build_select_formula,
    entity_class_by_symbol = entities.entity_class_by_symbol,
    )
build_simple_formula = partial(
    build_simple_formula,
    entity_class_by_symbol = entities.entity_class_by_symbol,
    )


from . import calage as cl
from . import common as cm
from .cotisations_sociales import travail as cs_travail


############################################################
# Cotisations sociales
############################################################

# Salaires
build_simple_formula(
    'type_sal',
    EnumCol(
        function = cs_travail._type_sal,
        label = u"Catégorie de salarié",
        enum = Enum(
            [
                u"prive_non_cadre",
                u"prive_cadre",
                u"public_titulaire_etat",
                u"public_titulaire_militaire",
                u"public_titulaire_territoriale",
                u"public_titulaire_hospitaliere",
                u"public_non_titulaire",
                ],
            ),
        url = u"http://fr.wikipedia.org/wiki/Professions_et_cat%C3%A9gories_socioprofessionnelles_en_France",
        ),
    replace = True,
    )
build_simple_formula(
    'taille_entreprise',
    EnumCol(
        function = cs_travail._taille_entreprise,
        enum = Enum(
            [
                u"Non pertinent",
                u"Moins de 10 salariés",
                u"De 10 à 19 salariés",
                u"De 20 à 249 salariés",
                u"Plus de 250 salariés",
                ]
            ),
        label = u"Catégorie de taille d'entreprise (pour calcul des cotisations sociales)",
        url = u"http://www.insee.fr/fr/themes/document.asp?ref_id=ip1321",
        ),
    replace = True,
    )
############################################################
# Catégories
############################################################
build_simple_formula(
    'nb_ageq0',
    IntCol(
        function = cl._nb_ageq0,
        entity = 'men',
        label = u"Effectifs des tranches d'âge quiquennal",
        survey_only = True,
        ),
    )
build_simple_formula(
    'decile',
    EnumCol(
        function = cm._decile,
        entity = 'men',
        label = u"Décile de niveau de vie disponible",
        enum = Enum(
            [
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
                ]
            ),
        survey_only = True,
        ),
    )
build_simple_formula(
    'decile_net',
    EnumCol(
        function = cm._decile_net,
        entity = 'men',
        label = u"Décile de niveau de vie net",
        enum = Enum(
            [
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
                ]
            ),
        survey_only = True,
        ),
    )
build_simple_formula(
    'pauvre40',
    EnumCol(
        function = cm._pauvre40,
        entity = 'men',
        label = u"Pauvreté monétaire au seuil de 40%",
        enum = Enum(
            [
                u"Ménage au dessus du seuil de pauvreté à 40%",
                u"Ménage en dessous du seuil de pauvreté à 40%",
                ]
            ),
        survey_only = True,
        ),
    )
build_simple_formula(
    'pauvre50',
    EnumCol(
        function = cm._pauvre50,
        entity = 'men',
        label = u"Pauvreté monétaire au seuil de 50%",
        enum = Enum(
            [
                u"Ménage au dessus du seuil de pauvreté à 50%",
                u"Ménage en dessous du seuil de pauvreté à 50%"
                ],
            ),
        survey_only = True,
        ),
    )
build_simple_formula(
    'pauvre60',
    EnumCol(
        function = cm._pauvre60,
        entity = 'men',
        label = u"Pauvreté monétaire au seuil de 60%",
        enum = Enum(
            [
                u"Ménage au dessus du seuil de pauvreté à 50%",
                u"Ménage en dessous du seuil de pauvreté à 50%"
                ],
            ),
        survey_only = True,
        ),
    )
build_simple_formula(
    'champm_ind',
    FloatCol(
        function = cm._champm_ind,
        entity = 'ind',
        label = u"L'individu est dans un ménage du champ ménage",
        survey_only = True,
        ),
    )
build_simple_formula(
    'champm_foy',
    FloatCol(
        function = cm._champm_foy,
        entity = 'foy',
        label = u"Le premier déclarant du foyer est dans un ménage du champ ménage",
        survey_only = True,
        ),
    )
build_simple_formula(
    'champm_fam',
    FloatCol(
        function = cm._champm_fam,
        entity = 'fam',
        label = u"Le premier parent de la famille est dans un ménage du champ ménage",
        survey_only = True,
        ),
    )
build_simple_formula(
    'weight_ind',
    FloatCol(
        function = cm._weight_ind,
        entity = 'ind',
        label = u"Poids de l'individu",
        survey_only = True,
        ),
    )
build_simple_formula(
    'weight_foy',
    FloatCol(
        function = cm._weight_foy,
        entity = 'foy',
        label = u"Poids du foyer",
        survey_only = True,
        ),
    )
build_simple_formula(
    'weight_fam',
    FloatCol(
        function = cm._weight_fam,
        entity = 'fam',
        label = u"Poids de la famille",
        survey_only = True,
        ),
    )

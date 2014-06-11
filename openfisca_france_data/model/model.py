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

#TODO: actualiser la date des end (c'est souvent 2014 ou 2015)


import collections

from openfisca_core.columns import EnumCol, FloatCol, IntCol
from openfisca_core.enumerations import Enum
from openfisca_core.formulas import AlternativeFormula, DatedFormula, SelectFormula, SimpleFormula

from openfisca_france import entities
from . import calage as cl
from . import common as cm

from .cotisations_sociales import travail as cs_travail
#from .cotisations_sociales import lps as cs_lps  # TODO: remove frome here
#from . import inversion_revenus as inv_rev
#from . import irpp as ir
#from . import irpp_charges_deductibles as cd
#from . import irpp_credits_impots as ci
#from . import irpp_plus_values_immo as immo
#from . import irpp_reductions_impots as ri
#from . import isf as isf
#from . import lgtm as lg
#from . import mini as ms
#from . import pfam as pf
#from . import th as th


def build_alternative_formula_couple(name, functions, column):
    assert isinstance(name, basestring), name
    name = unicode(name)
    assert isinstance(functions, list), functions
    assert column.function is None

    alternative_formulas_constructor = []
    for function in functions:
        formula_class = type(name.encode('utf-8'), (SimpleFormula,), dict(
            function = staticmethod(function),
            ))
        formula_class.extract_parameters()
        alternative_formulas_constructor.append(formula_class)
    column.formula_constructor = formula_class = type(name.encode('utf-8'), (AlternativeFormula,), dict(
        alternative_formulas_constructor = alternative_formulas_constructor,
        ))
    if column.label is None:
        column.label = name
    assert column.name is None
    column.name = name

    entity_column_by_name = entities.entity_class_by_symbol[column.entity].column_by_name
    assert name not in entity_column_by_name, name
    entity_column_by_name[name] = column

    return (name, column)


def build_dated_formula_couple(name, dated_functions, column):
    assert isinstance(name, basestring), name
    name = unicode(name)
    assert isinstance(dated_functions, list), dated_functions
    assert column.function is None

    dated_formulas_class = []
    for dated_function in dated_functions:
        assert isinstance(dated_function, dict), dated_function

        formula_class = type(
            name.encode('utf-8'),
            (SimpleFormula,),
            dict(
                function = staticmethod(dated_function['function']),
                ),
            )
        formula_class.extract_parameters()
        dated_formulas_class.append(dict(
            end = dated_function['end'],
            formula_class = formula_class,
            start = dated_function['start'],
            ))

    column.formula_constructor = formula_class = type(name.encode('utf-8'), (DatedFormula,), dict(
        dated_formulas_class = dated_formulas_class,
        ))
    if column.label is None:
        column.label = name
    assert column.name is None
    column.name = name

    entity_column_by_name = entities.entity_class_by_symbol[column.entity].column_by_name
    assert name not in entity_column_by_name, name
    entity_column_by_name[name] = column

    return (name, column)


def build_select_formula_couple(name, main_variable_function_couples, column):
    assert isinstance(name, basestring), name
    name = unicode(name)
    assert isinstance(main_variable_function_couples, list), main_variable_function_couples
    assert column.function is None

    formula_constructor_by_main_variable = collections.OrderedDict()
    for main_variable, function in main_variable_function_couples:
        formula_class = type(name.encode('utf-8'), (SimpleFormula,), dict(
            function = staticmethod(function),
            ))
        formula_class.extract_parameters()
        formula_constructor_by_main_variable[main_variable] = formula_class
    column.formula_constructor = formula_class = type(name.encode('utf-8'), (SelectFormula,), dict(
        formula_constructor_by_main_variable = formula_constructor_by_main_variable,
        ))
    if column.label is None:
        column.label = name
    assert column.name is None
    column.name = name

    entity_column_by_name = entities.entity_class_by_symbol[column.entity].column_by_name
    assert name not in entity_column_by_name, name
    entity_column_by_name[name] = column

    return (name, column)


def build_simple_formula_couple(name, column, replace = False):
    assert isinstance(name, basestring), name
    name = unicode(name)

    column.formula_constructor = formula_class = type(name.encode('utf-8'), (SimpleFormula,), dict(
        function = staticmethod(column.function),
        ))
    formula_class.extract_parameters()
    del column.function
    if column.label is None:
        column.label = name
    assert column.name is None
    column.name = name

    entity_column_by_name = entities.entity_class_by_symbol[column.entity].column_by_name
    if not replace:
        assert name not in entity_column_by_name, name
    entity_column_by_name[name] = column

    return (name, column)


prestation_by_name = collections.OrderedDict((
    ############################################################
    # Cotisations sociales
    ############################################################

    # Salaires
    build_simple_formula_couple(
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
        ),
    build_simple_formula_couple(
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
        ),
    ############################################################
    # Catégories
    ############################################################
    build_simple_formula_couple(
        'nb_ageq0',
        IntCol(
            function = cl._nb_ageq0,
            entity = 'men',
            label = u"Effectifs des tranches d'âge quiquennal",
            survey_only = True,
            )
        ),
    build_simple_formula_couple(
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
        ),
    build_simple_formula_couple(
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
            )
        ),
    build_simple_formula_couple(
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
            )
        ),
    build_simple_formula_couple(
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
            )
        ),
    build_simple_formula_couple(
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
            )
        ),
    build_simple_formula_couple(
        'champm_ind',
        FloatCol(
            function = cm._champm_ind,
            entity = 'ind',
            label = u"L'individu est dans un ménage du champ ménage",
            survey_only = True,
            )
        ),
    build_simple_formula_couple(
        'champm_foy',
        FloatCol(
            function = cm._champm_foy,
            entity = 'foy',
            label = u"Le premier déclarant du foyer est dans un ménage du champ ménage",
            survey_only = True,
            )
        ),
    build_simple_formula_couple(
        'champm_fam',
        FloatCol(
            function = cm._champm_fam,
            entity = 'fam',
            label = u"Le premier parent de la famille est dans un ménage du champ ménage",
            survey_only = True,
            )
        ),
    build_simple_formula_couple(
        'weight_ind',
        FloatCol(
            function = cm._weight_ind,
            entity = 'ind',
            label = u"Poids de l'individu",
            survey_only = True,
            )
        ),
    build_simple_formula_couple(
        'weight_foy',
        FloatCol(
            function = cm._weight_foy,
            entity = 'foy',
            label = u"Poids du foyer",
            survey_only = True,
            )
        ),
    build_simple_formula_couple(
        'weight_fam',
        FloatCol(
            function = cm._weight_fam,
            entity = 'fam',
            label = u"Poids de la famille",
            survey_only = True,
            )
        ),
    )
)

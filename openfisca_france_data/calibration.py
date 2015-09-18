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


import logging
import numpy
from numpy import logical_not
from pandas import DataFrame, read_csv
from openfisca_core.calmar import calmar
from openfisca_core.columns import AgeCol, BoolCol, EnumCol

log = logging.getLogger(__name__)


class Calibration(object):
    """
    An object to calibrate survey data of a SurveySimulation
    """
    filter_by_name = None
    initial_total_population = None
    margins_by_name = None
    parameters = {
        'use_proportions': True,
        'pondini': None,
        'method': None,  # 'linear', 'raking ratio', 'logit'
        'up': None,
        'lo': None
        }
    survey_scenario = None
    total_population = None
    weight_name = None
    initial_weight_name = None

    def __init__(self, survey_scenario = None):
        self.filter_by_name = "champm"
        assert survey_scenario is not None
        self.survey_scenario = survey_scenario

    def set_total_population(self, total_population):
        """
        Sets total population
        """
        self.total_population = total_population

    def reset(self):
        """
        Reset the calibration to it initial state
        """
        simulation = self.survey_scenario.simulation
        holder = simulation.get_or_new_holder(self.weight_name)
        holder.array = numpy.array(self.initial_weight, dtype = holder.column.dtype)

    def set_survey_scenario(self, survey_scenario):
        """
        Set simulation
        """
        self.survey_scenario = survey_scenario
        if survey_scenario.simulation is None:
            survey_scenario.simulation = survey_scenario.new_simulation()
        # self.entity = 'men'  # TODO: shoud not be france specific
        self.filter_by = filter_by = survey_scenario.simulation.calculate(self.filter_by_name)
        self.weight_name = weight_name = self.survey_scenario.weight_column_name_by_entity_key_plural['menages']
        self.initial_weight_name = weight_name + "_ini"
        self.initial_weight = initial_weight = survey_scenario.simulation.calculate(weight_name)
        self.initial_total_population = sum(initial_weight * filter_by)
        self.weight = survey_scenario.simulation.calculate(weight_name)

    def set_parameters(self, parameter, value):
        """
        Set parameter
        """
        if parameter == 'lo':
            self.parameters['lo'] = 1 / value
        else:
            self.parameters[parameter] = value

    def set_margins_target_from_file(self, filename, year, source):
        """
        Sets margins for inputs variable from file
        """
        # TODO read from h5 files
        with open(filename) as f_tot:
            totals = read_csv(f_tot, index_col = (0, 1))
        # if data for the configured year is not availbale leave margins empty
        year = str(year)
        if year not in totals:
            return
        margins = {}
        if source == "input":
            self.input_margins_data_frame = totals.rename(columns = {year: 'target'}, inplace = False)
        elif source == 'output':
            self.output_margins_data_frame = totals.rename(columns = {year: 'target'}, inplace = False)

        for var, mod in totals.index:
            if var not in margins:
                margins[var] = {}
            margins[var][mod] = totals.get_value((var, mod), year)

        for var in margins.keys():
            if var == 'total_population':
                if source == "input" or source == "config":
                    total_population = margins.pop('total_population')[0]
                    margins['total_population'] = total_population
                    self.total_population = total_population
            else:
                self.add_var2(var, margins[var], source = source)

    def get_parameters(self):
        p = {}
        p['method'] = self.parameters['method']
        p['lo'] = 1 / self.parameters['invlo']
        p['up'] = self.parameters['up']
        p['use_proportions'] = True

        p['pondini'] = self.weight_name + ""
        return p

    def _build_calmar_data(self):
        """
        Builds the data dictionnary used as calmar input argument
        """
        # Select only filtered entities
        assert self.initial_weight_name is not None
        data = {self.initial_weight_name: self.initial_weight * self.filter_by}
        for var in self.margins_by_name:
            if var == 'total_population':
                continue
            assert var in self.survey_scenario.tax_benefit_system.column_by_name.keys()
            data[var] = self.survey_scenario.simulation.calculate(var)
        return data

    def _update_weights(self, margins, parameters = {}):
        """
        Runs calmar, stores new weights and returns adjusted margins
        """
        data = self._build_calmar_data()
        assert self.initial_weight_name is not None
        val_pondfin, lambdasol, updated_margins = calmar(
            data, margins, parameters = parameters, pondini = self.initial_weight_name
            )
        # Updating only afetr filtering weights
        self.weight = val_pondfin * self.filter_by + self.weight * (logical_not(self.filter_by))
        return updated_margins

    def calibrate(self):
        """
        Calibrate according to margins found in frame
        """
        margins_by_name = self.margins_by_name
        parameters = self.get_parameters()

        simple_margins_by_name = dict([
            (variable, margins_by_type['target'])
            for variable, margins_by_type in margins_by_name.iteritems()])

        if self.total_population:
            simple_margins_by_name['total_population'] = self.total_population

        self._update_weights(simple_margins_by_name, parameters = parameters)
        self.update_margins()
#        w = self.weight
#        for var in margins.keys():
#            if var in self.survey_scenario.tax_benefit_system.column_by_name:
#                value = self.survey_scenario.simulation.calculate(var)  # TODO sum over menage
#
#            if isinstance(margins[var], dict):
#                items = [('marge', w), ('mod', value)]
#                updated_margins = DataFrame.from_items(items).groupby('mod', sort = True).sum()
#                for mod in margins[var].keys():
#                    df.set_value((var, mod), u"cible ajustée", adjusted_margins[var][mod])
#                    df.set_value((var, mod), u"marge", updated_margins['marge'][mod])
#            else:
#                updated_margin = (w * value).sum()
#                df.set_value((var, 0), u"cible ajustée", adjusted_margins[var])
#                df.set_value((var, 0), u"marge", updated_margin)
#
#        if self.frame is not None:
#            self.frame = df.reset_index()

    def calibrate_old(self):
        """
        Calibrate according to margins found in frame
        """

        df = self.frame
        margins = {}

        if df is not None:
            df.reset_index(drop = True, inplace = True)
            df.set_index(['var', 'mod'], inplace = True)
            for var, mod in df.index:
                # Dealing with non categorical vars ...
                if df.get_value((var, mod), u"modalités") == 'total':
                    margins[var] = df.get_value((var, mod), 'cible')
                #  ... and categorical vars
                else:
                    if var not in margins:
                        margins[var] = {}
                    margins[var][mod] = df.get_value((var, mod), 'cible')

        parameters = self.get_parameters()

        if self.total_population is not None:
            margins['total_population'] = self.total_population

        adjusted_margins = self.update_weights(margins, parameters = parameters)

        if 'total_population' in margins.keys():
            del margins['total_population']

        w = self.weight
        for var in margins.keys():
            if var in self.survey_scenario.tax_benefit_system.column_by_name:
                value = self.survey_scenario.simulation.calculate(var)  # TODO sum over menage

            if isinstance(margins[var], dict):
                items = [('marge', w), ('mod', value)]
                updated_margins = DataFrame.from_items(items).groupby('mod', sort = True).sum()
                for mod in margins[var].keys():
                    df.set_value((var, mod), u"cible ajustée", adjusted_margins[var][mod])
                    df.set_value((var, mod), u"marge", updated_margins['marge'][mod])
            else:
                updated_margin = (w * value).sum()
                df.set_value((var, 0), u"cible ajustée", adjusted_margins[var])
                df.set_value((var, 0), u"marge", updated_margin)

        if self.frame is not None:
            self.frame = df.reset_index()


    def set_calibrated_weights(self):
        """
        Modify the weights to use the calibrated weights
        """
        simulation = self.survey_scenario.simulation
        holder = simulation.get_or_new_holder(self.weight_name)
        holder.array = numpy.array(self.weight, dtype = holder.column.dtype)
        # TODO: propagation to other weights

    def set_target_margin(self, variable, target):
        survey_scenario = self.survey_scenario
        simulation = survey_scenario.simulation
        column_by_name = survey_scenario.tax_benefit_system.column_by_name
        assert variable in column_by_name
        column = survey_scenario.tax_benefit_system.column_by_name[variable]

        filter_by = self.filter_by
        value = simulation.calculate(variable)
        target_by_category = None
        if column.__class__ in [AgeCol, BoolCol, EnumCol]:
            categories = numpy.sort(numpy.unique(value[filter_by]))
            target_by_category = dict(zip(categories, target))

        # assert len(atrget) = len
        if not self.margins_by_name:
            self.margins_by_name = dict()
        if variable not in self.margins_by_name:
            self.margins_by_name[variable] = dict()
        self.margins_by_name[variable]['target'] = target_by_category or target
        self.update_margins()

    def update_margins(self):
        for variable in self.margins_by_name:
            survey_scenario = self.survey_scenario
            simulation = survey_scenario.simulation
            column_by_name = survey_scenario.tax_benefit_system.column_by_name

            assert variable in column_by_name
            column = survey_scenario.tax_benefit_system.column_by_name[variable]
            weight = self.weight
            filter_by = self.filter_by
            initial_weight = self.initial_weight

            value = simulation.calculate(variable)
            margin_items = [
                ('actual', weight[filter_by]),
                ('initial', initial_weight[filter_by]),
                ]

            if column.__class__ in [AgeCol, BoolCol, EnumCol]:
                margin_items.append(('category', value[filter_by]))
                margins_data_frame = DataFrame.from_items(margin_items)
                margins_data_frame = margins_data_frame.groupby('category', sort = True).sum()
                margin_by_type = margins_data_frame.to_dict()
            else:
                margin_by_type = dict(
                    actual = (weight[filter_by] * value[filter_by]).sum(),
                    initial = (initial_weight[filter_by] * value[filter_by]).sum(),
                    )
            self.margins_by_name[variable].update(margin_by_type)

            if self.total_population is not None:
                 target = self.margins_by_name[variable].get('target', False)


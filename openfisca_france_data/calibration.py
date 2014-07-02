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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


import logging
import numpy
from numpy import logical_not
from pandas import concat, DataFrame, read_csv
from openfisca_core.calmar import calmar
from openfisca_core.columns import AgeCol, BoolCol, EnumCol

log = logging.getLogger(__name__)


class Calibration(object):
    """
    An object to calibrate survey data of a SurveySimulation
    """
    def __init__(self):
        super(Calibration, self).__init__()
        self.filter_by = "champm"
        self.frame = None
        self.initial_total_population = None
        self.input_margins_data_frame = None
        self.output_margins_data_frame = None
        self.parameters = {
            'use_proportions': True,
            'pondini': None,
            'method': None,  # 'linear', 'raking ratio', 'logit'
            'up': None,
            'lo': None
            }
        self.simulation = None
        self.survey_scenario = None
        self.total_population = None
        self.weight_name = None
        # TODO: add a champm option

    def __repr__(self):
        return '%s \n simulation %s ' % (self.__class__.__name__, self.simulation)

    def set_total_population(self, total_population):
        """
        Sets total population
        """
        self.total_population = total_population

    def reset(self):
        """
        Reset the calibration to it initial state
        """
        self.frame = None
        simulation = self.survey_scenario.simulation
        holder = simulation.get_or_new_holder(self.weight_name)
        holder.array = numpy.array(self.initial_weights, dtype = holder.column.dtype)

    def set_survey_scenario(self, survey_scenario):
        """
        Set simulation
        """
        self.survey_scenario = survey_scenario
        if survey_scenario.simulation is None:
            survey_scenario.simulation = survey_scenario.new_simulation()
        self.entity = 'men'  # TODO: shoud not be france specific
        self.champm = survey_scenario.simulation.calculate("champm")
        weight_name = self.survey_scenario.weight_column_name_by_entity_symbol[self.entity]
        self.initial_weights = survey_scenario.simulation.calculate(weight_name)
        self.initial_total_population = sum(self.initial_weights * self.champm)
        self.weight_name = weight_name
        self.weights = survey_scenario.simulation.calculate(weight_name)

    def set_parameters(self, parameter, value):
        """
        Set parameter
        """
        if parameter == 'lo':
            self.parameters['lo'] = 1 / value
        else:
            self.parameters[parameter] = value

    def set_inputs_margins_from_file(self, filename, year):
        self.set_margins_from_file(filename, year, source="input")

    def set_margins_from_file(self, filename, year, source):
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
            if not var in margins:
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

    def add_var2(self, varname, target = None, source = 'free'):
        """
        Add a variable in the dataframe

        Parameters
        ----------

        varname : str
                  name of the variable
        target : float
                 target for the margin of the variable
        source : str, default 'free'
                 database source
        """

        w_init = self.initial_weights * self.champm
        w = self.weights * self.champm

        survey_scenario = self.survey_scenario
        simulation = survey_scenario.simulation
        column_by_name = survey_scenario.tax_benefit_system.column_by_name
#        varcol = self.simulation.get_col(varname)
#        entity = self.entity
#        enum = inputs.column_by_name.get('qui' + self.entity).enum
#        people = [x[1] for x in enum]
#
#        if varname in inputs.column_by_name:
#            value = inputs.get_value(varname, index = idx)
#        elif output_table is not None and varname in output_table.column_by_name:
#            value = output_table.get_value(varname, index = idx, opt = people, sum_ = True)

        if varname in column_by_name:
            value = simulation.calculate(varname)
            column = survey_scenario.tax_benefit_system.column_by_name[varname]
            label = column.label
        else:
            print varname
            return
        # TODO: rewrite this using pivot table

        items = [('marge', w[self.champm]), ('marge initiale', w_init[self.champm])]

        if column.__class__ in [AgeCol, BoolCol, EnumCol]:
            items.append(('mod', value[self.champm]))
            df = DataFrame.from_items(items)
            res = df.groupby('mod', sort = True).sum()
        else:
            res = DataFrame(index = ['total'],
                            data = {'marge': (value * w).sum(),
                                    'marge initiale': (value * w_init).sum()
                                    }
                            )
        res.insert(0, u"modalités", u"")
        res.insert(2, "cible", 0)
        res.insert(2, u"cible ajustée", 0)
        res.insert(4, "source", source)
        mods = res.index

        if target is not None:
            if len(mods) != len(target.keys()):
                drop_indices = [(varname, mod) for mod in target.keys()]
                if source == 'input':
                    self.input_margins_data_frame.drop(drop_indices, inplace=True)
                    self.input_margins_data_frame.index.names = ['var', 'mod']
                if source == 'output':
                    self.output_margins_data_frame.drop(drop_indices, inplace = True)
                    self.output_margins_data_frame.index.names = ['var', 'mod']
                return

        if isinstance(column, EnumCol):
            if column.enum:
                enum = column.enum
                res[u'modalités'] = [enum._vars[mod] for mod in mods]
                res['mod'] = mods
            else:
                res[u'modalités'] = [mod for mod in mods]
                res['mod'] = mods
        elif isinstance(column, BoolCol):
            res[u'modalités'] = bool(mods)
            res['mod'] = mods
        elif isinstance(column, AgeCol):
            res[u'modalités'] = mods
            res['mod'] = mods
        else:
            res[u'modalités'] = "total"
            res['mod'] = 0

        if label is not None:
            res['variable'] = label
        else:
            res['variable'] = varname
        res['var'] = varname

        if target is not None:
            for mod, margin in target.iteritems():
                if mod == varname:    # dirty to deal with non catgorical data
                    res['cible'][0] = margin
                else:
                    res['cible'][mod] = margin

        if self.frame is None:
            self.frame = res
        else:
            self.frame = concat([self.frame, res])
        self.frame = self.frame.reset_index(drop=True)
        print self.frame


    def get_parameters(self):
        p = {}
        p['method'] = self.parameters['method']
        p['lo'] = 1 / self.parameters['invlo']
        p['up'] = self.parameters['up']
        p['use_proportions'] = True

        p['pondini'] = self.weight_name + ""
        return p

    def build_calmar_data(self, margins, weights_in):
        """
        Builds the data dictionnary used as calmar input argument

        Parameters
        ----------
        margins : dict
                 Variables and their margins. A scalar var for numeric variables and a dict with
                 categories key and population
        weights_in : str
                     name of the original weight variable

        Returns
        -------
        data : TODO:
        """
        # Select only champm ménages by nullifying weight for irrelevant ménages
#        inputs = self.simulation.survey
#        output_table = self.simulation.output_table

        data = {weights_in: self.initial_weights * self.champm}
        for var in margins:
#            if var in inputs.column_by_name:
#                data[var] = inputs.get_value(var, self.entity)
#            elif output_table and var in output_table.column_by_name:
#                entity = self.entity
#                enum = inputs.column_by_name.get('qui' + self.entity).enum
#                people = [x[1] for x in enum]
#                data[var] = output_table.get_value(var, entity = entity, opt = people, sum_ = True)
            if var in self.survey_scenario.tax_benefit_system.column_by_name:
                data[var] = self.survey_scenario.simulation.calculate(var)
        return data

    def update_weights(self, margins, parameters = {}, weights_in = None):
        """
        Runs calmar, stores new weights and returns adjusted margins

        Parameters
        ----------
        margins : dict
                 Variables and their margins. A scalar var for numeric variables and a dict with
                 categories key and population
        parameters : dict
                parameters of the calibration
        weights_in : str
                     name of the original weight variable

        Returns
        -------
        marge_new : dict
                    computed values of the margins
        """
        if weights_in is None:
            weights_in = self.weight_name + "_ini"

        data = self.build_calmar_data(margins, weights_in)
        try:
            val_pondfin, lambdasol, updated_margins = calmar(
                data, margins, parameters = parameters, pondini = weights_in
                )
        except Exception, e:
            raise Exception("Calmar returned error '%s'" % e)

        # Updating only champm weights
        self.weights = val_pondfin * self.champm + self.weights * (logical_not(self.champm))
        return updated_margins

    def calibrate(self):
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

        w = self.weights
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
        Modify the weights to use the calibrated weight
        """
        simulation = self.survey_scenario.simulation
        holder = simulation.get_or_new_holder(self.weight_name)
        holder.array = numpy.array(self.weights, dtype = holder.column.dtype)
        # TODO: propagation to other weights

#! /usr/bin/env python
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
#

from __future__ import division


import logging


import numpy as np
from numpy import logical_and as and_
from pandas import merge, concat


from openfisca_france_data.model.common import mark_weighted_percentiles as mwp
from openfisca_france_data.surveys import SurveyCollection
from openfisca_france_data.utils import simulation_results_as_data_frame
from openfisca_france_data.erf import get_erf2of, get_of2erf
from openfisca_plugin_aggregates.aggregates import Aggregates


log = logging.getLogger(__name__)


def clean(parameter):
    return parameter[:-len('_holder')] if parameter.endswith('_holder') else parameter


class Debugger(object):
    def __init__(self):
        super(Debugger, self).__init__()
        self.erf_menage = None
        self.erf_eec_indivi = None
        self.of_menages_data_frame = None
        self.of_individus_data_frame = None
        self.variable = None
        self.survey_scenario = None

    def set_survey_scenario(self, survey_scenario = None):
        """
        Set the simulation to debug

        Parameters
        ----------

        set_survey_scenario : SurveyScenario, default None
                     survey_scenario to debug
        """
        assert survey_scenario is not None
        self.survey_scenario = survey_scenario
        self.column_by_name = self.survey_scenario.simulation.tax_benefit_system.column_by_name
        self.simulation = self.survey_scenario.simulation
        assert survey_scenario.simulation is not None, "The simulation attibute of survey_scenario is None"

    def set_variable(self, variable):
        if isinstance(variable, list):
            self.variable = variable[0]
        else:
            self.variable = variable

    def show_aggregates(self):
        from openfisca_france_data.erf.aggregates import build_erf_aggregates

        assert self.survey_scenario is not None, 'simulation attribute is None'
        assert self.variable is not None, 'variable attribute is None'
        variable = self.variable
        openfisca_aggregates = Aggregates()
        openfisca_aggregates.set_survey_scenario(self.survey_scenario)
        openfisca_aggregates.compute()

        column_by_name = self.column_by_name
        temp = (build_erf_aggregates(variables=[variable], year= self.survey_scenario.year))
        selection = openfisca_aggregates.aggr_frame["Mesure"] == column_by_name[variable].label
        print openfisca_aggregates.aggr_frame[selection]
        print temp
        # TODO: clean this
        return

    def extract(self, data_frame, entities = "men"):
        column_by_name = self.column_by_name
        filtered_data_frame_columns = list(set(column_by_name.keys()).intersection(set(data_frame.columns)))
        extracted_columns = [column_name for column_name in filtered_data_frame_columns
                             if column_by_name[column_name].entity in entities]
        extracted_columns = list(set(extracted_columns).union(set(['idmen'])))
        return data_frame[extracted_columns].copy()

    def get_all_parameters(self, column_list):
        column_by_name = self.column_by_name
        simulation = self.simulation
        if len(column_list) == 0:
            return []
        else:
            column_name = column_list[0].name
            holder = simulation.get_or_new_holder(column_name)
            formula = holder.real_formula
            print column_name, holder
            if formula is None:
                return [column_list[0]] + self.get_all_parameters(column_list[1:])
            else:
                return (
                    [column_list[0]] +
                    self.get_all_parameters(
                        [column_by_name[clean(parameter)] for parameter in formula.parameters]
                        ) +
                    self.get_all_parameters(column_list[1:]))

    def build_columns_to_fetch(self):
        column_by_name = self.column_by_name
        parameters_column = self.get_all_parameters([column_by_name.get(x) for x in [self.variable]])
        parameters = [x.name for x in parameters_column]
        # We want to get all parameters and consumers that we're going to encounter
        consumers = []
        for variable in [self.variable]:
            column = column_by_name.get(variable)
            consumers = list(set(consumers).union(set(column.consumers)))
        column_names = list(set(parameters).union(set(consumers)))
        self.columns_to_fetch = column_names
        self.variable_consumers = list(set(consumers))
        self.variable_parameters = list(set(parameters))

    def build_openfisca_data_frames(self):
        column_by_name = self.column_by_name

        def get_var(column_name):
            force_sum = True
            if column_name.endswith('_original'):
                force_sum = False
            column_names = [column_name]
            return simulation_results_as_data_frame(
                survey_scenario = survey_scenario,
                column_names = column_names,
                entity = "men",
                force_sum = force_sum)[column_name]

        column_names = self.columns_to_fetch
        of_menages_data_frame = concat(
            [get_var(column_name) for column_name in column_names + ["idmen_original"]],
            axis = 1,
            )
        idmen_to_idmen_original = dict(
            zip(
                of_menages_data_frame.index.values,
                of_menages_data_frame["idmen_original"].values
                )
            )
        of_menages_data_frame.rename(columns = {"idmen_original": "idmen"}, inplace = True)
       # First from the output_table
        # We recreate the noindiv in output_table
        individual_column_names = [
            column_name for column_name in column_names if column_by_name[column_name].entity != 'men'
            ]
        of_individus_data_frame = simulation_results_as_data_frame(
            survey_scenario = survey_scenario,
            column_names = individual_column_names + ['idfam', 'idmen', 'quifam', 'quimen'],
            entity = "ind",
            force_sum = False,
            )
        self.of_menages_data_frame = of_menages_data_frame
        self.of_individus_data_frame = of_individus_data_frame.replace(
            {'idmen': idmen_to_idmen_original}
            )

    def build_erf_data_frames(self):
        variables = self.columns_to_fetch
        erf_survey_collection = SurveyCollection.load(collection = "erfs")
        erf_survey = erf_survey_collection.surveys["erfs_{}".format(year)]

        erf_variables = list(set(variables + ["ident", "wprm", "quelfic", "noi"]))
        of2erf = get_of2erf()
        for index, variable in enumerate(erf_variables):
            if variable in of2erf:
                erf_variables[index] = of2erf[variable]
        data_frame_by_table = dict(eec_indivi = None, erf_indivi = None, erf_menage = None)
        erf_variables_by_table = dict(eec_indivi = [], erf_indivi = [], erf_menage = [])
        table_by_erf_variable = dict(
            [
                (
                    erf_variable,
                    set(
                        erf_survey.find_tables(variable = erf_variable)
                        ).intersection(
                        set(erf_variables_by_table.keys())
                        )
                    ) for erf_variable in erf_variables
                ]
            )
        for variable, tables in table_by_erf_variable.iteritems():
            if len(tables) < 1:
                log.info("No tables are present for variable {}".format(variable))
                continue
            else:
                log.info("Variable {} is present in multiple tables : {}".format(variable, tables))
                for table in tables:
                    log.info("Variable {} is retrieved from table {}".format(variable, table))
                    erf_variables_by_table[table].append(variable)

        erf2of = get_erf2of()
        for table, erf_variables in erf_variables_by_table.iteritems():
            if erf_variables:
                data_frame_by_table[table] = erf_survey.get_values(variables = erf_variables, table = table)
                data_frame_by_table[table].rename(columns = erf2of, inplace = True)
                data_frame_by_table[table].rename(columns = {'ident': 'idmen'}, inplace = True)

        assert not data_frame_by_table["erf_menage"].duplicated().any(), "Duplicated idmen in erf_menage"
        self.erf_menages_data_frame = data_frame_by_table["erf_menage"]
        self.erf_eec_individus_data_frame = data_frame_by_table["erf_indivi"].merge(
            data_frame_by_table["eec_indivi"],
            )

    def get_major_differences(self):
        self.build_columns_to_fetch()
        self.build_erf_data_frames()
        self.build_openfisca_data_frames()
        variable = self.variable
        erf_menages_data_frame = self.erf_menages_data_frame
        of_menages_data_frame = self.of_menages_data_frame
        merged_menage_data_frame = merge(
            erf_menages_data_frame[[variable, 'idmen']],
            of_menages_data_frame[[variable, 'idmen']],
            on = 'idmen',
            how = 'inner',
            suffixes = ('_erf', '_of')
            )
        log.info('Length of merged_menage_data_frameis {}'.format(len(merged_menage_data_frame)))
        merged_menage_data_frame.set_index('idmen', drop = False, inplace = True)
        table = merged_menage_data_frame[
            and_(
                merged_menage_data_frame[variable + '_erf'] != 0,
                merged_menage_data_frame[variable + '_of'] != 0
                )
            ]
        table[variable + "_rel_diff"] = (table[variable + '_of'] - table[variable + '_erf']) \
            / table[variable + '_erf']  # Difference relative
        log.info(
            "Minimum difference between the two tables for {} is {}".format(
                variable, str(table[variable + "_rel_diff"].min())
                )
            )
        log.info(
            "Maximum difference between the two tables for {} is {}".format(
                variable, str(table[variable + "_rel_diff"].max())
                )
            )
        table[variable + '_ratio'] = (
            table[variable + '_of'] / table[variable + '_erf']
            )
        log.info(table[variable + "_rel_diff"].describe())
        try:
            assert len(table[variable + "_rel_diff"]) == len(table['wprm_of']), "PINAGS"
            dec, values = mwp(
                table[variable + "_rel_diff"],
                np.arange(1, 11), table['wprm_of'],
                2,
                return_quantiles = True
                )
            log.info(sorted(values))
            dec, values = mwp(
                table[variable + "_rel_diff"],
                np.arange(1, 101),
                table['wprm_erf'],
                2,
                return_quantiles = True
                )
            log.info(sorted(values)[90:])
            del dec, values
        except:
            log.info('Weighted percentile method did not work for {}'.format(variable + "_rel_diff"))
            pass
        table.sort(columns = variable + "_rel_diff", ascending = False, inplace = True)
        return table

    def describe_discrepancies(self, fov = 10, consumers = False, parameters = True, descending = True, to_men = False):
        variable = self.variable
        major_differences_data_frame = self.get_major_differences()
        major_differences_data_frame.sort(
            columns = self.variable + "_rel_diff",
            ascending = not descending,
            inplace = True
            )
        debug_data_frame = major_differences_data_frame[0:fov]
        of_menages_data_frame = self.of_menages_data_frame
        of_individus_data_frame = self.of_individus_data_frame
        erf_eec_individus_data_frame = self.erf_eec_individus_data_frame
        erf_menages_data_frame = self.erf_menages_data_frame

        kept_columns = set()
        if parameters:
            kept_columns.update(set(self.variable_parameters))
        if consumers:
            kept_columns.update(set(self.variable_consumers))
        kept_columns = list(kept_columns)
        kept_columns = list(set(kept_columns).union(
            set(['idmen', 'idfam', 'idfoy', 'quimen', 'quifam', 'quifoy'] + list(major_differences_data_frame.columns)))
            )

        if to_men:
            entities_ind = ['ind']
            entities_men = ['men', 'fam', 'foy']
        else:
            entities_ind = ['ind', 'fam', 'foy']
            entities_men = ['men']

        debug_data_frame = debug_data_frame.merge(
            self.extract(of_menages_data_frame, entities = entities_men),
            how = 'inner',
            on = 'idmen',
            )
        debug_data_frame = debug_data_frame.merge(
            self.extract(of_individus_data_frame, entities = entities_ind),
            how = 'inner',
            on = 'idmen',
            )
        suffixes = ["_erf", "_of", "_rel_diff", "_ratio"]
        reordered_columns = [variable + suffixe for suffixe in suffixes] \
            + ["idmen", "quimen", "idfam", "quifam", "idfoy", "quifoy"]
        reordered_columns = reordered_columns + list(set(kept_columns) - set(reordered_columns))
        debug_data_frame = debug_data_frame[reordered_columns].copy()
        print debug_data_frame.to_string()


if __name__ == '__main__':
    import sys
    from openfisca_plugin_aggregates.tests.test_aggregates import create_survey_scenario
    logging.basicConfig(level = logging.INFO, stream = sys.stdout)
    restart = True
    if restart:
        year = 2006
        survey_scenario = create_survey_scenario(year)
        survey_scenario.simulation = survey_scenario.new_simulation()

    debugger = Debugger()
    debugger.set_survey_scenario(survey_scenario = survey_scenario)
    debugger.set_variable('af')

#    debugger.show_aggregates()
    debugger.describe_discrepancies(descending = False)

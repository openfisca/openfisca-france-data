# -*- coding:utf-8 -*-
# Created on 5 juil. 2013
# This file is part of OpenFisca.
# OpenFisca is a socio-fiscal microsimulation software
# Copyright ©2013 Clément Schaff, Mahdi Ben Jelloul
# Licensed under the terms of the GVPLv3 or later license
# (see openfisca/__init__.py for details)

# Author: Victor Le Breton


from __future__ import division

import gc
import logging
import os


import numpy as np
from numpy import logical_and as and_
from pandas import merge, concat

from openfisca_france_data.model.common import mark_weighted_percentiles as mwp
from openfisca_france_data.surveys import SurveyCollection
from openfisca_france_data.utils import simulation_results_as_data_frame
#from openfisca_france.data.erf.datatable import DataCollection
from openfisca_france_data.erf import get_erf2of, get_of2erf
from openfisca_plugin_aggregates.aggregates import Aggregates

#from .common import load_content


log = logging.getLogger(__name__)


def clean(parameter):
    return parameter[:-len('_holder')] if parameter.endswith('_holder') else parameter


class Debugger(object):
    def __init__(self):
        super(Debugger, self).__init__()
        self.erf_menage = None
        self.erf_eec_indivi = None
        self.simu_aggr_tables = None
        self.simu_nonaggr_tables = None

        self.variable = None
        self.survey_scenario = None

    def set_survey_scenario(self, survey_scenario = None, name = None, filename = None):
        """
        Set the simulation to debug

        Parameters
        ----------

        set_survey_scenario : SurveyScenario, default None
                     survey_scenario to debug
        name : str, default None
               name of the simulation to retrieve from filename
        filename : str, default None
                   path to the filename
        """
        assert survey_scenario is not None
#            try:
#                self.survey_scenario = load_content(name, filename) # TODO
#            except:
#                assert filename is not None and name is not None, 'filename and/or name is None'
#                log.info("load_content did not work for filename {}, name {}. Please verify".format(filename, name))
#        else:
        self.survey_scenario = survey_scenario
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

        column_by_name = self.survey_scenario.tax_benefit_system.column_by_name
        temp = (build_erf_aggregates(variables=[variable], year= self.survey_scenario.year))
        selection = openfisca_aggregates.aggr_frame["Mesure"] == column_by_name[variable].label
        print openfisca_aggregates.aggr_frame[selection]

        print temp
        # TODO: clean this
        return

    def preproc(self):

        simu_aggr_tables = self.simu_aggr_tables
        simu_nonaggr_tables = self.simu_nonaggr_tables
        column_by_name = self.survey_scenario.simulation.tax_benefit_system.column_by_name
        simulation = self.survey_scenario.simulation

        def get_all_ancestors(column_list):

            if len(column_list) == 0:
                return []
            else:
                column_name = column_list[0].name
                holder = simulation.get_or_new_holder(column_name)
                formula = holder.real_formula
#                print column_name, holder
                if formula is None:
                    return [column_list[0]] + get_all_ancestors(column_list[1:])
                else:
                    return (
                        [column_list[0]] +
                        get_all_ancestors(
                            [column_by_name[clean(parameter)] for parameter in formula.parameters]
                            ) +
                        get_all_ancestors(column_list[1:]))

        # We want to get all ancestors + children + the options that we're going to encounter

        parents = [column_by_name.get(x) for x in [self.variable]]
        parents = get_all_ancestors(parents)
        parents = [x.name for x in parents]
        for var in [self.variable]:
            children = set()
            varcol = column_by_name.get(var)
            children = children.union(set(varcol.consumers))
        variables = list(set(parents + list(children)))

        def get_var(variable):
            force_sum = True
            if variable.endswith('_original'):
                force_sum = False
            print variable
            variables = [variable]
            return simulation_results_as_data_frame(
                survey_scenario = survey_scenario,
                column_names = variables,
                entity = "men",
                force_sum = force_sum)[variable]

        simu_aggr_tables = concat([get_var(variable) for variable in variables + ["idmen_original"]], axis = 1)
        simu_aggr_tables.rename(columns = {"idmen_original": "idmen"}, inplace = True)
        # We load the data from erf table in case we have to pick data there
        erf_survey_collection = SurveyCollection.load(collection = "erfs")
        erf_survey = erf_survey_collection.surveys["erfs_{}".format(year)]
        os.system('cls')
        augmented_variables = list(set(variables + ["ident", "wprm", "quelfic"]))
        log.info("Variables or equivalents to fetch : {}".format(augmented_variables))
        erf_variables = augmented_variables[:]
        erf_variables.append("ident")
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
        # TODO use of2erf to check
        for variable, table in table_by_erf_variable.iteritems():
            if len(table) < 1:
                log.info("No tables are present for variable {}".format(variable))
                continue
            elif len(table) > 1:
                log.info("Variable {} is present in multiple tables : {}".format(variable, table))
                if "erf_menage" in table:
                    log.info("Variable {} is retrieved from table {}".format(variable, table))
                    erf_variables_by_table["erf_menage"].append(variable)
                elif "erf_indivi" in table:
                    log.info("Variable {} is retrieved from table {}".format(variable, table))
                    erf_variables_by_table["erf_indivi"].append(variable)
            else:
                erf_variables_by_table[list(table)[0]].append(variable)

        for table, erf_variables in erf_variables_by_table.iteritems():
            if erf_variables:
                data_frame_by_table[table] = erf_survey.get_values(variables = erf_variables, table = table)

#        fetch_eec = ['statut', 'titc', 'chpub', 'encadr', 'prosa', 'age', 'naim', 'naia', 'noindiv']
#        fetch_erf = ['zsali', 'ident', 'wprm', 'noi', 'noindiv', 'quelfic']

        # We then get the aggregate variables for the menage ( mainly to compare with of )

        erf2of = get_erf2of()
        data_frame_by_table["erf_menage"].rename(columns = erf2of, inplace = True)

    # We get the options from the simulation non aggregated tables:

        # First from the output_table
        # We recreate the noindiv in output_table
        of_variables = [
                var for var in set(variables).intersection(set(column_by_name.keys()))
                ] + ['idmen', 'quimen'] #, 'noindiv']
        simu_nonaggr_tables = simulation_results_as_data_frame(
            survey_scenario = survey_scenario,
            column_names = of_variables,
            entity = "ind",
            force_sum = False,
            )
#        assert 'noindiv' in simu_nonaggr_tables.columns
        erf_menage = data_frame_by_table["erf_menage"]
        assert 'idmen' in simu_nonaggr_tables.columns, 'Idmen not in simu_nonaggr_tables columns'
        assert "ident" in erf_menage.columns
        # Check the idmens that are not common
        erf_menage.rename(columns = {'ident': 'idmen'}, inplace = True)
        #print 'Dropping duplicates of idmen for both tables...'
        assert not erf_menage["idmen"].duplicated().any(), "Duplicated idmen in erf_menage"
#        assert not simu_aggr_tables["idmen"].duplicated().any(), "Duplicated idmen in  Openfisca"
        # Compare differences across of and erf dataframes
        log.info("Comparing differences between dataframes ")
        common_columns = set(erf_menage.columns).intersection(set(simu_aggr_tables.columns)) - set(['idmen', 'wprm'])
        log.info("Common variables : \n {}".format(common_columns))
#        erf_menage.reset_index(inplace = True)
#        simu_aggr_tables.reset_index(inplace = True)
#        for col in common_columns:
#            temp = set(erf_menage['idmen'][erf_menage[col] != simu_aggr_tables[col]])
#            print "Numbers of idmen that aren't equal on variable %s : %s \n" %(col, str(len(temp)))
#            del temp
#
        self.erf_menage = erf_menage
#        self.erf_eec_indivi = data_frame_by_table["erf_eec_indivi"] TODO need to create this one
        self.simu_aggr_tables = simu_aggr_tables
        self.simu_nonaggr_tables = simu_nonaggr_tables

    def describe_discrepancies(self, fov = 10, descending = True):
        """
        Describe discrepancies

        Parameters
        ----------
        fov :
        descending :
        """
        erf_menage = self.erf_menage
        erf_eec_indivi = self.erf_eec_indivi
        simu_aggr_tables = self.simu_aggr_tables
        simu_nonaggr_tables = self.simu_nonaggr_tables
        column_by_name = self.survey_scenario.simulation.tax_benefit_system.column_by_name
        simulation = self.survey_scenario.simulation

        # Detect the biggest differences
        merged_menage_data_frame = merge(
            erf_menage,
            simu_aggr_tables,
            on = 'idmen',
            how = 'inner',
            suffixes = ('_erf', '_of')
            )
        log.info('Length of merged_menage_data_frameis %s'.format(len(merged_menage_data_frame)))
        merged_menage_data_frame.set_index('idmen', drop = False, inplace = True)

        already_met = []

        for col in [self.variable]:
            debug_data_frame_by_entity = None
            table = merged_menage_data_frame[
                and_(
                    merged_menage_data_frame[col + '_erf'] != 0,
                    merged_menage_data_frame[col + '_of'] != 0
                    )
                ]
            table[col] = (table[col + '_of'] - table[col + '_erf']) / table[col + '_erf']  # Difference relative
            log.info(
                "Minimum difference between the two tables for {} is {}".format(
                    col, str(table[col].min())
                    )
                )
            log.info(
                "Maximum difference between the two tables for {} is {}".format(
                    col, str(table[col].max())
                    )
                )
            log.info(table[col].describe())

            try:
                assert len(table[col]) == len(table['wprm_of']), "PINAGS"
                dec, values = mwp(table[col], np.arange(1, 11), table['wprm_of'], 2, return_quantiles = True)
                print sorted(values)
                dec, values = mwp(table[col], np.arange(1, 101), table['wprm_erf'], 2, return_quantiles = True)
                print sorted(values)[90:]
                del dec, values
            except:
                log.info('Weighted percentile method didnt work for {}'.format(col))
                pass
            print "\n"

        # Show the relevant information for the most deviant households
            table.sort(columns = col, ascending = not descending, inplace = True)
            if debug_data_frame_by_entity is None:
                debug_data_frame_by_entity = {
                    'menage': table[[col, col + '_of', col + '_erf', 'idmen']][0:fov],
                    'individus': None,
                    }
            debug_data_frame_by_entity['menage'][col + '_ratio'] = debug_data_frame_by_entity['menage'][col + '_of'] / debug_data_frame_by_entity['menage'][col + '_erf']
            print debug_data_frame_by_entity['menage'].to_string()

            '''
            debug_data_frame_by_entity is the table which will get filled little by little by the relevant variables.
            Up to the last rows of code 'menage' refers to a table of aggregated values,
            while 'options is a table of individual variables.
            The reason we call it in a dictionnary is also because
            we modify it inside the recursive function 'iter_on parents',
            and it causes an error in Python unless for certain types like dictionnary values.
            '''
            # If variable is a Prestation, we show the dependancies
            varcol = self.survey_scenario.tax_benefit_system.column_by_name.get(col)
            if True:  # isinstance(varcol, Prestation):
                '''
                For the direct children
                '''
                if not varcol.consumers is None:
                    consumers_to_fetch = [consumer for consumer in varcol.consumers]
                    consumers_fetched = []

                    if set(consumers_to_fetch) <= set(simu_aggr_tables.columns):
                        log.info("Variables which need {} to be computed :\n {} \n".format(
                            col, str(consumers_to_fetch)
                            ))
                        for var in consumers_to_fetch:
                            if var + '_of' in table.columns:
                                consumers_fetched.append(var + '_of')
                            else:
                                consumers_fetched.append(var)
                    elif set(consumers_to_fetch) <= set(simu_aggr_tables.columns).union(erf_menage.columns):
                        log.info(
                            "Variables which need {} to be computed (some missing picked in erf):\n {} \n".format(
                                col,
                                str(consumers_to_fetch)
                                )
                            )
                        for var in consumers_to_fetch:
                            if var in simu_aggr_tables.columns:
                                if var + '_of' in table.columns:
                                    consumers_fetched.append(var + '_of')
                            elif var + '_erf' in table.columns:
                                    consumers_fetched.append(var + '_erf')
                            else:
                                consumers_fetched.append(var)
                    else:
                        log.info(
                            "Variables which need {} to be computed (some missing):\n {} \n".format(
                                (col, str(consumers_to_fetch))
                                )
                            )
                        for var in consumers_to_fetch:

                            if var in simu_aggr_tables.columns:
                                if var + '_of' in table.columns:
                                    consumers_fetched.append(var + '_of')
                            elif var in erf_menage.columns:
                                if var + '_erf' in table.columns:
                                    consumers_fetched.append(var + '_erf')

                    print table[[col] + consumers_fetched][0:fov]
                    print "\n"
                    del consumers_to_fetch, consumers_fetched

                '''
                For the parents
                '''
                def iter_on_parents(varcol):
                    print varcol.name
                    parents = []
                    column_name = varcol.name
                    holder = simulation.get_or_new_holder(column_name)
                    formula = holder.real_formula
                    if formula is not None:
                        parents = [column_by_name[clean(parameter)] for parameter in formula.parameters]
                    log.info("Variables the column {} depends on :\n {} \n".format(
                        varcol.name, str([parent.name for parent in parents])))

                    if not parents or varcol.name in already_met:
                        return

                    else:
                        of_menage_columns_name = []
                        erf_menage_columns_name = []
                        indvidual_columns_name = []

                        for column in parents:
                            column_name = column.name

                            if column_name in simu_aggr_tables.columns:
                                of_menage_columns_name.append(column_name)
                            if column_name in erf_menage.columns:
                                erf_menage_columns_name.append(column_name)
                            else:
                                indvidual_columns_name.append(column_name)

                        menage_column_fetched = list(
                            set(of_menage_columns_name).intersection(
                                set(of_menage_columns_name)
                                )
                            )
                        temp = table[['idmen'] + menage_column_fetched][0:fov]
                        debug_data_frame_by_entity['menage'] = debug_data_frame_by_entity['menage'].merge(
                            temp,
                            how = 'inner',
                            on = 'idmen'
                            )


                            #print temp.to_string(), "\n"
#                        if varcol._option != {} and not set(varcol._option.keys()) < set(options_met):
#                            vars_to_fetch = list(set(varcol._option.keys())-set(options_met))
#                            #print "and the options to current variable %s for the id's with strongest difference :\n %s \n" %(varcol.name, varcol._option.keys())
#                            liste = [i for i in range(0,fov)]
#                            liste = map(lambda x: table['idmen'].iloc[x], liste)
#                            temp = simu_nonaggr_tables[['idmen', 'quimen','noindiv']
#                                                      + vars_to_fetch][simu_nonaggr_tables['idmen'].isin(table['idmen'][0:fov])]
#
#                            temp_sorted = temp[temp['idmen'] == liste[0]]
#                            for i in xrange(1,fov):
#                                temp_sorted = temp_sorted.append(temp[temp['idmen'] == liste[i]])
#                            if debug_data_frame_by_entity['individus'] is None:
#                                debug_data_frame_by_entity['individus'] = temp_sorted
#                                debug_data_frame_by_entity['individus'] = debug_data_frame_by_entity['individus'].merge(erf_eec_indivi, on = 'noindiv', how = 'outer')
#                            else:
#                                debug_data_frame_by_entity['individus'] = debug_data_frame_by_entity['individus'].merge(temp_sorted, on = ['noindiv','idmen','quimen'], how = 'outer')
#    #                         temp_sorted.set_index(['idmen',  'quimen'], drop = True, inplace = True) # If we do that
#                            del temp, temp_sorted


                        already_met.append(varcol.name)
#                        options_met.extend(varcol._option.keys())
                        for var in parents:
                            iter_on_parents(var)

                iter_on_parents(varcol)
                # We merge the aggregate table with the option table ( for each individual in entity )
#                debug_data_frame_by_entity['menage'] = debug_data_frame_by_entity['menage'].merge(debug_data_frame_by_entity['individus'],
#                                                           how = 'left',
#                                                            on = 'idmen',
#                                                             suffixes = ('(agg)', '(ind)'))

                # Reshaping the table to group by descending error on col, common entities
                debug_data_frame_by_entity['menage'].sort(columns = ['af', 'quimen'], ascending = [False, True], inplace = True)
                debug_data_frame_by_entity['menage'] = debug_data_frame_by_entity['menage'].groupby(['idmen', 'quimen'], sort = False).sum()
                print "Table of values for {} dependencies : \n".format(col)
                print debug_data_frame_by_entity['menage'].to_string()
                del debug_data_frame_by_entity['menage'], debug_data_frame_by_entity['individus']



if __name__ == '__main__':

    import sys
    from openfisca_plugin_aggregates.tests.test_aggregates import create_survey_scenario
    logging.basicConfig(level = logging.INFO, stream = sys.stdout)

    restart = True
#    survey = 'survey.h5'
#    save_path = os.path.join(model.DATA_DIR, 'erf')
#    saved_simulation_filename = os.path.join(save_path, 'debugger_' + survey[:-3])

    if restart:
        year = 2006
        survey_scenario = create_survey_scenario(year)
        survey_scenario.simulation = survey_scenario.new_simulation()

    debugger = Debugger()
    debugger.set_survey_scenario(name = 'debug', survey_scenario = survey_scenario)
    debugger.set_variable('af')
#    debugger.show_aggregates()
    debugger.preproc()
    debugger.describe_discrepancies(descending = False)

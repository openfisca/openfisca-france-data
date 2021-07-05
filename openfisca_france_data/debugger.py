#! /usr/bin/env python
import logging


import numpy
from pandas import merge, concat, DataFrame


from openfisca_france_data.erfs.input_data_builder.base import (
    year_specific_by_generic_data_frame_name)
from openfisca_france_data.utils import simulation_results_as_data_frame
from openfisca_france_data.erf import get_erf2of, get_of2erf
from openfisca_plugin_aggregates.aggregates import Aggregates
from openfisca_survey_manager.statshelpers import mark_weighted_percentiles as mwp
from openfisca_survey_manager.survey_collections import SurveyCollection


from openfisca_parsers import input_variables_extractors

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
        assert survey_scenario is not None
        self.survey_scenario = survey_scenario
        self.variables = self.survey_scenario.simulation.tax_benefit_system.variables
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

        variables = self.variables
        temp = (build_erf_aggregates(variables=[variable], year= self.survey_scenario.year))
        selection = openfisca_aggregates.aggr_frame["Mesure"] == variables[variable].label
        print(openfisca_aggregates.aggr_frame[selection])
        print(temp)
        # TODO: clean this
        return

    def extract(self, data_frame, entities = "men"):
        variables = self.variables
        filtered_data_frame_columns = list(set(variables.keys()).intersection(set(data_frame.columns)))
        extracted_columns = [column_name for column_name in filtered_data_frame_columns
                             if variables[column_name].entity in entities]
        extracted_columns = list(set(extracted_columns).union(set(['idmen'])))
        return data_frame[extracted_columns].copy()

    def get_all_parameters(self, column_list):
        global x
        print([column.name for column in column_list])
        x = x + 1
        if x == 20:
            boum
        variables = self.variables
        tax_benefit_system = self.survey_scenario.simulation.tax_benefit_system

        extractor = input_variables_extractors.setup(tax_benefit_system)

        if len(column_list) == 0:
            return []
        else:
            column_name = column_list[0].name
            print(column_name)
            if extractor.get_input_variables(variables[column_name]) is None:
                return column_list
            else:
                first_column = [column_list[0]]
                input_columns = self.get_all_parameters([
                    variables[clean(parameter)]
                    for parameter in list(extractor.get_input_variables(variables[column_name]))
                    ])
                other_columns = list(
                    set(self.get_all_parameters(column_list[1:])) - set(first_column + input_columns)
                    )
                print('input_variables: ', [column.name for column in input_columns])

                print('new_variables: ', [column.name for column in other_columns])

                new_column_list = first_column + input_columns + other_columns
                print('final list: ', [column.name for column in new_column_list])
                return new_column_list

    def build_columns_to_fetch(self):
        variables = self.variables
#        parameters_column = self.get_all_parameters([variables.get(x) for x in [self.variable]])
#        parameters = [x.name for x in parameters_column]
        parameters = [self.variable]
        # We want to get all parameters and consumers that we're going to encounter
#        consumers = []
#        for variable in [self.variable]:
#            column = variables.get(variable)
#            consumers = list(set(consumers).union(set(column.consumers)))
#        column_names = list(set(parameters).union(set(consumers)))

        # self.columns_to_fetch = column_names
        # self.variable_consumers = list(set(consumers))
        self.variable_parameters = list(set(parameters))
        self.columns_to_fetch = list(set(parameters))

    def build_openfisca_data_frames(self):
        column_names = self.columns_to_fetch
        for column in column_names:
            assert column in survey_scenario.tax_benefit_system.variables.keys()
        data_frame_by_entity_key_plural = survey_scenario.create_data_frame_by_entity(
            variables = column_names + ['idmen_original'],
            indices = True,
            roles = True,
            )
        self.data_frame_by_entity_key_plural = data_frame_by_entity_key_plural

        projected = self.project_on(data_frame_by_entity_key_plural = data_frame_by_entity_key_plural)
        idmen_original_by_idmen = dict(
            zip(
                data_frame_by_entity_key_plural['menages'].index.values,
                data_frame_by_entity_key_plural['menages']["idmen_original"].values
                )
            )
        self.idmen_original_by_idmen = idmen_original_by_idmen

        idmen_by_idmen_original = dict(
            zip(
                data_frame_by_entity_key_plural['menages']["idmen_original"].values,
                data_frame_by_entity_key_plural['menages'].index.values,
                )
            )
        self.idmen_by_idmen_original = idmen_by_idmen_original

        data_frame_by_entity_key_plural['menages'] = projected.rename(
            columns = {"idmen_original": "idmen"})
        data_frame_by_entity_key_plural['individus'].replace(
            {'idmen': idmen_original_by_idmen}, inplace = True)
        self.data_frame_by_entity_key_plural = data_frame_by_entity_key_plural

    def project_on(self, receiving_entity_key_plural = 'menages', data_frame_by_entity_key_plural = None):
        tax_benefit_system = self.survey_scenario.tax_benefit_system
        assert data_frame_by_entity_key_plural is not None
        assert receiving_entity_key_plural is not tax_benefit_system.person_key_plural

        entity_data_frame = data_frame_by_entity_key_plural[receiving_entity_key_plural]
        person_data_frame = data_frame_by_entity_key_plural[tax_benefit_system.person_key_plural]

        entity_keys_plural = list(
            set(tax_benefit_system.entity_class_by_key_plural.keys()).difference(set(
                [tax_benefit_system.person_key_plural, receiving_entity_key_plural]
                ))
            )

        for entity_key_plural in entity_keys_plural:
            entity = tax_benefit_system.entity_class_by_key_plural[entity_key_plural]
            # Getting only heads of other entities prenent in the projected on entity
            boolean_index = person_data_frame[entity.role_for_person_variable_name] == 0  # Heads
            index_entity = person_data_frame.loc[boolean_index, entity.index_for_person_variable_name].values  # Ent.
            for column_name, column_series in self.data_frame_by_entity_key_plural[entity_key_plural].items():
                person_data_frame.loc[boolean_index, column_name] \
                    = column_series.iloc[index_entity].values
                person_data_frame[column_name].fillna(0)

        receiving_entity = tax_benefit_system.entity_class_by_key_plural[receiving_entity_key_plural]
        grouped_data_frame = person_data_frame.groupby(by = receiving_entity.index_for_person_variable_name).agg(sum)
        grouped_data_frame.drop(receiving_entity.role_for_person_variable_name, axis = 1, inplace = True)
        data_frame = concat([entity_data_frame, grouped_data_frame], axis = 1)

        assert data_frame.notnull().all().all()
        return data_frame

    def build_erf_data_frames(self):
        # TODO: remove this
        self.columns_to_fetch = ['af']
        variables = self.columns_to_fetch
        erf_survey_collection = SurveyCollection.load(
            collection = "erfs", config_files_directory = config_files_directory)
        erf_survey = erf_survey_collection.get_survey("erfs_{}".format(year))
        year_specific_by_generic = year_specific_by_generic_data_frame_name(year)
        generic_by_year_specific = dict(zip(year_specific_by_generic.values(), year_specific_by_generic.keys()))

        erf_variables = list(set(variables + ["ident", "wprm", "quelfic", "noi"]))
        of2erf = get_of2erf()
        for index, variable in enumerate(erf_variables):
            if variable in of2erf:
                erf_variables[index] = of2erf[variable]
        data_frame_by_table = dict(eec_indivi = None, erf_indivi = None, erf_menage = None)
        erf_variables_by_generic_table = dict(eec_indivi = [], erf_indivi = [], erf_menage = [])

        year_specific_tables_by_erf_variable = dict(
            [
                (
                    erf_variable,
                    set(
                        erf_survey.find_tables(variable = erf_variable)
                        ).intersection(
                        set([year_specific_by_generic[key] for key in erf_variables_by_generic_table.keys()])
                        )
                    ) for erf_variable in erf_variables
                ]
            )
        for variable, year_specific_tables in year_specific_tables_by_erf_variable.items():
            if len(year_specific_tables) < 1:
                log.info("No tables are present for variable {}".format(variable))
                continue
            else:
                log.info("Variable {} is present in multiple tables : {}".format(variable, year_specific_tables))
                for table in year_specific_tables:
                    log.info("Variable {} is retrieved from table {}".format(variable, table))
                    erf_variables_by_generic_table[generic_by_year_specific[table]].append(variable)

        erf2of = get_erf2of()

        for table, erf_variables in erf_variables_by_generic_table.items():
            if erf_variables:
                data_frame_by_table[table] = erf_survey.get_values(
                    variables = erf_variables, table = year_specific_by_generic[table]
                    )
                data_frame_by_table[table].rename(columns = erf2of, inplace = True)
                data_frame_by_table[table].rename(columns = {'ident': 'idmen'}, inplace = True)

        assert not data_frame_by_table["erf_menage"].duplicated().any(), "Duplicated idmen in erf_menage"
        self.erf_data_frame_by_entity_key_plural = dict(
            menages = data_frame_by_table["erf_menage"],
            individus = data_frame_by_table["erf_indivi"].merge(data_frame_by_table["eec_indivi"])
            )
    # TODO: fichier foyer

    def get_major_differences(self):
        variable = self.variable

        of_menages_data_frame = self.data_frame_by_entity_key_plural['menages']
        erf_menages_data_frame = self.erf_data_frame_by_entity_key_plural['menages']

        merged_menage_data_frame = merge(
            erf_menages_data_frame[[variable, 'idmen']],
            of_menages_data_frame[[variable, 'idmen']],
            on = 'idmen',
            how = 'inner',
            suffixes = ('_erf', '_of')
            )

        log.info('Length of merged_menage_data_frame is {}'.format(len(merged_menage_data_frame)))
        merged_menage_data_frame.set_index('idmen', drop = False, inplace = True)
        table = merged_menage_data_frame[
            numpy.logical_and(
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
                numpy.arange(1, 11), table['wprm_of'],
                2,
                return_quantiles = True
                )
            log.info(sorted(values))
            dec, values = mwp(
                table[variable + "_rel_diff"],
                numpy.arange(1, 101),
                table['wprm_erf'],
                2,
                return_quantiles = True
                )
            log.info(sorted(values)[90:])
            del dec, values
        except Exception:
            log.info('Weighted percentile method did not work for {}'.format(variable + "_rel_diff"))
            pass
        table.sort(columns = variable + "_rel_diff", ascending = False, inplace = True)

        print(table[:10].to_string())
        return table

    def describe_discrepancies(self, fov = 10, consumers = False, parameters = True, descending = True, to_men = False):
        variable = self.variable
        major_differences_data_frame = self.get_major_differences()
        major_differences_data_frame.sort(
            columns = self.variable + "_rel_diff",
            ascending = not descending,
            inplace = True
            )
        debug_data_frame = major_differences_data_frame[0:fov].copy()
        del major_differences_data_frame

        of_menages_data_frame = self.data_frame_by_entity_key_plural['menages']
        of_individus_data_frame = self.data_frame_by_entity_key_plural['individus']
        erf_individus_data_frame = self.erf_data_frame_by_entity_key_plural['individus']
        erf_menages_data_frame = self.erf_data_frame_by_entity_key_plural['menages']
        return debug_data_frame

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

        print(debug_data_frame.to_string())

        debug_data_frame = debug_data_frame.merge(
            self.extract(of_individus_data_frame, entities = entities_ind),
            how = 'inner',
            on = 'idmen',
            )

        debug_data_frame = debug_data_frame.merge(
            erf_individus_data_frame,
            how = 'inner',
            on = 'idmen',
            )

        suffixes = ["_erf", "_of", "_rel_diff", "_ratio"]
        reordered_columns = [variable + suffixe for suffixe in suffixes] \
            + ["idmen", "quimen", "idfam", "quifam", "idfoy", "quifoy"]
        reordered_columns = reordered_columns + list(set(kept_columns) - set(reordered_columns))
        debug_data_frame = debug_data_frame[reordered_columns].copy()
        return debug_data_frame

    def generate_test_case(self):
        entity_class_by_key_plural = self.survey_scenario.tax_benefit_system.entity_class_by_key_plural
        menages_entity = entity_class_by_key_plural['menages']
        idmen_by_idmen_original = self.idmen_by_idmen_original
        idmen_original = self.describe_discrepancies(descending = False)[
            menages_entity.index_for_person_variable_name].iloc[0]
        idmen = idmen_by_idmen_original[idmen_original]
        input_data_frame = self.survey_scenario.input_data_frame
        individus_index = input_data_frame.index[
            input_data_frame[menages_entity.index_for_person_variable_name] == idmen]
        index_by_entity = {
            entity_class_by_key_plural['individus']: individus_index,
            }
        for entity in list(entity_class_by_key_plural.values()):
            if entity.key_plural != 'individus':
                index_by_entity[entity] = input_data_frame.loc[
                    individus_index, entity.index_for_person_variable_name].unique()

        extracted_indices = individus_index
        for entity, entity_index in index_by_entity.items():
            if entity.key_plural in ['menages', 'individus']:
                continue
            extracted_indices = extracted_indices + \
                input_data_frame.index[input_data_frame[entity.index_for_person_variable_name].isin(entity_index)]

        extracted_input_data_frame = input_data_frame.loc[extracted_indices]
        return extracted_input_data_frame


if __name__ == '__main__':
    import sys
    from openfisca_plugin_aggregates.tests.test_aggregates import create_survey_scenario
    logging.basicConfig(level = logging.INFO, stream = sys.stdout)
    restart = True
    if restart:
        year = 2009
        survey_scenario = create_survey_scenario(year)
        survey_scenario.simulation = survey_scenario.new_simulation()

    debugger = Debugger()
    debugger.set_survey_scenario(survey_scenario = survey_scenario)
    debugger.set_variable('af')
    debugger.build_columns_to_fetch()
    debugger.build_openfisca_data_frames()
    debugger.build_erf_data_frames()

    # df_menage = debugger.data_frame_by_entity_key_plural['menages']
    # df_famille = debugger.data_frame_by_entity_key_plural['familles']
    # df_individus = debugger.data_frame_by_entity_key_plural['individus']

    # df = debugger.get_major_differences()

    # debugger.show_aggregates()
    df = debugger.describe_discrepancies(descending = False)
    df = debugger.generate_test_case()

    boum
    entity_class_by_key_plural = debugger.survey_scenario.tax_benefit_system.entity_class_by_key_plural
    menages_entity = entity_class_by_key_plural['menages']

    idmen = debugger.describe_discrepancies(descending = False)[menages_entity.index_for_person_variable_name].iloc[0]

    input_data_frame = debugger.survey_scenario.input_data_frame

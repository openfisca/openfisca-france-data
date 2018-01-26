# -*- coding: utf-8 -*-


import os

from pandas import DataFrame, concat
from openfisca_core.model_api import *


def check_consistency(table_simu, dataframe, corrige = True):
    '''
    Studies dataframe columns as described in a simulation table columns attribute, and should eventually
    TODO table_simu -> input_table
    Parameters
    ----------
    table_simu : datatable object, typically output table of a simulation
    dataframe : dataframe object that we want to compare
    corrige : if corrige is True, the function tries to correct errors in datatable by passing default values
    '''
    # check_inputs_enumcols(simulation):
    # TODO: eventually should be a method of SurveySimulation specific for france

    is_ok = True
    message = "\n"
    missing_variables = []
    present_variables = []
    count = 0

    from .data.erf.build_survey.utilitaries import control
    print 'Controlling simulation input_table'
    control(table_simu.table, verbose = True)

    # First : study of the datatable / the specification of columns given by table_simu
    for var, varcol in table_simu.variables.iteritems():
        try:
            serie = dataframe[var]
            simu_serie = table_simu.table[var]
            present_variables.append(var)
            # First checks for all if there is any missing data
            if serie.isnull().any() or simu_serie.isnull().any():
                is_ok = False
                if serie.isnull().any():
                    message += "Some missing values in dataframe column %s, \n" % var
                if simu_serie.isnull().any():
                    message += 'Some missing values in input_table column %s \n' % var
                cnt = len(set(simu_serie.isnull())) - len(set(serie.isnull()))
                if 0 < cnt:
                    message += "Warning : %s More NA's in simulation than in original dataframe for %s \n" % (
                        str(cnt), var)

                if corrige:
                    try:
                        message += "Filling NA's with default values for %s... \n" % var
                        serie[serie.isnull()] = varcol.default
                        message += "Done \n"
                    except:
                        message += " Cannot fill NA for column %s, maybe _.default doesn't exist \n" % var

            if not corrige:  # On ne modifie pas la série donc on peut l'amputer, elle n'est pas en return
                serie = serie[serie.notnull()]

            # Then checks if all values are of specified datatype
            # verify type, force type

            if varcol.value_type == Enum:
                try:
                    if set(serie.unique()) > set(sorted(varcol.possible_values._nums.values())):
                        message += "Some variables out of range for Enum variable %s : \n" % var
                        message += str(set(serie.unique()) - set(sorted(varcol.possible_values._nums.values()))) + "\n"
                        # print varcol.enum._nums
                        # print sorted(serie.unique()), "\n"
                        is_ok = False

                except:
                    is_ok = False
                    message += "Error : no _num attribute for EnumCol.enum %s \n" % var
                    # print varcol.enum
                    # print sorted(serie.unique()), "\n"
                try:
                    varcol.enum._vars

                except:
                    is_ok = False
                    message += "Error : no _var attribute for EnumCol.enum %s \n" % var
                    # print varcol.enum
                    # print sorted(serie.unique())
                    # print "\n"
                try:
                    n = varcol.enum._count
                    if n < len(set(serie.unique())):
                        message += "More types of enum than expected : %s ( expected : %s) \n" % (
                            str(set(serie.unique())), str(n))
                except:
                    message += "Error : no _count attribute for EnumCol.enum %s \n" % var
                try:
                    varcol.enum
                except:
                    is_ok = False
                    message += "Error : not enum attribute for EnumCol %s ! \n" % var
                    # Never happening, enum attribute is initialized to None at least

            if varcol.value_type == int:
                if serie.dtype not in ('int', 'int16', 'int32', 'int64'):
                    is_ok = False
                    # print serie[serie.notnull()]
                    message += "Some values in column %s are not integer as wanted: %s \n" % (var, serie.dtype)
                    stash = []
                    for v in serie:
                        if not isinstance(v, int):
                            stash.append(v)
                    message += str(list(set(stash))) + " \n"
                    if corrige:
                        message += "Warning, forcing type integer for %s..." % var
                        try:
                            serie = serie.astype(varcol.dtype)
                            message += "Done \n"
                        except:
                            message += "sorry, cannot force type.\n"
                else:
                    message += "Values for %s are in range [%s,%s]\n" % (var, str(serie.min()), str(serie.max()))

            if varcol.value_type == bool:
                if serie.dtype != 'bool':
                    is_ok = False
                    # print serie[serie.notnull()]
                    message += "Some values in column %s are not boolean as wanted \n" % var
                    if corrige:
                        message += "Warning, forcing type boolean for %s..." % var
                        try:
                            serie = serie.astype(varcol.dtype)
                            message += "Done \n"
                        except:
                            message += "sorry, cannot force type.\n"

            # There isn't a specific type of variable for age anymore
            # if isinstance(varcol, AgeCol):
            #     if serie.dtype not in ('int', 'int16', 'int32', 'int64'):
            #         is_ok = False
            #         message += "Age variable %s not of type int: \n"
            #         stash = list(set(serie.value) - set(range(serie.min(), serie.max() + 1)))
            #         message += str(stash) + "\n"
            #         message += "Total frequency for non-integers for %s is %s \n" % (var, str(len(stash)))
            #         if corrige:
            #             pass

            #     if not serie.isin(range(-1, 156)).all():  # Pas plus vieux que 100 ans ?
            #         is_ok = False
            #         # print serie[serie.notnull()]
            #         message += "Age variable %s not in wanted range: \n" % var
            #         stash = list(set(serie.unique()) - set(range(-1, 156)))
            #         message += str(stash) + "\n"
            #         message += "Total frequency of outranges for %s is %s \n" % (var, str(len(stash)))
            #         del stash
            #         if corrige:
            #             try:
            #                 message += "Fixing the outranges for %s... " % var
            #                 tmp = serie[serie.isin(range(-1, 156))]
            #                 serie[~(serie.isin(range(-1, 156)))] = tmp.median()
            #                 message += "Done \n"
            #                 del tmp
            #             except:
            #                 message += "sorry, cannot fix outranges.\n"

            if varcol.value_type == float:
                if serie.dtype not in ('float', 'float32', 'float64', 'float16'):
                    is_ok = False
                    message += "Some values in column %s are not float as wanted \n" % var
                    stash = list(set(serie.unique()) - set(range(serie.min(), serie.max() + 1)))
                    message += str(stash) + "\n"
                    message += "Total frequency for non-integers for %s is %s \n" % (var, str(len(stash)))

            if varcol.value_type == date:
                if serie.dtype != 'np.datetime64':
                    is_ok = False
                    # print serie[serie.notnull()]
                    message += "Some values in column %s are not of type date as wanted \n" % var

            if corrige:
                dataframe[var] = serie
            count += 1
            del serie, varcol
        except:
            is_ok = False
            missing_variables.append(var)
            # message = "Oh no ! Something went wrong in the tests. You may have coded like a noob"

    # TODO : Then, comparaison between datatable and table_simu.table ?

    if len(missing_variables) > 0:
        message += "Some variables were not present in the datatable or caused an error:\n" \
            + str(sorted(missing_variables)) + "\n"
        message += "Variables present in both tables :\n" + str(sorted(present_variables)) + "\n"
    else:
        message += "All variables were present in the datatable and were handled without error \n"

    if is_ok:
        print "All is well. Sleep mode activated."
    else:
        print message

    if corrige:
        return dataframe
    else:
        return

    # NotImplementedError


def dump_simulation_results_data_frame(survey_scenario, collection = None):
    assert collection is not None
    year = survey_scenario.year
    data_frame_by_entity = get_calculated_data_frame_by_entity(survey_scenario)
    openfisca_survey_collection = SurveyCollection.load(collection = "openfisca")
    output_data_directory = openfisca_survey_collection.config.get('data', 'output_directory')
    survey_name = "openfisca_data_{}".format(year)
    for entity, data_frame in data_frame_by_entity.iteritems():
        print entity
        table = entity
        hdf5_file_path = os.path.join(
            os.path.dirname(output_data_directory),
            "{}{}".format(survey_name, ".h5"),
            )
        survey = Survey(
            name = survey_name,
            hdf5_file_path = hdf5_file_path,
            )
        survey.insert_table(name = table)
        survey.fill_hdf(table, data_frame)
        openfisca_survey_collection.surveys[survey_name] = survey
        openfisca_survey_collection.dump(collection = "openfisca")


def get_data_frame(columns_name, survey_scenario, load_first = False, collection = None):
    year = survey_scenario.year
    if survey_scenario.simulation is None:
        survey_scenario.new_simulation()
    simulation = survey_scenario.simulation
    if load_first:
        assert collection is not None
        entities = [simulation.tax_benefit_system.variables[column_name].entity for column_name in columns_name]
        assert len(set(entities)) == 1
        # entity_symbol = entities[0]
        for entity_key_plural in simulation.entity_by_key_plural:
            if columns_name[0] in simulation.entity_by_key_plural[entity_key_plural].variables:
                entity = entity_key_plural
                break
        openfisca_survey_collection = SurveyCollection.load(collection = collection)
        survey_name = "openfisca_data_{}".format(year)
        survey = openfisca_survey_collection.surveys[survey_name]
        table = entity
        data_frame = survey.get_values(variables = columns_name, table = table)
    else:
        data_frame = DataFrame(dict([(column_name, simulation.calculate_add(column_name)) for column_name in columns_name]))
    return data_frame


def get_calculated_data_frame_by_entity(survey_scenario = None):
    if survey_scenario.simulation is None:
        survey_scenario.new_simulation()
    simulation = survey_scenario.simulation
    data_frame_by_entity = dict()
    for entity in simulation.entity_by_key_plural.itervalues():
        variables_name = entity.variables.keys()
        data_frame_by_entity[entity] = get_data_frame(variables_name, survey_scenario)
    return data_frame_by_entity


def simulation_results_as_data_frame(survey_scenario = None, column_names = None, entity = None, force_sum = False):
    assert survey_scenario is not None
    assert force_sum is False or entity != 'ind', "force_sum cannot be True when entity is 'ind'"
    simulation = survey_scenario.simulation
    variables = simulation.tax_benefit_system.variables
    assert set(column_names) <= set(variables), \
        "Variables {} do not exist".format(list(set(column_names) - set(variables)))
    entities = list(set([variables[column_name].entity for column_name in column_names] + [entity]))

    if force_sum is False and entity != 'ind':
        assert len(entities) == 1
        data_frame = get_data_frame(column_names, survey_scenario, load_first = False, collection = None)
    else:
        if 'ind' in entities:
            entities.remove('ind')
        if entity is None and len(entities) == 1:
            entity = entities[0]

        data_frame_by_entity = dict()
        individual_column_names = [
            column_name for column_name in column_names if variables[column_name].entity == 'ind'
            ]
        for selected_entity in entities:
            id_variables_column_names = ["id{}".format(selected_entity), "qui{}".format(selected_entity)]
            individual_column_names.extend(id_variables_column_names)
            selected_entity_column_names = [
                column_name for column_name in column_names if variables[column_name].entity == selected_entity
                ]
            data_frame_by_entity[selected_entity] = get_data_frame(
                selected_entity_column_names,
                survey_scenario,
                load_first = False,
                collection = None
                )
            data_frame_by_entity[selected_entity]["id{}".format(entity)] = data_frame_by_entity[selected_entity].index

        individual_data_frame = get_data_frame(
            individual_column_names,
            survey_scenario,
            load_first = False,
            collection = None
            )

        for other_entity in entities:
            if other_entity != entity:
                boolean_index = individual_data_frame["qui{}".format(other_entity)] == 0
                index_other_entity = individual_data_frame.loc[boolean_index, "id{}".format(other_entity)].values
                for column_name, column_series in data_frame_by_entity[other_entity].iteritems():
                    individual_data_frame.loc[boolean_index, column_name] \
                        = column_series.loc[index_other_entity].values
                    individual_data_frame[column_name].fillna(0)

        if entity == 'ind' and force_sum is False:
            return individual_data_frame

        entity_column_names = [
            column_name for column_name in column_names if variables[column_name].entity == entity
            ]
        entity_data_frame = get_data_frame(
            entity_column_names,
            survey_scenario,
            load_first = False,
            collection = None
            )

        grouped_data_frame = individual_data_frame.groupby(by = "id{}".format(entity)).agg(sum)
        grouped_data_frame.drop("qui{}".format(entity), axis = 1, inplace = True)
        data_frame = concat([entity_data_frame, grouped_data_frame], axis = 1)

    return data_frame


if __name__ == '__main__':
    import logging
    log = logging.getLogger(__name__)
    import sys
    logging.basicConfig(level = logging.INFO, stream = sys.stdout)

    from openfisca_survey_manager.surveys import Survey, SurveyCollection
    from openfisca_plugin_aggregates.tests.test_aggregates import create_survey_scenario

    year = 2006
    survey_scenario = create_survey_scenario(year)
#    dump_simulation_results_data_frame(survey_scenario, collection = "openfisca")

    df = get_data_frame(["af"], survey_scenario, load_first = True, collection = "openfisca")
    print df

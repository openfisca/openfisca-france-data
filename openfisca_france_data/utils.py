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

import os

from pandas import DataFrame, concat


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
        entities = [simulation.tax_benefit_system.column_by_name[column_name].entity for column_name in columns_name]
        assert len(set(entities)) == 1
        entity_symbol = entities[0]
        for entity_key_plural in simulation.entity_by_key_plural:
            if columns_name[0] in simulation.entity_by_key_plural[entity_key_plural].column_by_name:
                entity = entity_key_plural
                break
        openfisca_survey_collection = SurveyCollection.load(collection = collection)
        survey_name = "openfisca_data_{}".format(year)
        survey = openfisca_survey_collection.surveys[survey_name]
        table = entity
        data_frame = survey.get_values(variables = columns_name, table = table)
    else:
        data_frame = DataFrame(dict([(column_name, simulation.calculate(column_name)) for column_name in columns_name]))
    return data_frame


def get_calculated_data_frame_by_entity(survey_scenario = None):
    if survey_scenario.simulation is None:
        survey_scenario.new_simulation()
    simulation = survey_scenario.simulation
    data_frame_by_entity = dict()
    for entity in simulation.tax_benefit_system.entities:
        columns = simulation.entity_by_key_plural[entity].column_by_name.keys()
        data_frame_by_entity[entity] = get_data_frame(columns, survey_scenario)
    return data_frame_by_entity


def simulation_results_as_data_frame(survey_scenario = None, column_names = None, entity = None, force_sum = False):
    assert survey_scenario is not None
    assert force_sum is False or entity != 'ind', "force_sum cannot be tru when entity is 'ind'"
    simulation = survey_scenario.simulation
    column_by_name = simulation.tax_benefit_system.column_by_name
    assert set(column_names) <= set(column_by_name), \
        "Variables {} do not exist".format(list(set(column_names) - set(column_by_name)))
    entities = list(set([column_by_name[column_name].entity for column_name in column_names] + [entity]))

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
            column_name for column_name in column_names if column_by_name[column_name].entity == 'ind'
            ]
        for selected_entity in entities:
            id_variables_column_names = ["id{}".format(selected_entity), "qui{}".format(selected_entity)]
            individual_column_names.extend(id_variables_column_names)
            selected_entity_column_names = [
                column_name for column_name in column_names if column_by_name[column_name].entity == selected_entity
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
                    individual_data_frame.loc[boolean_index, column_name] = column_series.iloc[index_other_entity].values
                    individual_data_frame[column_name].fillna(0)

        if entity == 'ind' and force_sum is False:
            return individual_data_frame

        entity_column_names = [
            column_name for column_name in column_names if column_by_name[column_name].entity == entity
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

    from openfisca_france_data.surveys import Survey, SurveyCollection
    from openfisca_plugin_aggregates.tests.test_aggregates import create_survey_scenario

    year = 2006
    survey_scenario = create_survey_scenario(year)
#    dump_simulation_results_data_frame(survey_scenario, collection = "openfisca")

    df = get_data_frame(["af"], survey_scenario, load_first = True, collection = "openfisca")
    print df
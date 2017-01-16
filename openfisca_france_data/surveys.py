# -*- coding: utf-8 -*-


import logging
import numpy as np
import pandas as pd


from openfisca_core import periods, simulations, taxbenefitsystems

from openfisca_france_data.tests import base
from openfisca_survey_manager.survey_collections import SurveyCollection
from openfisca_survey_manager.scenarios import AbstractSurveyScenario


log = logging.getLogger(__name__)


class AbstractErfsSurveyScenario(AbstractSurveyScenario):
    filtering_variable_by_entity = dict(
        individu = 'champm_individus',
        foyer_fiscal = 'champm_foyers_fiscaux',
        famille = 'champm_familles',
        )
    filtering_variable_by_entity['menage'] = 'champm'

    # def cleanup_input_data_frame(data_frame, filter_entity = None, filter_index = None, simulation = None):
    #     from openfisca_france_data.utils import id_formatter
    #     person_index = dict()
    #     id_variables = [
    #         entity.index_for_person_variable_name for entity in simulation.entity_by_key_singular.values()
    #         if not entity.is_persons_entity]

    #     if filter_entity.is_persons_entity:
    #         selection = data_frame.index.isin(filter_index)
    #         person_index[filter_entity.key_plural] = data_frame.index[selection].copy()
    #     else:
    #         selection = data_frame[filter_entity.index_for_person_variable_name].isin(filter_index)
    #         id_variables.remove(filter_entity.index_for_person_variable_name)
    #         person_index[filter_entity.key_plural] = data_frame.index[selection].copy()

    #     final_selection_index = person_index[filter_entity.index_for_person_variable_name]  # initialisation

    #     for entity in simulation.entity_by_key_singular.values():
    #         if entity.index_for_person_variable_name in id_variables:
    #             other_entity_index = \
    #                 data_frame[entity.index_for_person_variable_name][person_index[filter_entity.key_plural]].unique()
    #             person_index[entity.key_plural] = \
    #                 data_frame.index[data_frame[entity.index_for_person_variable_name].isin(other_entity_index)].copy()
    #             final_selection_index += person_index[entity.key_plural]

    #     data_frame = data_frame.iloc[final_selection_index].copy().reset_index()
    #     for entity in simulation.entity_by_key_singular.values():
    #         data_frame = id_formatter(data_frame, entity.index_for_person_variable_name)
    #     return data_frame

    @classmethod
    def build_input_data_from_test_case(cls, tax_benefit_system, test_case_scenario, year):
        for axe in test_case_scenario['axes'][0]:
            axe['name'] = 'salaire_imposable_pour_inversion'
        simulation = tax_benefit_system.new_scenario().init_single_entity(**test_case_scenario).new_simulation()
        array_by_variable = dict()
        period = periods.period("{}".format(year))

        for variable in cls.default_used_as_input_variables:
            array_by_variable[variable] = simulation.calculate_add(variable, period = period)

        for ident in ['idmen', 'idfoy', 'idfam']:
            array_by_variable[ident] = range(axe['count'])

        input_data_frame = pd.DataFrame(array_by_variable)

        for qui in ['quimen', 'quifoy', 'quifam']:
            input_data_frame[qui] = 0

        return input_data_frame

    @classmethod
    def create(cls, calibration_kwargs = None, data_year = None, inflation_kwargs = None, rebuild_input_data = False,
            reference_tax_benefit_system = None, reform = None, reform_key = None, tax_benefit_system = None,
            test_case_scenario = None, year = None):

        assert year is not None
        assert not(
            (reform is not None) and (reform_key is not None)
            )

        if calibration_kwargs is not None:
            assert set(calibration_kwargs.keys()).issubset(set(
                ['target_margins_by_variable', 'parameters', 'total_population']))

        if data_year is None:
            data_year = year

        if inflation_kwargs is not None:
            assert set(inflation_kwargs.keys()).issubset(set(['inflator_by_variable', 'target_by_variable']))

        if reform_key is not None:
            reform = base.get_cached_reform(
                reform_key = reform_key,
                tax_benefit_system = reference_tax_benefit_system or base.france_data_tax_benefit_system,
                )

        if reform is None:
            if reference_tax_benefit_system is None:
                reference_tax_benefit_system = base.france_data_tax_benefit_system
        else:
            tax_benefit_system = reform

        if rebuild_input_data:
            cls.build_input_data(year = data_year)

        if test_case_scenario is not None:
            assert rebuild_input_data is False
            input_data_frame = cls.build_input_data_from_test_case(
                tax_benefit_system = tax_benefit_system,
                test_case_scenario = test_case_scenario,
                year = year,
                )
        else:
            openfisca_survey_collection = SurveyCollection.load(collection = cls.collection)
            openfisca_survey = openfisca_survey_collection.get_survey("{}_{}".format(
                cls.input_data_survey_prefix, data_year))
            input_data_frame = openfisca_survey.get_values(table = "input").reset_index(drop = True)
            input_data_frame['salaire_imposable_pour_inversion'] = input_data_frame.salaire_imposable
            input_data_frame['cotisation_sociale_mode_recouvrement'] = 1
            input_data_frame['salaire_imposable']

        survey_scenario = cls().init_from_data_frame(
            input_data_frame = input_data_frame,
            tax_benefit_system = tax_benefit_system,
            reference_tax_benefit_system = reference_tax_benefit_system,
            year = year,
            )

        survey_scenario.new_simulation()
        if reform or reform_key:
            survey_scenario.new_simulation(reference = True)

        if calibration_kwargs:
            survey_scenario.calibrate(**calibration_kwargs)

        if inflation_kwargs:
            survey_scenario.inflate(**inflation_kwargs)
        #
        return survey_scenario

    def custom_initialize(self):
        for simulation in [self.simulation, self.reference_simulation]:
            if simulation is None:
                continue

            three_year_span_variables = [
                'categorie_salarie',
                'cotisation_sociale_mode_recouvrement',
                'chomage_brut',
                'chomage_imposable',
                'contrat_de_travail',
                'effectif_entreprise',
                'hsup',
                'pensions_alimentaires_percues',
                'retraite_brute',
                'retraite_imposable',
                'salaire_imposable',
                'salaire_imposable_pour_inversion',
                ]
            for offset in [0, -1, -2]:
                for variable_name in three_year_span_variables:
                    holder = simulation.get_or_new_holder(variable_name)
                    holder.set_input(simulation.period.offset(offset), simulation.calculate_add(variable_name))

            simulation.get_or_new_holder('taux_incapacite').set_input(simulation.period, .50)

    def init_from_collection(self, collection = None, reference_tax_benefit_system = None, tax_benefit_system = None,
            used_as_input_variables = None, year = None):

        if used_as_input_variables is None:
            used_as_input_variables = self.default_used_as_input_variables

        if tax_benefit_system is None:
            tax_benefit_system = base.france_data_tax_benefit_system
            reference_tax_benefit_system = None

        variables_mismatch = set(used_as_input_variables).difference(set(input_data_frame.columns))
        if variables_mismatch:
            log.info(
                'The following variables used as input variables are not present in the input data frame: \n {}'.format(
                    variables_mismatch))
            log.info('The following variables are used as input variables: \n {}'.format(used_as_input_variables))
            log.info('The input_data_frame contains the following variables: \n {}'.format(input_data_frame.columns))
        return super(AbstractErfsSurveyScenario, self).init_from_collection(
            collection = collection,
            reference_tax_benefit_system = reference_tax_benefit_system,
            tax_benefit_system = tax_benefit_system,
            used_as_input_variables = used_as_input_variables,
            year = year,
            )

    def init_from_data_frame(self, input_data_frame = None, input_data_frame_by_entity = None,
            reference_tax_benefit_system = None, tax_benefit_system = None, used_as_input_variables = None,
            year = None):

        if used_as_input_variables is None:
            used_as_input_variables = self.default_used_as_input_variables

        if tax_benefit_system is None:
            tax_benefit_system = base.france_data_tax_benefit_system
            reference_tax_benefit_system = None

        variables_mismatch = set(used_as_input_variables).difference(set(input_data_frame.columns))
        if variables_mismatch:
            log.info(
                'The following variables used as input variables are not present in the input data frame: \n {}'.format(
                    variables_mismatch))
            log.info('The following variables are used as input variables: \n {}'.format(used_as_input_variables))
            log.info('The input_data_frame contains the following variables: \n {}'.format(input_data_frame.columns))
        return super(AbstractErfsSurveyScenario, self).init_from_data_frame(
            input_data_frame = input_data_frame,
            input_data_frame_by_entity = input_data_frame_by_entity,
            reference_tax_benefit_system = reference_tax_benefit_system,
            tax_benefit_system = tax_benefit_system,
            used_as_input_variables = used_as_input_variables,
            year = year,
            )

    def initialize_weights(self):
        self.weight_column_name_by_entity['menage'] = 'wprm'
        self.weight_column_name_by_entity['famille'] = 'weight_familles'
        self.weight_column_name_by_entity['foyer_fiscal'] = 'weight_foyers'
        self.weight_column_name_by_entity['individu'] = 'weight_individus'


def new_simulation_from_array_dict(array_dict = None, debug = False, debug_all = False, legislation_json = None,
        tax_benefit_system = None, trace = False, year = None):
    simulation = simulations.Simulation(
        debug = debug,
        debug_all = debug_all,
        legislation_json = legislation_json,
        period = periods.period(year),
        tax_benefit_system = tax_benefit_system,
        trace = trace,
        )

    assert len(set(len(x) for x in array_dict.itervalues() if len(x) != 1)) == 1, 'Arrays do not have the same size'
    global_count = len(array_dict.values()[0])

    for role_var in ['quifam', 'quifoy', 'quimen']:
        if role_var not in array_dict:
            array_dict[role_var] = np.zeros(global_count, dtype = int)

    for id_var in ['idfam', 'idfoy', 'idmen']:
        if id_var not in array_dict:
            array_dict[id_var] = np.arange(global_count, dtype = int)

    column_by_name = tax_benefit_system.column_by_name
    for column_name, array in array_dict.iteritems():
        assert column_name in column_by_name, column_name

    entity_by_key_plural = simulation.entity_by_key_plural

    familles = entity_by_key_plural[u'familles']
    familles.count = familles.step_size = (array_dict['quifam'] == 0).sum()
    foyers_fiscaux = entity_by_key_plural[u'foyers_fiscaux']
    foyers_fiscaux.count = foyers_fiscaux.step_size = (array_dict['quifoy'] == 0).sum()
    individus = entity_by_key_plural[u'individus']
    individus.count = individus.step_size = global_count
    menages = entity_by_key_plural[u'menages']
    menages.count = menages.step_size = (array_dict['quimen'] == 0).sum()

    assert 'idfam' in array_dict.keys()
    assert 'idfoy' in array_dict.keys()
    assert 'idmen' in array_dict.keys()
    assert 'quifam' in array_dict.keys()
    assert 'quifoy' in array_dict.keys()
    assert 'quimen' in array_dict.keys()

    familles.roles_count = array_dict['quifam'].max() + 1
    menages.roles_count = array_dict['quimen'].max() + 1
    foyers_fiscaux.roles_count = array_dict['quifoy'].max() + 1

    for column_name, column_array in array_dict.iteritems():
        holder = simulation.get_or_new_holder(column_name)
        entity = holder.entity
        if entity.is_persons_entity:
            array = column_array
        else:
            array = column_array[array_dict['qui' + entity.symbol].values == 0]
        assert array.size == entity.count, 'Bad size for {}: {} instead of {}'.format(
            column_name,
            array.size,
            entity.count
            )
        holder.array = np.array(array, dtype = holder.column.dtype)

    return simulation

# -*- coding: utf-8 -*-


import logging
import numpy as np


from openfisca_core import periods, simulations, taxbenefitsystems
from openfisca_france_data import france_data_tax_benefit_system
from openfisca_france_data.utils import id_formatter
from openfisca_survey_manager.scenarios import AbstractSurveyScenario


log = logging.getLogger(__name__)


class AbstractErfsSurveyScenario(AbstractSurveyScenario):
    filtering_variable_by_entity_key_plural = dict(
        (entity, "champm_{}".format(entity)) for entity in ['individus', 'foyers_fiscaux', 'familles']
        )
    filtering_variable_by_entity_key_plural['menages'] = 'champm'

    def cleanup_input_data_frame(data_frame, filter_entity = None, filter_index = None, simulation = None):
        person_index = dict()
        id_variables = [
            entity.index_for_person_variable_name for entity in simulation.entity_by_key_singular.values()
            if not entity.is_persons_entity]

        if filter_entity.is_persons_entity:
            selection = data_frame.index.isin(filter_index)
            person_index[filter_entity.key_plural] = data_frame.index[selection].copy()
        else:
            selection = data_frame[filter_entity.index_for_person_variable_name].isin(filter_index)
            id_variables.remove(filter_entity.index_for_person_variable_name)
            person_index[filter_entity.key_plural] = data_frame.index[selection].copy()

        final_selection_index = person_index[filter_entity.index_for_person_variable_name]  # initialisation

        for entity in simulation.entity_by_key_singular.values():
            if entity.index_for_person_variable_name in id_variables:
                other_entity_index = \
                    data_frame[entity.index_for_person_variable_name][person_index[filter_entity.key_plural]].unique()
                person_index[entity.key_plural] = \
                    data_frame.index[data_frame[entity.index_for_person_variable_name].isin(other_entity_index)].copy()
                final_selection_index += person_index[entity.key_plural]

        data_frame = data_frame.iloc[final_selection_index].copy().reset_index()
        for entity in simulation.entity_by_key_singular.values():
            data_frame = id_formatter(data_frame, entity.index_for_person_variable_name)
        return data_frame

    def custom_initialize(self):
        for simulation in [self.simulation, self.reference_simulation]:
            if simulation is None:
                continue
            for offset in [0, -1, -2]:
                for variable_name in ['salaire_imposable', 'chomage_imposable', 'retraite_imposable',
                        'pensions_alimentaires_percues', 'hsup']:
                    holder = simulation.get_or_new_holder(variable_name)
                    holder.set_input(simulation.period.offset(offset), simulation.calculate_add(variable_name))
                    if variable_name == 'salaire_imposable':
                        try:
                            holder = simulation.get_or_new_holder('salaire_imposable_pour_inversion')
                            holder.set_input(simulation.period.offset(offset), simulation.calculate(variable_name))
                            log.info('salaire_imposable_pour_inversion initialized')
                        except taxbenefitsystems.VariableNotFound:
                            log.info('WARNING salaire_imposable_pour_inversion not present and thus not initialized')
                            pass

            simulation.get_or_new_holder('taux_incapacite').set_input(simulation.period, .50)

    def init_from_data_frame(self, input_data_frame = None, input_data_frames_by_entity_key_plural = None,
            reference_tax_benefit_system = None, tax_benefit_system = None, used_as_input_variables = None,
            year = None):

        if used_as_input_variables is None:
            used_as_input_variables = self.default_used_as_input_variables

        if tax_benefit_system is None:
            tax_benefit_system = france_data_tax_benefit_system
            reference_tax_benefit_system = None

        return super(AbstractErfsSurveyScenario, self).init_from_data_frame(
            input_data_frame = input_data_frame,
            input_data_frames_by_entity_key_plural = input_data_frames_by_entity_key_plural,
            reference_tax_benefit_system = reference_tax_benefit_system,
            tax_benefit_system = tax_benefit_system,
            used_as_input_variables = used_as_input_variables,
            year = year
            )

    def initialize_weights(self):
        self.weight_column_name_by_entity_key_plural['menages'] = 'wprm'
        self.weight_column_name_by_entity_key_plural['familles'] = 'weight_familles'
        self.weight_column_name_by_entity_key_plural['foyers_fiscaux'] = 'weight_foyers'
        self.weight_column_name_by_entity_key_plural['individus'] = 'weight_individus'


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

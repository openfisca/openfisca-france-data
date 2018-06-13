# -*- coding: utf-8 -*-


import logging
import numpy as np
import pandas as pd


from openfisca_core import periods, simulations
from openfisca_france_data.tests import base
from openfisca_survey_manager.scenarios import AbstractSurveyScenario

log = logging.getLogger(__name__)


class AbstractErfsSurveyScenario(AbstractSurveyScenario):
    id_variable_by_entity_key = dict(
        famille = 'idfam',
        foyer_fiscal = 'idfoy',
        menage = 'idmen',
        )
    filtering_variable_by_entity = dict(
        famille = 'menage_ordinaire_familles',
        foyer_fiscal = 'menage_ordinaire_foyers_fiscaux',
        individu = 'menage_ordinaire_individus',
        menage = 'menage_ordinaire',
        )
    role_variable_by_entity_key = dict(
        famille = 'quifam',
        foyer_fiscal = 'quifoy',
        menage = 'quimen',
        )
    weight_column_name_by_entity = dict(
        menage = 'wprm',
        famille = 'weight_familles',
        foyer_fiscal = 'weight_foyers',
        individu = 'weight_individus',
        )

    def build_input_data_from_test_case(self, test_case_scenario):
        for axe in test_case_scenario['axes'][0]:
            axe['name'] = 'salaire_imposable_pour_inversion'
        tax_benefit_system = self.tax_benefit_system
        simulation = tax_benefit_system.new_scenario().init_single_entity(**test_case_scenario).new_simulation()
        array_by_variable = dict()
        period = periods.period("{}".format(self.year))

        for variable in self.used_as_input_variables:
            array_by_variable[variable] = simulation.calculate_add(variable, period = period)

        for ident in ['idmen', 'idfoy', 'idfam']:
            array_by_variable[ident] = range(axe['count'])

        input_data_frame = pd.DataFrame(array_by_variable)

        for qui in ['quimen', 'quifoy', 'quifam']:
            input_data_frame[qui] = 0

        return input_data_frame

    @classmethod
    def create(cls, input_data_type = None, baseline_tax_benefit_system = None, reform = None, reform_key = None,
            tax_benefit_system = None, year = None):

        assert baseline_tax_benefit_system is not None
        assert year is not None
        assert not(
            (reform is not None) and (reform_key is not None)
            )
        assert not(
            ((reform is not None) or (reform_key is not None)) and (tax_benefit_system is not None)
            )

        if reform_key is not None:
            reform = base.get_cached_reform(
                reform_key = reform_key,
                tax_benefit_system = baseline_tax_benefit_system,
                )

        if reform is not None:
            tax_benefit_system = reform
        if input_data_type is not None:
            survey_scenario = cls(input_data_type = input_data_type, year = year)
        else:
            survey_scenario = cls(year = year)

        survey_scenario.set_tax_benefit_systems(
            tax_benefit_system = tax_benefit_system,
            baseline_tax_benefit_system = baseline_tax_benefit_system
            )
        survey_scenario.year = year

        return survey_scenario

    def init_from_test_case(self, test_case_scenario = None):
        assert test_case_scenario is not None
        input_data_frame = self.build_input_data_from_test_case(test_case_scenario)
        self.init_from_data_frame(input_data_frame = input_data_frame)
        self.new_simulation()
        if self.baseline_tax_benefit_system is not None:
            self.new_simulation(use_baseline = True)

    # def init_from_survey_tables(self, calibration_kwargs = None, data_year = None, inflation_kwargs = None,
    #         rebuild_input_data = False, rebuild_kwargs = None, input_survey_kwargs = None, trace = False, memory_config = None,
    #         tax_and_benefit_system = None):

    #     assert tax_and_benefit_system is not None

    #     if data_year is None:
    #         data_year = self.year

    #     if calibration_kwargs is not None:
    #         assert set(calibration_kwargs.keys()).issubset(set(
    #             ['target_margins_by_variable', 'parameters', 'total_population']))

    #     if inflation_kwargs is not None:
    #         assert set(inflation_kwargs.keys()).issubset(set(['inflator_by_variable', 'target_by_variable']))

    #     if rebuild_input_data:
    #         if rebuild_kwargs is not None:
    #             self.build_input_data(year = data_year, tax_and_benefit_system = tax_and_benefit_system, **rebuild_kwargs)
    #         else:
    #             self.build_input_data(year = data_year, tax_and_benefit_system = tax_and_benefit_system)

    #     if self.input_data_table_by_period is None:
    #         openfisca_survey_collection = SurveyCollection.load(collection = self.collection)
    #         openfisca_survey = openfisca_survey_collection.get_survey("{}_{}".format(
    #             self.input_data_survey_prefix, data_year))
    #         input_data_frame = openfisca_survey.get_values(table = "input").reset_index(drop = True)

    #         self.init_from_data_frame(
    #             input_data_frame = input_data_frame,
    #             )
    #     else:
    #         pass
    #     #
    #     input_survey_kwargs = input_survey_kwargs if input_survey_kwargs else dict()
    #     self.new_simulation(survey = input_survey_kwargs.get('input_survey'), trace = trace, memory_config = memory_config)
    #     if self.baseline_tax_benefit_system is not None:
    #         self.new_simulation(use_baseline = True, survey = input_survey_kwargs.get('baseline_input_survey'), trace = trace, memory_config = memory_config)
    #     #
    #     if calibration_kwargs:
    #         self.calibrate(**calibration_kwargs)

    #     if inflation_kwargs:
    #         self.inflate(**inflation_kwargs)

    def custom_initialize(self, simulation):
        three_year_span_variables = [
            'categorie_salarie',
            'chomage_brut',
            'chomage_imposable',
            'contrat_de_travail',
            'effectif_entreprise',
            'heures_remunerees_volume',
            # 'hsup',
            'pensions_alimentaires_percues',
            'retraite_brute',
            'retraite_imposable',
            'salaire_de_base',
            ]
        for offset in [0, -1, -2]:
            for variable in three_year_span_variables:
                assert variable in self.used_as_input_variables, \
                    '{} is not a in the input_varaibles to be used {}'.format(
                        variable, self.used_as_input_variables)
                holder = simulation.get_or_new_holder(variable)
                holder.set_input(simulation.period.offset(offset), simulation.calculate_add(variable))
            #
            for variable, value in self.default_value_by_variable.iteritems():
                log.info('Setting {} to new default value {}'.format(variable, value))
                holder = simulation.get_or_new_holder(variable)
                array = np.empty(holder.entity.count, dtype = holder.variable.dtype)
                array.fill(value)
                holder.set_input(simulation.period.offset(offset), array)

        # salaire_de_base = simulation.calculate_add('salaire_de_base')
        # months = ["0{}".format(i) for i in range(1, 10)] + ["10", "11", "12"]
        # for month in months:
        #     holder = simulation.get_or_new_holder('salaire_de_base')
        #     year = str(simulation.period.this_year)
        #     period = periods.period('{}-{}'.format(year, month))
        #     holder.set_input(period, salaire_de_base / 12)

    def custom_input_data_frame(self, input_data_frame, **kwargs):
        # input_data_frame['salaire_imposable_pour_inversion'] = input_data_frame.salaire_imposable
        if 'loyer' in input_data_frame:
            input_data_frame['loyer'] = 12 * input_data_frame.loyer

        input_data_frame.loc[
            input_data_frame.categorie_salarie.isin(range(2, 7)),
            'categorie_salarie'
            ] = 1

        for variable in ['quifam', 'quifoy', 'quimen']:
            log.debug(input_data_frame[variable].value_counts(dropna = False))


def new_simulation_from_array_dict(array_dict = None, debug = False,
        tax_benefit_system = None, trace = False, year = None):
    simulation = simulations.Simulation(
        debug = debug,
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

    column_by_name = tax_benefit_system.variables
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
        holder.array = np.array(array, dtype = holder.variable.dtype)

    return simulation

# -*- coding: utf-8 -*-


import logging
import numpy as np
import pandas as pd


from openfisca_core import periods, simulations
from openfisca_france_data.tests import base
from openfisca_survey_manager.survey_collections import SurveyCollection
from openfisca_survey_manager.scenarios import AbstractSurveyScenario


log = logging.getLogger(__name__)


class AbstractErfsSurveyScenario(AbstractSurveyScenario):
    id_variable_by_entity_key = dict(
        famille = 'idfam',
        foyer_fiscal = 'idfoy',
        menage = 'idmen',
        )
    filtering_variable_by_entity = dict(
        famille = 'champm_familles',
        foyer_fiscal = 'champm_foyers_fiscaux',
        individu = 'champm_individus',
        menage = 'champm',
        )
    role_variable_by_entity_key = dict(
        famille = 'quifam',
        foyer_fiscal = 'quifoy',
        menage = 'quimen',
        )

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
            if cls.input_data_table_by_period is not None:
                input_data_frame = None
            else:
                openfisca_survey_collection = SurveyCollection.load(collection = cls.collection)
                openfisca_survey = openfisca_survey_collection.get_survey("{}_{}".format(
                    cls.input_data_survey_prefix, data_year))
                input_data_frame = openfisca_survey.get_values(table = "input").reset_index(drop = True)

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
                'chomage_brut',
                'chomage_imposable',
                'contrat_de_travail',
                'effectif_entreprise',
                'heures_remunerees_volume',
                # 'hsup',
                'pensions_alimentaires_percues',
                'retraite_brute',
                'retraite_imposable',
                # 'salaire_imposable',
                'salaire_imposable_pour_inversion',
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
                    array = np.empty(holder.entity.count, dtype = holder.column.dtype)
                    array.fill(value)
                    holder.set_input(simulation.period.offset(offset), array)

    def custom_input_data_frame(self, input_data_frame):
        log.info('Customizing input_data_frame')
        input_data_frame['salaire_imposable_pour_inversion'] = input_data_frame.salaire_imposable
        input_data_frame['heures_remunerees_volume'] = input_data_frame.heures_remunerees_volume * 52
        if 'loyer' in input_data_frame:
            input_data_frame['loyer'] = 12 * input_data_frame.loyer

        input_data_frame.loc[
            input_data_frame.categorie_salarie.isin(range(2, 7)),
            'categorie_salarie'
            ] = 1

        for variable in ['quifam', 'quifoy', 'quimen']:
            log.info(input_data_frame[variable].value_counts(dropna = False))



            # def init_from_collection(self, collection = None, reference_tax_benefit_system = None, tax_benefit_system = None,
    #         used_as_input_variables = None, year = None):

    #     if used_as_input_variables is None:
    #         used_as_input_variables = self.default_used_as_input_variables

    #     if tax_benefit_system is None:
    #         tax_benefit_system = base.france_data_tax_benefit_system
    #         reference_tax_benefit_system = None

    #     variables_mismatch = set(used_as_input_variables).difference(set(input_data_frame.columns))
    #     if variables_mismatch:
    #         log.info(
    #             'The following variables used as input variables are not present in the input data frame: \n {}'.format(
    #                 variables_mismatch))
    #         log.info('The following variables are used as input variables: \n {}'.format(used_as_input_variables))
    #         log.info('The input_data_frame contains the following variables: \n {}'.format(input_data_frame.columns))
    #     return super(AbstractErfsSurveyScenario, self).init_from_collection(
    #         collection = collection,
    #         reference_tax_benefit_system = reference_tax_benefit_system,
    #         tax_benefit_system = tax_benefit_system,
    #         used_as_input_variables = used_as_input_variables,
    #         year = year,
    #         )

    def init_from_data_frame(self, input_data_frame = None, input_data_frame_by_entity = None,
            reference_tax_benefit_system = None, tax_benefit_system = None, used_as_input_variables = None,
            year = None):

        if used_as_input_variables is None:
            used_as_input_variables = self.default_used_as_input_variables

        if tax_benefit_system is None:
            tax_benefit_system = base.france_data_tax_benefit_system
            reference_tax_benefit_system = None

        return super(AbstractErfsSurveyScenario, self).init_from_data_frame(
            input_data_frame = input_data_frame,
            input_data_frame_by_entity = input_data_frame_by_entity,
            reference_tax_benefit_system = reference_tax_benefit_system,
            tax_benefit_system = tax_benefit_system,
            used_as_input_variables = used_as_input_variables,
            year = year,
            )

    def initialize_weights(self):
        self.weight_column_name_by_entity = dict(
            menage = 'wprm',
            famille = 'weight_familles',
            foyer_fiscal = 'weight_foyers',
            individu = 'weight_individus',
            )


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

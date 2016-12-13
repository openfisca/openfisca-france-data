# -*- coding: utf-8 -*-


from __future__ import division

import collections
from datetime import datetime
import logging
import os

from numpy import nan
import pandas

from openfisca_france_data import AGGREGATES_DEFAULT_VARS, FILTERING_VARS, DATA_DIR


log = logging.getLogger(__name__)


# TODO: units for amount and beneficiaries

class Aggregates(object):
    base_data_frame = None
    filter_by = None
    labels = collections.OrderedDict((
        ('var', u"Mesure"),
        ('entity', u"Entité"),
        ('dep', u"Dépenses\n(millions d'€)"),
        ('benef', u"Bénéficiaires\n(milliers)"),
        ('dep_default', u"Dépenses initiales\n(millions d'€)"),
        ('benef_default', u"Bénéficiaires\ninitiaux\n(milliers)"),
        ('dep_real', u"Dépenses\nréelles\n(millions d'€)"),
        ('benef_real', u"Bénéficiaires\nréels\n(milliers)"),
        ('dep_diff_abs', u"Diff. absolue\nDépenses\n(millions d'€)"),
        ('benef_diff_abs', u"Diff absolue\nBénéficiaires\n(milliers)"),
        ('dep_diff_rel', u"Diff. relative\nDépenses"),
        ('benef_diff_rel', u"Diff. relative\nBénéficiaires"),
        ))  # TODO: localize
    reference_simulation = None
    reform_simulation = None
    survey_scenario = None
    totals_df = None
    varlist = None

    def __init__(self, survey_scenario = None, debug = False, debug_all = False, trace = False):
        assert survey_scenario is not None
        self.year = survey_scenario.year
        self.survey_scenario = survey_scenario
        if self.reform_simulation is not None:
            raise('A simulation already exists')

        else:
            if not survey_scenario.simulation:
                survey_scenario.new_simulation()
            self.reform_simulation = survey_scenario.simulation

            if survey_scenario.reference_tax_benefit_system is not None:
                if not survey_scenario.reference_simulation:
                    survey_scenario.new_simulation(reference = True)
                self.reference_simulation = survey_scenario.reference_simulation
            else:
                self.reference_simulation = self.reform_simulation

        self.weight_column_name_by_entity = survey_scenario.weight_column_name_by_entity

        self.varlist = AGGREGATES_DEFAULT_VARS
        self.filter_by = FILTERING_VARS[0]

    def compute_aggregates(self, reference = True, reform = True, actual = True):
        """
        Compute aggregate amounts
        """
        filter_by = self.filter_by
        self.load_amounts_from_file()

        simulation_types = list()
        if reference:
            simulation_types.append('reference')
        if reform:
            simulation_types.append('reform')
        if actual:
            simulation_types.append('actual')

        no_reform = self.survey_scenario.reference_tax_benefit_system is None

        data_frame_by_simulation_type = dict()

        for simulation_type in simulation_types:
            if simulation_type == 'actual':
                data_frame_by_simulation_type['actual'] = self.totals_df.copy()
            else:
                if (
                    no_reform and (not reform) and
                    reference and
                    data_frame_by_simulation_type.get('reference') is not None
                        ):
                    data_frame_by_simulation_type['reform'] = data_frame_by_simulation_type['reference']
                    data_frame_by_simulation_type['reform'].rename(columns = dict(
                        reference_amount = "reform_amount",
                        reference_beneficiaries = "reform_beneficiaries",
                        ))
                    continue

                data_frame = pandas.DataFrame()
                for variable in self.varlist:
                    variable_data_frame = self.compute_variable_aggregates(
                        variable, filter_by = filter_by, simulation_type = simulation_type)
                    data_frame = pandas.concat((data_frame, variable_data_frame))
                data_frame_by_simulation_type[simulation_type] = data_frame.copy()

        if reference and reform:
            del data_frame_by_simulation_type['reform']['entity']
            del data_frame_by_simulation_type['reform']['label']

        self.base_data_frame = pandas.concat(data_frame_by_simulation_type.values(), axis = 1).loc[self.varlist]
        return self.base_data_frame

    def compute_difference(self, target = "reference", default = 'actual', amount = True, beneficiaries = True,
            absolute = True, relative = True):
        '''
        Computes and adds relative differences to the data_frame
        '''
        assert relative or absolute
        assert amount or beneficiaries
        base_data_frame = self.base_data_frame if self.base_data_frame is not None else self.compute_aggregates()

        difference_data_frame = base_data_frame[['label', 'entity']].copy()
        quantities = ['amount'] if amount else None + ['beneficiaries'] if beneficiaries else None

        for quantity in quantities:
            difference_data_frame['{}_absolute_difference'.format(quantity)] = (
                base_data_frame['{}_{}'.format(target, quantity)] - base_data_frame['{}_{}'.format(default, quantity)]
                )
            difference_data_frame['{}_relative_difference'.format(quantity)] = (
                base_data_frame['{}_{}'.format(target, quantity)] - base_data_frame['{}_{}'.format(default, quantity)]
                ) / abs(base_data_frame['{}_{}'.format(default, quantity)])
        return difference_data_frame

    def create_description(self):
        '''
        Creates a description dataframe
        '''
        now = datetime.now()
        return pandas.DataFrame([
            u'OpenFisca',
            u'Calculé le %s à %s' % (now.strftime('%d-%m-%Y'), now.strftime('%H:%M')),
            u'Système socio-fiscal au %s' % self.simulation.period.start,
            u"Données d'enquêtes de l'année %s" % str(self.simulation.input_table.survey_year),
            ])

    def compute_variable_aggregates(self, variable, filter_by = None, simulation_type = 'reference'):
        """
        Returns aggregate spending, and number of beneficiaries
        for the relevant entity level

        Parameters
        ----------
        variable : string
                   name of the variable aggregated according to its entity
        filter_by : string
                    name of the variable to filter by
        simulation_type : string
                          reference or reform or actual
        """
        assert simulation_type in ['reference', 'reform']
        prefixed_simulation = '{}_simulation'.format(simulation_type)
        simulation = getattr(self, prefixed_simulation)
        column_by_name = simulation.tax_benefit_system.column_by_name
        column = column_by_name[variable]
        weight = self.weight_column_name_by_entity[column.entity.key]
        assert weight in column_by_name, "{} not a variable of the {} tax_benefit_system".format(
            weight, simulation_type)
        # amounts and beneficiaries from current data and default data if exists
        # Build weights for each entity
        data = pandas.DataFrame({
            variable: simulation.calculate_add(variable),
            weight: simulation.calculate(weight),
            })
        if filter_by:
            filter_dummy = simulation.calculate(
                self.survey_scenario.filtering_variable_by_entity[column.entity.key]
                )
        try:
            amount = int(
                (data[variable] * data[weight] * filter_dummy / 10 ** 6).sum().round()
                )
        except:
            amount = nan
        try:
            beneficiaries = int(
                ((data[variable] != 0) * data[weight] * filter_dummy / 10 ** 3).sum().round()
                )
        except:
            beneficiaries = nan

        variable_data_frame = pandas.DataFrame(
            data = {
                'label': column_by_name[variable].label,
                'entity': column_by_name[variable].entity.key,
                '{}_amount'.format(simulation_type): amount,
                '{}_beneficiaries'.format(simulation_type): beneficiaries,
                },
            index = [variable],
            )

        return variable_data_frame

    def load_amounts_from_file(self, filename = None, year = None):
        '''
        Loads totals from files
        '''
        if year is None:
            year = self.year
        if filename is None:
            data_dir = DATA_DIR
            assert os.path.exists(DATA_DIR)

        try:
            filename = os.path.join(data_dir, "amounts.h5")
            store = pandas.HDFStore(filename)
            df_a = store['amounts']
            df_b = store['benef']
            store.close()
            self.totals_df = pandas.DataFrame(data = {
                "actual_amount": df_a[year] / 10 ** 6,
                "actual_beneficiaries": df_b[year] / 10 ** 3,
                })
            row = pandas.DataFrame({'actual_amount': nan, 'actual_beneficiaries': nan}, index = ['logt'])
            self.totals_df = self.totals_df.append(row)

            # Add some aditionnals totals
            for col in ['actual_amount', 'actual_beneficiaries']:
                # Deals with logt
                logt = 0
                for var in ['apl', 'alf', 'als']:
                    logt += self.totals_df.get_value(var, col)
                self.totals_df.set_value('logt', col, logt)

                # Deals with rsa rmi
                rsa = 0
                for var in ['rmi', 'rsa']:
                    rsa += self.totals_df.get_value(var, col)
                self.totals_df.set_value('rsa', col, rsa)

                # Deals with irpp, csg, crds
                for var in ['irpp', 'csg', 'crds', 'cotsoc_noncontrib']:
                    if col in ['actual_amount']:
                        val = - self.totals_df.get_value(var, col)
                        self.totals_df.set_value(var, col, val)
                return
        except KeyError as e:
            log.info("No administrative data available for year {} in file {}".format(year, filename))
            log.info("Try to use administrative data for year {}".format(year - 1))
            self.load_amounts_from_file(year = year - 1)
            # self.totals_df = pandas.DataFrame()
            return

    def save_table(self, directory = None, filename = None, table_format = None):
        '''
        Saves the table to csv or xls (default) format
        '''
        now = datetime.now()
        if table_format is None:
            if filename is not None:
                extension = filename[-4:]
                if extension == '.xls':
                    table_format = 'xls'
                elif extension == '.csv':
                    table_format = 'csv'
            else:
                table_format = 'xls'

        if directory is None:
            directory = "."
        if filename is None:
            filename = 'Aggregates_%s.%s' % (now.strftime('%d-%m-%Y'), table_format)

        fname = os.path.join(directory, filename)

        try:
            df = self.data_frame
            if table_format == "xls":
                writer = pandas.ExcelWriter(str(fname))
                df.to_excel(writer, "aggregates", index= False, header= True)
                descr = self.create_description()
                descr.to_excel(writer, "description", index = False, header=False)
                writer.save()
            elif table_format == "csv":
                df.to_csv(fname, "aggregates", index= False, header = True)
        except Exception, e:
                raise Exception("Aggregates: Error saving file", str(e))

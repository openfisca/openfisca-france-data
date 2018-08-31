# -*- coding: utf-8 -*-


import collections
from datetime import datetime
import logging
import os

import numpy as np
import pandas as pd

try:
    from ipp_macro_series_parser.config import Config  # type: ignore
except ImportError:
    Config = None


from openfisca_france_data import AGGREGATES_DEFAULT_VARS  # type: ignore


log = logging.getLogger(__name__)


# TODO:
#  * units for amount and beneficiaries
#  * Localisation

class Aggregates(object):
    base_data_frame = None
    filter_by = None
    labels = collections.OrderedDict((
        ('label', u"Mesure"),
        ('entity', u"Entité"),
        ('reform_amount', u"Dépenses\n(millions d'€)"),
        ('reform_beneficiaries', u"Bénéficiaires\n(milliers)"),
        ('baseline_amount', u"Dépenses initiales\n(millions d'€)"),
        ('baseline_beneficiaries', u"Bénéficiaires\ninitiaux\n(milliers)"),
        ('actual_amount', u"Dépenses\nréelles\n(millions d'€)"),
        ('actual_beneficiaries', u"Bénéficiaires\nréels\n(milliers)"),
        ('amount_absolute_difference', u"Diff. absolue\nDépenses\n(millions d'€)"),
        ('beneficiaries_absolute_difference', u"Diff absolue\nBénéficiaires\n(milliers)"),
        ('amount_relative_difference', u"Diff. relative\nDépenses"),
        ('beneficiaries_relative_difference', u"Diff. relative\nBénéficiaires"),
        ))
    baseline_simulation = None
    simulation = None
    survey_scenario = None
    totals_df = None
    aggregate_variables = None

    def __init__(self, survey_scenario = None, debug = False, trace = False):
        assert survey_scenario is not None
        self.year = survey_scenario.year
        self.survey_scenario = survey_scenario
        assert self.simulation is None

        assert survey_scenario.simulation is not None
        self.simulation = survey_scenario.simulation

        if survey_scenario.baseline_tax_benefit_system is not None:
            assert survey_scenario.baseline_simulation is not None
            self.baseline_simulation = survey_scenario.baseline_simulation
        else:
            self.baseline_simulation = None

        self.weight_variable_by_entity = survey_scenario.weight_variable_by_entity
        self.aggregate_variables = AGGREGATES_DEFAULT_VARS

    def compute_aggregates(self, use_baseline = True, reform = True, actual = True):
        """
        Compute aggregate amounts
        """
        filter_by = self.filter_by
        self.totals_df = load_actual_data(year = self.year)

        simulation_types = list()
        if use_baseline:
            assert self.baseline_simulation is not None
            simulation_types.append('baseline')
        if reform:
            simulation_types.append('reform')
        if actual:
            simulation_types.append('actual')

        data_frame_by_simulation_type = dict()

        for simulation_type in simulation_types:
            if simulation_type == 'actual':
                data_frame_by_simulation_type['actual'] = self.totals_df.copy() if self.totals_df is not None else None
            else:
                use_baseline = False if simulation_type == 'reform' else True
                data_frame = pd.DataFrame()
                for variable in self.aggregate_variables:
                    variable_data_frame = self.compute_variable_aggregates(
                        variable, use_baseline = use_baseline, filter_by = filter_by)
                    data_frame = pd.concat((data_frame, variable_data_frame))

                data_frame.rename(columns = {
                    'amount': '{}_amount'.format(simulation_type),
                    'beneficiaries': '{}_beneficiaries'.format(simulation_type),
                    },
                    inplace = True
                    )
                data_frame_by_simulation_type[simulation_type] = data_frame

        if use_baseline and reform:
            del data_frame_by_simulation_type['reform']['entity']
            del data_frame_by_simulation_type['reform']['label']

        self.base_data_frame = pd.concat(
            list(data_frame_by_simulation_type.values()),
            axis = 1,
            sort = True,
            ).loc[self.aggregate_variables]
        return self.base_data_frame

    def compute_difference(self, target = "baseline", default = 'actual', amount = True, beneficiaries = True,
            absolute = True, relative = True):
        '''
        Compute and add relative and/or absolute differences to the data_frame
        '''
        assert relative or absolute
        assert amount or beneficiaries
        base_data_frame = self.base_data_frame if self.base_data_frame is not None else self.compute_aggregates()

        difference_data_frame = base_data_frame[['label', 'entity']].copy()
        quantities = list()
        quantities += ['amount'] if amount else None
        quantities += ['beneficiaries'] if beneficiaries else None

        for quantity in quantities:
            difference_data_frame['{}_absolute_difference'.format(quantity)] = (
                abs(base_data_frame['{}_{}'.format(target, quantity)]) - base_data_frame['{}_{}'.format(default, quantity)]
                )
            difference_data_frame['{}_relative_difference'.format(quantity)] = (
                abs(base_data_frame['{}_{}'.format(target, quantity)]) - base_data_frame['{}_{}'.format(default, quantity)]
                ) / abs(base_data_frame['{}_{}'.format(default, quantity)])
        return difference_data_frame

    def compute_variable_aggregates(self, variable, use_baseline = False, filter_by = None):
        """
        Returns aggregate spending, and number of beneficiaries
        for the relevant entity level

        Parameters
        ----------
        variable : string
                   name of the variable aggregated according to its entity
        use_baseline : bool
                    Use the baseline or the reform or the only avalilable simulation when no reform (default)
        filter_by : string or boolean
                    If string use it as the name of the variable to filter by
                    If not None or False and the string is not present in the tax-benefit-system use the default filtering variable if any
        """
        if use_baseline:
            simulation = self.baseline_simulation
        else:
            simulation = self.simulation

        variables = simulation.tax_benefit_system.variables
        column = variables.get(variable)

        if column is None:
            msg = "Variable {} is not available".format(variable)
            if use_baseline:
                msg += " in baseline simulation"
            log.info(msg)
            return pd.DataFrame(
                data = {
                    'label': variable,
                    'entity': 'Unknown entity',
                    'amount': 0,
                    'beneficiaries': 0,
                    },
                index = [variable],
                )
        weight = self.weight_variable_by_entity[column.entity.key]
        assert weight in variables, "{} not a variable of the tax_benefit_system".format(weight)

        weight_array = simulation.calculate(weight, period = self.year).astype('float')
        assert not np.isnan(np.sum(weight_array)), "The are some NaN in weights {} for entity {}".format(
            weight, column.entity.key)
        # amounts and beneficiaries from current data and default data if exists
        # Build weights for each entity
        variable_array = simulation.calculate_add(variable, period = self.year).astype('float')
        assert np.isfinite(variable_array).all(), "The are non finite values in variable {} for entity {}".format(
            variable, column.entity.key)
        data = pd.DataFrame({
            variable: variable_array,
            weight: weight_array,
            })
        if filter_by:
            filter_dummy_variable = (
                filter_by
                if filter_by in variables
                else self.survey_scenario.filtering_variable_by_entity[column.entity.key]
                )
            filter_dummy_array = simulation.calculate(filter_dummy_variable, period = self.year)

        else:
            filter_dummy_array = 1

        assert np.isfinite(filter_dummy_array).all(), "The are non finite values in variable {} for entity {}".format(
            filter_dummy_variable, column.entity.key)

        amount = int(
            (data[variable] * data[weight] * filter_dummy_array / 10 ** 6).sum()
            )
        beneficiaries = int(
            ((data[variable] != 0) * data[weight] * filter_dummy_array / 10 ** 3).sum()
            )
        variable_data_frame = pd.DataFrame(
            data = {
                'label': variables[variable].label,
                'entity': variables[variable].entity.key,
                'amount': amount,
                'beneficiaries': beneficiaries,
                },
            index = [variable],
            )

        return variable_data_frame

    # def load_amounts_from_file(self, filename = None, year = None):
    #     """
    #     Load totals from files
    #     """
    #     if year is None:
    #         year = self.year
    #     if filename is None:
    #         data_dir = DATA_DIR
    #         assert os.path.exists(DATA_DIR)

    #     try:
    #         filename = os.path.join(data_dir, "amounts.h5")
    #         store = pd.HDFStore(filename)
    #         df_a = store['amounts']
    #         df_b = store['benef']
    #         store.close()
    #         self.totals_df = pd.DataFrame(data = {
    #             "actual_amount": df_a[year] / 10 ** 6,
    #             "actual_beneficiaries": df_b[year] / 10 ** 3,
    #             })
    #         row = pd.DataFrame({'actual_amount': np.nan, 'actual_beneficiaries': np.nan}, index = ['logt'])
    #         self.totals_df = self.totals_df.append(row)

    #         # Add some aditionnals totals
    #         for col in ['actual_amount', 'actual_beneficiaries']:
    #             # Deals with logt
    #             logt = 0
    #             for var in ['apl', 'alf', 'als']:
    #                 logt += self.totals_df.get_value(var, col)
    #             self.totals_df.set_value('logt', col, logt)

    #             # Deals with rsa rmi
    #             rsa = 0
    #             for var in ['rmi', 'rsa']:
    #                 rsa += self.totals_df.get_value(var, col)
    #             self.totals_df.set_value('rsa', col, rsa)

    #             # Deals with irpp, csg, crds
    #             for var in ['irpp', 'csg', 'crds', 'cotisations_non_contributives']:
    #                 if col in ['actual_amount']:
    #                     val = - self.totals_df.get_value(var, col)
    #                     self.totals_df.set_value(var, col, val)
    #             return
    #     except KeyError as e:
    #         log.info("No administrative data available for year {} in file {}".format(year, filename))
    #         log.info("Try to use administrative data for year {}".format(year - 1))
    #         self.load_amounts_from_file(year = year - 1)
    #         # self.totals_df = pd.DataFrame()
    #         return

    def create_description(self):
        """
        Create a description dataframe
        """
        now = datetime.now()
        return pd.DataFrame([
            u'OpenFisca',
            u'Calculé le %s à %s' % (now.strftime('%d-%m-%Y'), now.strftime('%H:%M')),
            u'Système socio-fiscal au %s' % self.simulation.period.start.year,
            u"Données d'enquêtes de l'année %s" % str(self.data_year),
            ])

    def export_table(self,
            path = None,
            absolute = True,
            amount = True,
            beneficiaries = True,
            default = 'actual',
            relative = True,
            table_format = None,
            target = "reform"):
        """
        Save the table to csv or excel (default) format
        """
        assert path is not None
        now = datetime.now()

        df = self.get_data_frame(
            absolute = absolute,
            amount = amount,
            beneficiaries = beneficiaries,
            default = default,
            relative = relative,
            target = target,
            )

        if os.path.isdir(path):
            file_path = os.path.join(path, 'Aggregates_%s.%s' % (now.strftime('%d-%m-%Y'), table_format))
        else:
            file_path = path

        if table_format is None:
            if path is not None:
                extension = file_path[-4:]
                if extension == '.xls':
                    table_format = 'xls'
                elif extension == '.csv':
                    table_format = 'csv'
            else:
                table_format = 'xls'
        try:
            if table_format == "xls":
                writer = pd.ExcelWriter(file_path)
                df.to_excel(writer, "aggregates", index = False, header = True)
                descr = self.create_description()
                descr.to_excel(writer, "description", index = False, header = False)
                writer.save()
            elif table_format == "csv":
                df.to_csv(file_path, index = False, header = True)
        except Exception as e:
                raise Exception("Aggregates: Error saving file", str(e))

    def get_calibration_coeffcient(self, target = "reform"):
        df = self.compute_aggregates(
            actual = True,
            use_baseline = 'baseline' == target,
            reform = 'reform' == target,
            )
        return df['{}_amount'.format(target)] / df['actual_amount']

    def get_data_frame(
            self,
            absolute = True,
            amount = True,
            beneficiaries = True,
            default = 'actual',
            formatting = True,
            relative = True,
            target = "reform",
            ):
        assert target is None or target in ['reform', 'baseline']

        columns = self.labels.keys()
        if (absolute or relative) and (target != default):
            difference_data_frame = self.compute_difference(
                absolute = absolute,
                amount = amount,
                beneficiaries = beneficiaries,
                default = default,
                relative = relative,
                target = target,
                )
        else:
            difference_data_frame = None
        # Removing unwanted columns
        if amount is False:
            columns = [column for column in columns if 'amount' not in columns]

        if beneficiaries is False:
            columns = [column for column in columns if 'beneficiaries' not in column]

        if absolute is False:
            columns = [column for column in columns if 'absolute' not in column]

        if relative is False:
            columns = [column for column in columns if 'relative' not in column]

        for simulation_type in ['reform', 'baseline', 'actual']:
            if simulation_type not in [target, default]:
                columns = [column for column in columns if simulation_type not in column]

        aggregates_data_frame = self.compute_aggregates(
            actual = 'actual' in [target, default],
            use_baseline = 'baseline' in [target, default],
            reform = 'reform' in [target, default],
            )
        ordered_columns = [
            'label',
            'entity',
            'reform_amount',
            'baseline_amount',
            'actual_amount',
            'amount_absolute_difference',
            'amount_relative_difference',
            'reform_beneficiaries',
            'baseline_beneficiaries',
            'actual_beneficiaries',
            'beneficiaries_absolute_difference',
            'beneficiaries_relative_difference'
            ]
        if difference_data_frame is not None:
            df = (
                aggregates_data_frame
                .merge(difference_data_frame, how = 'left')[columns]
                .reindex_axis(ordered_columns, axis = 1)
                .dropna(axis = 1, how = 'all')
                .rename(columns = self.labels)
                )
        else:
            df = (
                aggregates_data_frame[columns]
                .reindex_axis(ordered_columns, axis = 1)
                .dropna(axis = 1, how = 'all')
                .rename(columns = self.labels)
                )

        if formatting:
            relative_columns = [column for column in df.columns if 'relative' in column]
            df[relative_columns] = df[relative_columns].applymap(
                lambda x: "{:.2%}".format(x) if str(x) != 'nan' else 'nan')
            import numpy as np
            for column in df.columns:
                if issubclass(np.dtype(df[column]).type, np.number):
                    df[column] = (df[column]
                        .apply(lambda x: "{:d}".format(int(round(x))) if str(x) != 'nan' else 'nan')
                        )
        return df


# Helpers


def load_actual_data(year = None):
    assert year is not None

    if not Config:
        log.info("No actual data available")
        return

    parser = Config()

    # Cotisations CSG -CRDS
    try:
        directory = os.path.join(
            parser.get('data', 'prelevements_sociaux_directory'),
            'clean',
            )
        csg_crds_amounts = pd.read_csv(
            os.path.join(directory, 'recette_csg_crds.csv'),
            index_col = 0
            ).rename(
                dict(
                    recette_csg = 'csg',
                    recette_crds = 'crds',
                    )
                ) / 1e6
        csg_by_type_amounts = pd.read_csv(
            os.path.join(directory, 'recette_csg_by_type.csv'),
            index_col = 0,
            ).drop(
                ['source']
                ).astype(float) / 1e6
        assiette_csg_by_type_amounts = pd.read_csv(
            os.path.join(directory, 'assiette_csg_by_type.csv'),
            index_col = 0,
            ) / 1e6
    except Exception:
        assiette_csg_by_type_amounts = None
        csg_by_type_amounts = None
        csg_crds_amounts = None
        pass
    # Prestations sociales
    directory = os.path.join(
        parser.get('data', 'prestations_sociales_directory'),
        'clean',
        )
    amounts_csv = os.path.join(directory, 'historique_depenses.csv')
    beneficiaries_csv = os.path.join(directory, 'historique_beneficiaires.csv')
    prestations_sociales_amounts = pd.read_csv(amounts_csv, index_col = 0)
    prestations_sociales_beneficiaries = pd.read_csv(beneficiaries_csv, index_col = 0)
    # Minimum vieillesses
    minimum_vieillesse_beneficiaries_csv = os.path.join(
        directory, 'historique_beneficiaires_minimum_vieillesse.csv')
    if os.path.exists(minimum_vieillesse_beneficiaries_csv):
        minimum_vieillesse_beneficiaries = pd.read_csv(minimum_vieillesse_beneficiaries_csv, index_col = 0)

    amounts = pd.concat(
        [
            assiette_csg_by_type_amounts,
            csg_by_type_amounts,
            csg_crds_amounts,
            prestations_sociales_amounts,
            ],
        sort = True,
        )
    beneficiaries = pd.concat(
        [minimum_vieillesse_beneficiaries, prestations_sociales_beneficiaries],
        sort = True,
        )

    return pd.DataFrame(data = {
        "actual_amount": amounts[str(year)],
        "actual_beneficiaries": beneficiaries[str(year)],
        })

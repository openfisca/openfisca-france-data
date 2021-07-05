import logging
import os

import numpy
from pandas import Series

import openfisca_france  # type: ignore
from openfisca_survey_manager.survey_collections import SurveyCollection  # type: ignore
from openfisca_survey_manager.surveys import Survey  # type: ignore

from openfisca_france_data import openfisca_france_tax_benefit_system


log = logging.getLogger(__name__)


def assert_dtype(series, dtype_string):
    assert isinstance(series, Series), "First argument is not of Series type"
    try:
        assert series.dtype == numpy.dtype(dtype_string), "Series {} dtype is {} instead of {}".format(
            series.name, series.dtype, dtype_string)
    except AssertionError:
        assert numpy.issubdtype(series.dtype, numpy.dtype(dtype_string)), "Series {} dtype is {} instead of {}".format(
            series.name, series.dtype, dtype_string)


def assert_variable_in_range(name, wrange, table):
    """Asserts if transformed variables are in correct range.

    wrange is a list like [minimum, maximum]
    """
    temp = (table[table[name].notnull()])
    range_1 = wrange[0]
    range_2 = wrange[1]
    for v in temp[name]:
        assert v in range(range_1, range_2), 'some non-null values for %s not in wanted %s: %s' % (
            name, str(wrange), str(v))


def control(dataframe, verbose = False, verbose_columns = None, debug = False, verbose_length = 5, ignore = None):
    """Helps debugging the data crunchin' files.

    Parameters
    ---------
    verbose: Default False
    Indicates whether to print the dataframe itself or just perform reguler checks.

    verbose_columns: List
    The columns of the dataframe to print

    verbose_length: Int
    the number of rows to print
    """
    std_list = ['idfoy', 'quifoy', 'idmen', 'quimen', 'idfam', 'quifam']
    for var in std_list:
        try:
            assert var in dataframe.columns
        except Exception:
            raise Exception('the dataframe does not contain the required column %s' % var)

    log.info('longueur de la data frame = {}'.format(len(dataframe.index)))
    if debug:
        log.info('nb de doublons: {}'.format(len(dataframe[dataframe.duplicated()])))
        log.info('nb de doublons idfoy/quifoy: {}'.format(len(dataframe[dataframe.duplicated(
            subset = ['idfoy', 'quifoy'])])))
        log.info('nb de doublons idmen/quimen: {}'.format(len(dataframe[dataframe.duplicated(
            subset = ['idmen', 'quimen'])])))
        log.info('nb de doublons idfam/quifam: {}'.format(len(dataframe[dataframe.duplicated(
            subset = ['idfam', 'quifam'])])))

    if not(debug):
        assert not(dataframe.duplicated().any()), 'présence de lignes en double dans la dataframe'
        assert ~(dataframe.duplicated(subset = ['idfoy', 'quifoy'])).all(), 'duplicate of tuple idfoy/quifoy'
        assert ~(dataframe.duplicated(subset = ['idmen', 'quimen'])).all(), 'duplicate of tuple idmen/quimen'
        assert ~(dataframe.duplicated(subset = ['idfam', 'quifam'])).all(), 'duplicate of tuple idfam/quifam'

    empty_columns = []
    for col in dataframe:
        if dataframe[col].isnull().all():
            empty_columns.append(col)

    if empty_columns != []:
        log.info('liste des colonnes entièrement vides: \n {}'.format(empty_columns))

    if verbose is True:
        log.info('------ informations détaillées -------')
        print_id(dataframe)

        if verbose_columns is None:
            if dataframe.duplicated().any():
                log.info(dataframe[dataframe.duplicated()].head(verbose_length).to_string())

        else:
            if dataframe.duplicated(verbose_columns).any():
                print('nb lignes lignes dupliquées _____', len(dataframe[dataframe.duplicated(verbose_columns)]))
                print(dataframe.loc[:, verbose_columns].describe())
            for col in verbose_columns:
                print('nombre de NaN dans %s : ' % (col), dataframe[col].isnull().sum())
            print('colonnes contrôlées ------>', verbose_columns)
    print('vérifications terminées')


def count_NA(name, table):
    """Counts the number of Na's in a specified axis."""
    print("count of NA's for %s is %s" % (name, str(sum(table[name].isnull()))))


def id_formatter(dataframe, entity_id):
    dataframe[entity_id + "_original"] = dataframe[entity_id].copy()
    id_unique = dataframe[entity_id].unique()
    new_id_by_old_id = dict(zip(
        id_unique, range(len(id_unique)))
        )
    dataframe[entity_id] = dataframe[entity_id].map(new_id_by_old_id)
    return dataframe


def print_id(df):
    try:
        log.info("Individus with distinc noindiv: {} / {}".format(len(df.noindiv), len(df)))
    except Exception:
        log.info("No noindiv")

    try:
        # Ici, il doit y avoir autant de vous que d'idfoy
        log.info("Individus dans les Foyers: {} \n".format(len(df.idfoy)))
        log.info(df["quifoy"].value_counts(dropna=False))
        if df["idfoy"].isnull().any():
            log.info("NaN in idfoy : {}".format(df["idfoy"].isnull().sum()))
        if df["quifoy"].isnull().any():
            log.info("NaN in quifoy : {}".format(df["quifoy"].isnull().sum()))
    except Exception:
        log.info("No idfoy or quifoy")

    try:
        # Ici, il doit y avoir autant de quimen = 0 que d'idmen
        log.info(u"Individus dans les Ménages {} \n".format(len(df.idmen)))
        log.info("\n" + str(df["quimen"].value_counts(dropna=False)))
        if df["idmen"].isnull().any():
            log.info("NaN in idmen : {} ".format(df["idmen"].isnull().sum()))
        if df["quimen"].isnull().any():
            log.info("NaN in quimen : {} ".format(df["quimen"].isnull().sum()))
    except Exception:
        print("No idmen or quimen")

    try:
        # Ici, il doit y avoir autant de quifam = 0 que d'idfam
        log.info("Individus dans les Familles {}\n".format(len(df.idfam)))
        log.info(df["quifam"].value_counts(dropna=False))
        if df["idfam"].isnull().any():
            log.info("NaN in idfam : {} ".format(df["idfam"].isnull().sum()))
        if df["quifam"].isnull().any():
            log.info("NaN in quifam : {} ".format(df["quifam"].isnull().sum()))
    except Exception:
        log.info("No idfam or quifam")
    compute_masses(df)


def compute_masses(dataframe):
    variables = [
        'chomage_imposable',
        'pensions_alimentaires_percues',
        'rag',
        'retraite_imposable',
        'ric',
        'rnc',
        'salaire_imposable',
        'f4ba',
        ]
    for variable in variables:
        if set([variable, 'wprm']).issubset(set(dataframe.columns)):
            log.info("Mass of {}: {}".format(variable, (dataframe[variable] * dataframe['wprm']).sum() / 1e9))
        else:
            log.info("Impossible to compute mass of {}".format(variable))


def check_entity_structure(dataframe, entity):
    log.info("Checking entity {}".format(entity))
    role = 'qui' + entity
    entity_id = 'id' + entity
    error_messages = list()

    if dataframe[role].isnull().any():
        error_messages.append("there are NaN in qui{}".format(entity))
    max_entity_role_value = dataframe[role].max().astype("int")
    id_count = len(dataframe['id' + entity].unique())
    head_count = (dataframe['qui' + entity] == 0).sum()
    if id_count != head_count:
        error_messages.append("Wrong number of heads for {}: {} different ids for {} heads".format(
            entity, id_count, head_count))

    entity_ids_by_role = dict()
    for role_value in range(max_entity_role_value + 1, 1, -1):
        print(entity, role_value)
        log.info("Dealing with role {} of entity {}".format(role_value, entity))
        entity_ids_by_role[role_value] = set(dataframe.loc[dataframe[role] == role_value, entity_id].unique())

        if role_value < max_entity_role_value:
            difference = entity_ids_by_role[role_value + 1].difference(entity_ids_by_role[role_value])
            if not entity_ids_by_role[role_value + 1].issubset(entity_ids_by_role[role_value]):
                error_messages.append(
                    "Problem with entity {} at role = {} for id {}".format(
                        entity, role_value, difference
                        )
                    )
                erroneous_ids = difference
                return False, error_messages, erroneous_ids
            else:
                continue
    return True, None, None


def check_structure(dataframe):
    duplicates = dataframe.noindiv.duplicated().sum()
    messages = list()
    erroneous_ids_by_entity = dict()
    if duplicates != 0:
        messages.append("There are {} duplicated individuals".format(duplicates))
    for entity in ['fam', 'foy', 'men']:
        print(entity)
        checked, error_messages, erroneous_ids = check_entity_structure(dataframe, entity)
        print(checked, error_messages, erroneous_ids)
        if not checked:
            messages.append('Structure error for {}'.format(entity))
            messages.append(error_messages)
            erroneous_ids_by_entity[entity] = erroneous_ids
    if not messages:
        return True, None
    else:
        log.info('\n'.join('{}'.format(item) for item in messages))
        return False, erroneous_ids_by_entity


def build_cerfa_fields_by_column_name(year, sections_cerfa):
    tax_benefit_system = openfisca_france_tax_benefit_system
    cerfa_fields_by_column_name = dict()
    for name, column in tax_benefit_system.variables.items():
        for section_cerfa in sections_cerfa:
            if name.startswith(f"f{section_cerfa}"):
                end = column.end or None

                if end is None or end.year >= year:
                    if column.entity.key == 'individu':
                        cerfa_field = ['f' + x.lower() for x in list(column.cerfa_field.values())]
                    elif column.entity.key == 'foyer_fiscal':
                        cerfa_field = ['f' + column.cerfa_field.lower()]
                    cerfa_fields_by_column_name[name] = cerfa_field
    return cerfa_fields_by_column_name


def build_cerfa_fields_by_variable(year):
    tax_benefit_system = openfisca_france_tax_benefit_system
    cerfa_fields_by_variable = dict()
    for name, variable in sorted(tax_benefit_system.variables.items()):
        if variable.cerfa_field is None:
            continue
        if name.startswith('case') or name.startswith('nb'):
            continue
        end = variable.end or None
        if end is None or end.year >= year:
            if variable.entity.key == 'individu':
                cerfa_field = ['f' + x.lower() for x in list(variable.cerfa_field.values())]
            elif variable.entity.key == 'foyer_fiscal':
                cerfa_field = ['f' + variable.cerfa_field.lower()]
            cerfa_fields_by_variable[name] = cerfa_field
    return cerfa_fields_by_variable


def rectify_dtype(dataframe, verbose = True):
    series_to_rectify = []
    rectified_series = []
    for serie_name, serie in dataframe.items():
        if serie.dtype.char == 'O':  # test for object
            series_to_rectify.append(serie_name)
            if verbose:
                print("""
Variable name: {}
NaN are present : {}
{}""".format(serie_name, serie.isnull().sum(), serie.value_counts()))
            # bool
            if serie.dropna().isin([True, False]).all():
                if serie.isnull().any():
                    serie = serie.fillna(False).copy()
                dataframe[serie_name] = serie.astype('bool', copy = True)
                rectified_series.append(serie_name)
            # Nombre 01-99
            elif serie.dropna().str.match("\d\d$").all():
                if serie.isnull().any():
                    serie = serie.fillna(0)
                dataframe[serie_name] = serie.astype('int', copy = True)
                rectified_series.append(serie_name)
            # year
            elif serie_name in ['birthvous', 'birthconj', 'caseH']:
                if serie.isnull().any():
                    serie = serie.fillna(9999)
                dataframe[serie_name] = serie.astype('int', copy = True)
                rectified_series.append(serie_name)
            # datetime
            elif serie_name[0:4] == "date":
                from pandas import to_datetime
                dataframe[serie_name] = to_datetime(
                    serie.str[:2] + "-" + serie.str[2:4] + "-" + serie.str[4:8],
                    coerce = True)
                rectified_series.append(serie_name)

            if serie_name in rectified_series:
                if verbose:
                    print("""Converted to {}
{}""".format(dataframe[serie_name].dtype, dataframe[serie_name].value_counts()))

    if verbose:
        print(set(series_to_rectify).difference(rectified_series))


def normalizes_roles_in_entity(dataframe, entity_id_name, entity_role_name):
    last_roles = (dataframe[entity_role_name] >= 2).copy()
    dataframe.loc[last_roles, entity_role_name] = 2
    dataframe[entity_role_name] = dataframe[entity_role_name].astype('int')


def set_variables_default_value(dataframe, year):
    tax_benefit_system = openfisca_france_tax_benefit_system

    for column_name, column in tax_benefit_system.variables.items():
        if column_name in dataframe.columns:
            dataframe[column_name].fillna(column.default_value, inplace = True)
            dataframe[column_name] = dataframe[column_name].astype(column.dtype)


def store_input_data_frame(data_frame = None, collection = None, survey = None, table = None):
    assert data_frame is not None
    assert collection is not None
    assert survey is not None
    try:
        openfisca_survey_collection = SurveyCollection.load(collection = collection)
    except Exception as e:
        openfisca_survey_collection = SurveyCollection(name = collection)

    log.debug("In collection {} the following survey are present: {}".format(collection, openfisca_survey_collection.surveys))
    output_data_directory = openfisca_survey_collection.config.get('data', 'output_directory')
    if table is None:
        table = "input"
    #
    survey_name = survey
    hdf5_file_path = os.path.join(os.path.dirname(output_data_directory), "{}.h5".format(survey_name))
    available_survey_names = [survey_.name for survey_ in openfisca_survey_collection.surveys]
    if survey_name in available_survey_names:
        survey = openfisca_survey_collection.get_survey(survey_name)
    else:
        survey = Survey(name = survey_name, hdf5_file_path = hdf5_file_path)
    survey.insert_table(name = table, data_frame = data_frame)
    openfisca_survey_collection.surveys.append(survey)
    collections_directory = openfisca_survey_collection.config.get('collections', 'collections_directory')
    json_file_path = os.path.join(collections_directory, '{}.json'.format(collection))
    log.debug("In collection {} the following surveyx are present: {}".format(collection, openfisca_survey_collection.surveys))
    openfisca_survey_collection.dump(json_file_path = json_file_path)

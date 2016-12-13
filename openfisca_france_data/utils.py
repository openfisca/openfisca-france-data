# -*- coding: utf-8 -*-


import logging
import numpy
import os
from pandas import Series

import openfisca_france
from openfisca_survey_manager.survey_collections import SurveyCollection
from openfisca_survey_manager.surveys import Survey
from openfisca_france_data import default_config_files_directory as config_files_directory


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
    '''
    Assert if transformed variables are in correct range
    wrange is a list like [minimum, maximum]
    '''
    temp = (table[table[name].notnull()])
    range_1 = wrange[0]
    range_2 = wrange[1]
    for v in temp[name]:
        assert v in range(range_1, range_2), 'some non-null values for %s not in wanted %s: %s' % (
            name, str(wrange), str(v))


def control(dataframe, verbose = False, verbose_columns = None, debug = False, verbose_length = 5, ignore = None):
    """
    Function to help debugging the data crunchin' files.

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
        except:
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
    '''Counts the number of Na's in a specified axis'''
    print("count of NA's for %s is %s" % (name, str(sum(table[name].isnull()))))


def id_formatter(dataframe, entity_id):
    dataframe[entity_id + "_original"] = dataframe[entity_id].copy()
    id_unique = dataframe[entity_id].unique()
    new_id_by_old_id = dict(zip(id_unique, range(len(id_unique))))
    dataframe[entity_id].replace(to_replace = new_id_by_old_id, inplace = True)
    return dataframe


def print_id(df):
    try:
        log.info("Individus with distinc noindiv: {} / {}".format(len(df.noindiv), len(df)))
    except:
        log.info("No noindiv")

    try:
        # Ici, il doit y avoir autant de vous que d'idfoy
        log.info("Individus dans les Foyers: {} \n".format(len(df.idfoy)))
        log.info(df["quifoy"].value_counts(dropna=False))
        if df["idfoy"].isnull().any():
            log.info("NaN in idfoy : {}".format(df["idfoy"].isnull().sum()))
        if df["quifoy"].isnull().any():
            log.info("NaN in quifoy : {}".format(df["quifoy"].isnull().sum()))
    except:
        log.info("No idfoy or quifoy")

    try:
        # Ici, il doit y avoir autant de quimen = 0 que d'idmen
        log.info(u"Individus dans les Ménages {} \n".format(len(df.idmen)))
        log.info("\n" + str(df["quimen"].value_counts(dropna=False)))
        if df["idmen"].isnull().any():
            log.info("NaN in idmen : {} ".format(df["idmen"].isnull().sum()))
        if df["quimen"].isnull().any():
            log.info("NaN in quimen : {} ".format(df["quimen"].isnull().sum()))
    except:
        print("No idmen or quimen")

    try:
        # Ici, il doit y avoir autant de quifam = 0 que d'idfam
        log.info("Individus dans les Familles {}\n".format(len(df.idfam)))
        log.info(df["quifam"].value_counts(dropna=False))
        if df["idfam"].isnull().any():
            log.info("NaN in idfam : {} ".format(df["idfam"].isnull().sum()))
        if df["quifam"].isnull().any():
            log.info("NaN in quifam : {} ".format(df["quifam"].isnull().sum()))
    except:
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
    tax_benefit_system = openfisca_france.FranceTaxBenefitSystem()
    cerfa_fields_by_column_name = dict()
    for name, column in tax_benefit_system.column_by_name.iteritems():
        for section_cerfa in sections_cerfa:
            if name.startswith('f{}'.format(section_cerfa)):
                start = column.start or None
                end = column.end or None
                if (start is None or start.year <= year) and (end is None or end.year >= year):
                    if column.entity.key == 'individu':
                        cerfa_field = ['f' + x.lower().encode('ascii', 'ignore') for x in column.cerfa_field.values()]
                    elif column.entity.key == 'foyer_fiscal':
                        cerfa_field = ['f' + column.cerfa_field.lower().encode('ascii', 'ignore')]
                    cerfa_fields_by_column_name[name.encode('ascii', 'ignore')] = cerfa_field
    return cerfa_fields_by_column_name


def rectify_dtype(dataframe, verbose = True):
    series_to_rectify = []
    rectified_series = []
    for serie_name, serie in dataframe.iteritems():
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


def normalizes_roles_in_entity(dataframe, entity_suffix):
    entity_id_name = 'id' + entity_suffix
    entity_role_name = 'qui' + entity_suffix
    dataframe.set_index('noindiv', inplace = True, verify_integrity = True)
    test1 = dataframe.loc[dataframe[entity_role_name] >= 2, [entity_id_name, entity_role_name]].copy()
    test1.loc[:, entity_role_name] = 2
    j = 2
    while any(test1.duplicated([entity_id_name, entity_role_name])):
        test1.loc[test1.duplicated([entity_id_name, entity_role_name]), entity_role_name] = j + 1
        j += 1
    dataframe.update(test1)
    dataframe.reset_index(inplace = True)
    dataframe[entity_role_name] = dataframe[entity_role_name].astype('int')
    assert_dtype(dataframe[entity_role_name], 'int')
    return dataframe.copy()


def set_variables_default_value(dataframe, year):
    import openfisca_france
    tax_benefit_system = openfisca_france.FranceTaxBenefitSystem()

    for column_name, column in tax_benefit_system.column_by_name.iteritems():
        if column_name in dataframe.columns:
            dataframe[column_name].fillna(column.default, inplace = True)
            dataframe[column_name] = dataframe[column_name].astype(column.dtype)


def store_input_data_frame(data_frame = None, collection = None, survey = None):
    assert data_frame is not None
    assert collection is not None
    assert survey is not None
    openfisca_survey_collection = SurveyCollection(name = collection, config_files_directory = config_files_directory)
    output_data_directory = openfisca_survey_collection.config.get('data', 'output_directory')
    survey_name = survey
    table = "input"
    hdf5_file_path = os.path.join(os.path.dirname(output_data_directory), "{}.h5".format(survey_name))
    survey = Survey(
        name = survey_name,
        hdf5_file_path = hdf5_file_path,
        )
    survey.insert_table(name = table, data_frame = data_frame)
    openfisca_survey_collection.surveys.append(survey)
    collections_directory = openfisca_survey_collection.config.get('collections', 'collections_directory')
    json_file_path = os.path.join(collections_directory, 'openfisca_erfs_fpr.json')
    openfisca_survey_collection.dump(json_file_path = json_file_path)

import click
import ipdb as pdb
import logging
import pandas as pd
import sys
import yaml

from pandas.api.types import is_datetime64_any_dtype as is_datetime
from openfisca_core.model_api import ETERNITY


from openfisca_france_data import france_data_tax_benefit_system
from openfisca_france_data.erfs_fpr import original_id_by_entity
from openfisca_france_data.erfs_fpr.scenario import ErfsFprSurveyScenario
from openfisca_france_data.erfs_fpr.comparison import ErfsFprtoInputComparator
from openfisca_france_data.erfs_fpr.get_survey_scenario import variables_converted_to_annual


tax_benefit_system = france_data_tax_benefit_system
openfisca_variables_by_entity = dict(
    (
        entity.key,
        [variable_name for variable_name, variable in tax_benefit_system.variables.items() if variable.entity.key == entity.key],
        )
    for entity in tax_benefit_system.entities
    )

id_variable_by_entity_key = ErfsFprSurveyScenario.id_variable_by_entity_key
weight_variable_by_entity = ErfsFprSurveyScenario.weight_variable_by_entity


renaming_variables_to_annual = {
    monthly_variable: f"{monthly_variable}_annuel"
    for monthly_variable in variables_converted_to_annual
    }

def build_test(period, noindiv, target_variables = None):
    if target_variables is None:
        target_variables = ErfsFprtoInputComparator.default_target_variables

    comparator = ErfsFprtoInputComparator()
    comparator.period = period
    input_dataframe_by_entity, target_dataframe_by_entity = comparator.get_test_dataframes(rebuild = True, noindivs = [noindiv])

    def convert_date_to_sting(dataframe):
        date_columns = list(dataframe.select_dtypes(include=["datetime64"]))
        dataframe[date_columns] = dataframe[date_columns].astype(str)

    def remove_non_openfisca_columns(dataframe):
        openfisca_variables = set(sum([list(value) for value in openfisca_variables_by_entity.values()], [])).union(set(["noindiv", "idmen_original"]))
        selected_variables = list(set(dataframe.columns).intersection(openfisca_variables))
        return dataframe[selected_variables]

    def build_test_dict(dataframe_by_entity, renaming_variables_to_annual = None):
        input_by_entity = dict()
        for entity, dataframe in dataframe_by_entity.items():
            convert_date_to_sting(dataframe)
            identifier = "noindiv" if entity == "individu" else "idmen_original"
            entity_plural = "individus" if entity == "individu" else "menages"
            input_by_entity[entity_plural] = input = dict()
            dataframe[identifier] = "id_" + dataframe[identifier].astype(str)
            df = remove_non_openfisca_columns(dataframe).set_index(identifier)
            for row, series in df.iterrows():
                series.drop(
                    (
                        list(weight_variable_by_entity.values())
                        + list(id_variable_by_entity_key.values())
                        + list(original_id_by_entity.values())
                        ),
                    inplace = True,
                    errors = "ignore",
                    )
                if renaming_variables_to_annual:
                    series.rename(renaming_variables_to_annual, inplace = True)
                input[row] = series.dropna().to_dict()

        return input_by_entity

    input_by_entity = build_test_dict(input_dataframe_by_entity)
    output_by_entity = build_test_dict(target_dataframe_by_entity, renaming_variables_to_annual)

    relative_error_margin = {
        "default": 5e-3,
        }
    test = dict(
        name = f"Observation {noindiv} on {period}",
        reforms = "openfisca_france_data.erfs_fpr.get_survey_scenario.erfs_fpr_plugin",
        max_spiral_loops = 4,
        relative_error_margin = relative_error_margin,
        period = period,
        input = input_by_entity,
        output = output_by_entity,
        )
    return test



def export_test_file(period, noindiv, test_case_name = None):
    """
    Export a erfs-fpr input and output to an OpenFisca test case.

    Args:
        period (int): simulation year
        noindiv (int): individu id number
        test_case_name (str, optional): _description_. Defaults to Name of the test case file. Defaults to 'test_case_erfs_fpr_NOINDIV'.
    """
    if test_case_name is None:
        test_case_name = f"test_case_erfs_fpr_{noindiv}"

    test_case_file_path = f'{test_case_name}.yaml'
    test = build_test(period, noindiv)

    with open(test_case_file_path, 'w') as file:
        yaml.dump(test, file, sort_keys=False)

    text = get_erfs_fpr_data_as_comment(noindiv)

    with open(test_case_file_path, "a+") as file:
        _ = file.read()  # this auto closes the file after reading, which is a good practice
        file.write(text)


def get_erfs_fpr_data_as_comment(noind):
    return "# Blabal"


@click.command()
@click.option('-n', '--noindiv', type = int, help = "Individual id number", required = True)
@click.option('-v', '--verbose', is_flag = True, default = False, help = "Increase output verbosity", show_default = True)
@click.option('-d', '--debug', is_flag = True, default = False, help = "Use python debugger", show_default = True)
def create_test(noindiv = 0, verbose = False, debug = False):
    """Create test case for a specific ERFS FPR individual."""
    assert noindiv != 0, "Provide valid individual"
    logging.basicConfig(level = logging.DEBUG if verbose else logging.WARNING, stream = sys.stdout)
    from openfisca_france_data.erfs_fpr import REFERENCE_YEAR
    period = REFERENCE_YEAR
    try:
        export_test_file(period, noindiv)
    except Exception as e:
        if debug:
            pdb.post_mortem(sys.exc_info()[2])
        raise e


if __name__ == "__main__":
    sys.exit(create_test())

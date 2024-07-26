import datetime
import dtale
try:
    import ipdb as pdb
except ImportError:
    import pdb
import logging
from math import ceil
import numpy as np
from pathlib import Path, PurePath
import pandas as pd
import pypandoc
import seaborn as sns
import sys


from openfisca_core import periods

from openfisca_france_data.config import config
from openfisca_france_data.erfs_fpr.get_survey_scenario import get_survey_scenario


log = logging.getLogger(__name__)


def get_entity_original_id(survey_scenario, variable):
    entity = survey_scenario.tax_benefit_systems['baseline'].variables[variable].entity.key
    return "noindiv" if entity == "individu" else "idmen_original"


def compute_result(variable, survey_scenario, target_dataframe):
    result = None
    stats = None
    entity = survey_scenario.tax_benefit_systems['baseline'].variables[variable].entity.key
    entity_original_id = get_entity_original_id(survey_scenario, variable)
    output_variables = [entity_original_id, variable]
    entity_dataframe = survey_scenario.create_data_frame_by_entity(
        variables = output_variables,
        )[entity]
    target = target_dataframe[output_variables].rename(columns = {variable: f"target_{variable}"})

    if f"target_{variable}" not in target:
        return None, None

    result = entity_dataframe.merge(
        target,
        on = entity_original_id,
        how = "outer",
        )

    result[f"diff_{variable}"] = result[variable] - result[f"target_{variable}"]
    result_variables = [entity_original_id, variable, f"diff_{variable}", f"target_{variable}"]
    stats = compute_error_stats(result, variable, entity_original_id = entity_original_id)
    return result, stats


def compute_confidence_interval(data, variable, width = .9, entity_original_id = None):
    """
    Compute confidence interval

    Args:
        data (pandas.DataFrame): The data
        variable (str, optional): The variable name. Defaults to None.
        width (float, optional): Witdh of the symmetruc confidence interval. Defaults to .9.

    Returns:
        [type]: [description]
    """
    assert entity_original_id is not None
    df = pd.DataFrame({
        "signed_values": data[variable].values,
        "noind": data[entity_original_id].values
        })
    df["abs_values"] = df.signed_values.abs()
    in_range_obs = ceil(width * len(df))
    sorted_df = df.sort_values("abs_values")
    in_range_values = sorted_df[:in_range_obs]["signed_values"]
    left = in_range_values.min()
    right = in_range_values.max()
    largest_errors = sorted_df[in_range_obs:].copy().sort_values("abs_values", ascending = False)[["signed_values", "abs_values", "noind"]].copy()

    return left, right, largest_errors


def compute_error_stats(data, variable, entity_original_id):
    assert entity_original_id is not None
    numerical = (
        isinstance(data[variable].values.flat[0], np.integer)
        or isinstance(data[variable].values.flat[0], np.floating)
        )
    if not numerical:
        return

    df = data.loc[
        (data[variable].values != 0.0) | (data[f"target_{variable}"].values != 0.0),
        [variable, f"target_{variable}", entity_original_id]
        ].copy()
    df["relative_error"] = (df[variable] - df[f"target_{variable}"]) / (df[f"target_{variable}"] + (df[f"target_{variable}"] == 0.0) * df[variable])
    if df.empty:
        return

    left, right, largest_errors = compute_confidence_interval(df, "relative_error", entity_original_id = entity_original_id)
    less_than_5_pc_error = (df["relative_error"].abs() <= .05).sum() / len(df)
    less_than_20_pc_error = (df["relative_error"].abs() <= .2).sum() / len(df)
    more_than_80_pc_error = (df["relative_error"].abs() >= .8).sum() / len(df)
    return pd.DataFrame.from_dict({
        "variable": [variable],
        "size": [len(data)],
        "share": [len(df) / len(data)],
        "< 5%": [less_than_5_pc_error],
        "< 20%": [less_than_20_pc_error],
        "> 80%": [more_than_80_pc_error],
        "CI (10%)": [[round(left, 2), round(right, 2)]],
        }).round(2)


def create_output_files(markdown_sections, figures_directory, filename):
    header = r"""---
header-includes:
- \usepackage{caption}
- \usepackage{subcaption}
---
"""
    markdown_sections_joined = header + "".join(markdown_sections)
    with open(PurePath.joinpath(figures_directory, "variables.md"), "w", encoding = "utf-8") as markdown_file:
        markdown_file.write(markdown_sections_joined)

    pypandoc.convert_file(
        str(PurePath.joinpath(figures_directory, "variables.md")),
        "pdf",
        format = "markdown",
        outputfile = str(PurePath.joinpath(figures_directory, f"{filename}.pdf")),
        extra_args = ['--pdf-engine=pdflatex'],
        )


def create_variable_distribution_figures(variable, result, bins = None, figures_directory = None, entity_original_id = None):
    assert entity_original_id is not None
    log.debug(f"create_variable_distribution_figures: Examining {variable}")
    assert figures_directory is not None
    if bins is None:
        bins = 100

    non_both_zeroes = (result[f"{variable}"].fillna(0) != 0) | (result[f"target_{variable}"].fillna(0) != 0)
    non_both_zeroes_count = sum(non_both_zeroes)
    both_zeroes_count = len(result) - non_both_zeroes_count

    melted = result.loc[
        non_both_zeroes,
        [entity_original_id, variable, f"target_{variable}"]
        ].melt(
            id_vars = [entity_original_id],
            value_vars = [f"{variable}", f"target_{variable}"]
            )

    if melted.empty:
        print(f"Cannot create variable_distribution_figures for variable = {variable} because all null values")
        return False

    unique_values_count = melted["value"].nunique()

    bins = unique_values_count if unique_values_count < bins else bins
    print(f"create_variable_distribution_figures (total): variable = {variable}, bins = {bins}")

    melted["value"] = melted["value"].clip(1, melted["value"].max())

    log_scale = bins > 10

    sns_plot = sns.histplot(
        data = melted,
        # palette = "crest",
        alpha = .5,
        bins = bins,
        common_bins = True,
        common_norm = False,
        fill = True,
        hue = "variable",
        linewidth = 0,
        x = "value",
        log_scale = log_scale,
        )

    sns_plot.annotate(
        f"Dropping {both_zeroes_count} null observations ({round(100 * both_zeroes_count / (both_zeroes_count + non_both_zeroes_count))}  %)",
        xy = (0, 1),
        xycoords = "axes fraction",
        xytext = (5, -5),
        textcoords = "offset points",
        ha = "left",
        va = "top"
        )
    filename = f"{variable}.pdf"
    sns_plot.figure.savefig(PurePath.joinpath(figures_directory, filename))
    sns_plot.figure.clf()

    return True


def create_variable_markdown_section(variable, stats, figures_directory):
    if stats is None:
        return None

    variable_pdf_path = PurePath.joinpath(figures_directory, f"{variable}.pdf")

    markdown_section = f"""
## Variable `{variable}`


### Valeurs

![]({variable_pdf_path})

### En niveau

![]({PurePath.joinpath(figures_directory, f"diff_{variable}.pdf")})


""" + stats.drop("variable", axis = 1).to_markdown(index = False)

    table_ecarts_markdown_path = PurePath.joinpath(figures_directory, f"table_ecarts_{variable}.md")
    stats.drop("variable", axis = 1).to_markdown(table_ecarts_markdown_path, index = False)

    pypandoc.convert_file(
        str(table_ecarts_markdown_path),
        "pdf",
        format = "markdown",
        outputfile = str(PurePath.joinpath(figures_directory, f"table_ecarts_{variable}.pdf")),
        extra_args = ['--pdf-engine=pdflatex'],
        )

    return markdown_section


def create_variable_markdown_summary_section(variable, stats, figures_directory):
    if stats is None:
        return None
    markdown_section = f"""

## Variable `{variable}`

![]({PurePath.joinpath(figures_directory, f"{variable}.pdf")}){{width=50% height=35%}}
![]({PurePath.joinpath(figures_directory, f"diff_{variable}.pdf")}){{width=50% height=35%}}
\\begin{{figure}}[!h]
\\begin{{subfigure}}[t]{{0.5\\textwidth}}
\\caption{{Distributions des valeurs}}
\\end{{subfigure}}
\\hfill
\\begin{{subfigure}}[t]{{0.5\\textwidth}}
\\caption{{Distributions des écarts}}
\\end{{subfigure}}
\\end{{figure}}

"""
    return markdown_section


def create_diff_variable_distribution_figures(variable, result, bins = None, figures_directory = None, entity_original_id = None):
    assert entity_original_id is not None
    numerical = (
        isinstance(result[f"{variable}"].values.flat[0], np.integer)
        or isinstance(result[f"{variable}"].values.flat[0], np.floating)
        )
    if not numerical:
        return

    assert figures_directory is not None
    if bins is None:
        bins = 100

    non_both_zeroes = (result[f"{variable}"].fillna(0) != 0) | (result[f"target_{variable}"].fillna(0) != 0)
    non_both_zeroes_count = sum(non_both_zeroes)
    both_zeroes_count = len(result) - non_both_zeroes_count

    unique_values_count = result[f"diff_{variable}"].nunique()
    bins == unique_values_count if unique_values_count < bins else bins

    data = result.loc[non_both_zeroes]

    if data.empty:
        print(f"Cannot create diff variable_distribution_figures for variable = {variable} because all null values")
        return

    print(f"create_diff_variable_distribution_figures (total): variable = {variable}, bins = {bins}")
    sns_plot = sns.histplot(data, x = f"diff_{variable}", stat = "probability", bins = bins)

    sns_plot.annotate(
        f"Dropping {both_zeroes_count} null observations ({round(100 * both_zeroes_count / (both_zeroes_count + non_both_zeroes_count))}  %)",
        xy = (0, 1),
        xycoords = "axes fraction",
        xytext = (5, -5),
        textcoords = "offset points",
        ha = "left",
        va = "top"
        )
    filename = f"diff_{variable}.pdf"
    sns_plot.figure.savefig(PurePath.joinpath(figures_directory, filename))
    sns_plot.figure.clf()
    return


class AbstractComparator(object):
    name = None
    default_target_variables = None
    filter_expr_by_label = None
    period = None
    messages = list()
    survey_scenario = None

    def __init__(self, period):
        self.period = period
        name = self.get_name()
        assert name is not None and isinstance(name, str)

        figures_directory = Path(config.get("paths", "figures_directory")) / name

        if not figures_directory.exists():
            figures_directory.mkdir(parents = True, exist_ok = True)

        self.figures_directory = figures_directory

    def compute_aggregates_comparison(self, input_dataframe_by_entity = None):
        pass

    def compute_distibution_comparison(self, input_dataframe_by_entity = None):
        pass

    def get_name(self):
        return self.name + "_" + str(self.period)

    def get_test_dataframes(self, rebuild = False, noindivs = None):
        start_time = datetime.datetime.now()
        if not rebuild:
            return self._load_test_dataframes()

        input_dataframe_by_entity, target_dataframe_by_entity = self.compute_test_dataframes()
        log.debug(f"Test data has been processed in {datetime.datetime.now() - start_time}")
        save_start_time = datetime.datetime.now()
        try:
            self._save_test_dataframes(input_dataframe_by_entity, target_dataframe_by_entity)
            log.debug(f"Test data has been saved in {datetime.datetime.now() - save_start_time}")
        except Exception as e:
            log.debug(f"Test data has not been saved because of {e}")
            pass

        if noindivs is not None:
            selected_idmen_original = list(input_dataframe_by_entity["individu"].query(f"noindiv in {noindivs}").idmen_original.unique())[0]
            menage_query = f"idmen_original == {selected_idmen_original}"
            selected_noindivs = list(input_dataframe_by_entity["individu"].query(menage_query).noindiv.unique())

            input_dataframe_by_entity = {
                "individu": input_dataframe_by_entity["individu"].query(f"noindiv in {selected_noindivs}"),
                "menage": input_dataframe_by_entity["menage"].query(menage_query),
                }
            target_dataframe_by_entity = {
                "individu": target_dataframe_by_entity["individu"].query(f"noindiv in {selected_noindivs}"),
                "menage": target_dataframe_by_entity["menage"].query(menage_query),
                }
        return input_dataframe_by_entity, target_dataframe_by_entity

    def compare(self, browse, load, verbose, debug, target_variables = None, period = None, rebuild = False, summary = False, compute_divergence = False):
        """Compare actual data with openfisca-france-data computation."""
        log.setLevel(level = logging.DEBUG if verbose else logging.WARNING)

        if target_variables is not None and isinstance(target_variables, str):
            target_variables = [target_variables]

        assert (target_variables is None) or isinstance(target_variables, list)

        if target_variables is None:
            target_variables = self.default_target_variables

        self.target_variables = target_variables
        if period is not None:
            period = int(period)

        backup_directory = PurePath.joinpath(Path(config.get("paths", "backup")))
        backup_directory.mkdir(parents = True, exist_ok = True)
        name = self.name
        backup_path = PurePath.joinpath(backup_directory, f"{name}_backup.h5")

        if load:
            assert Path.exists(backup_path), f"Backup file {backup_path} doesn't exist"
            shown = pd.read_hdf(
                backup_path,
                'result',
                )
            dtale.show(
                shown,
                open_browser = True,
                subprocess = False,
                )

        try:
            start_time = datetime.datetime.now()
            input_dataframe_by_entity, target_dataframe_by_entity = self.get_test_dataframes(rebuild)

            log.debug(f"Test data has been prepared in {datetime.datetime.now() - start_time}")

            self.compute_aggregates_comparison(
                input_dataframe_by_entity = input_dataframe_by_entity,
                )

            self.compute_distibution_comparison(input_dataframe_by_entity = input_dataframe_by_entity)

            if compute_divergence:
                result_by_variable, markdown_section_by_variable, markdown_summary_section_by_variable = self.compute_divergence(
                    input_dataframe_by_entity = None,  # To force load the data_table from hdf file
                    target_dataframe_by_entity = target_dataframe_by_entity,
                    target_variables = target_variables,
                    period = period,
                    summary = summary,
                    )

            # Deal with markdown_section

                self.create_report(markdown_section_by_variable, markdown_summary_section_by_variable)

                if result_by_variable is None:
                    return

                result = pd.concat(result_by_variable, ignore_index = True)
            else:
                self.create_report(None,None)

            log.debug(f"Eveyrthing has been computed in {datetime.datetime.now() - start_time}")
            del input_dataframe_by_entity, target_dataframe_by_entity


            if browse:
                start_browsing_time = datetime.datetime.now()
                result = result.dropna(axis = 1, how = 'all')
                matching_variables = ["noindiv"]
                assert set(matching_variables) <= set(result.columns)
                cols_to_use = result.columns.tolist() + matching_variables
                shown = result

                log.debug(f"Data for browsing has been prepared in {datetime.datetime.now() - start_browsing_time}")

                dtale.show(
                    shown,
                    open_browser = True,
                    subprocess = False,
                    )

                assert backup_directory.exists()
                shown.to_hdf(
                    backup_path,
                    'result',
                    mode = "w",
                    format = "table",
                    )

        except Exception as error:
            if debug:
                print(error)
                pdb.post_mortem(sys.exc_info()[2])
            raise error

    def compute_divergence(self, input_dataframe_by_entity, target_dataframe_by_entity,
            target_variables = None, period = None, summary = False):
        """
        Compare openfisca-france-data computation with data targets.

        Args:
            input_dataframe_by_period (dict): Input data
            target_dataframe_by_period (dict): Targets to macth
            figures_directory (path): Where to store the figures
        """
        figures_directory = self.figures_directory.resolve()
        assert Path.exists(figures_directory)

        if target_variables is None:
            log.info(f"No target variables. Exiting divergence computation.")
            return None, None, None

        data = (
            dict(input_dataframe_by_entity = input_dataframe_by_entity)
            if input_dataframe_by_entity is not None
            else None
            )

        survey_scenario = self.get_survey_scenario(
            data = data
            )

        tax_benefit_system = survey_scenario.tax_benefit_systems['baseline']
        markdown_section_by_variable = dict()
        markdown_summary_section_by_variable = dict()
        stats_by_variable = dict()
        result_by_variable = dict()

        for variable in target_variables:
            if variable == 'noind':
                continue

            entity = tax_benefit_system.variables[variable].entity.key
            target_dataframe = target_dataframe_by_entity[entity]
            print(  target_dataframe.columns)
            assert variable in target_dataframe
            log.debug(f"Testing final only variable: {variable}")
            result, stats = compute_result(
                variable,
                survey_scenario,
                target_dataframe,
                )

            result_by_variable[variable] = result
            variable_distribution_figures_created = create_variable_distribution_figures(
                variable,
                result,
                figures_directory = figures_directory,
                entity_original_id = get_entity_original_id(survey_scenario, variable),
                )
            diff_variable_distribution_figures_created = create_diff_variable_distribution_figures(
                variable,
                result,
                figures_directory = figures_directory,
                entity_original_id = get_entity_original_id(survey_scenario, variable)
                )
            stats_by_variable[variable] = stats

            variable_markdown_section = create_variable_markdown_section(
                variable,
                stats,
                figures_directory,
                )

            if variable_markdown_section is not None:
                markdown_section_by_variable[variable] = variable_markdown_section

            if summary:
                variable_markdown_summary_section = create_variable_markdown_summary_section(
                    variable,
                    stats,
                    figures_directory,
                    )
                if variable_markdown_summary_section is not None:
                    markdown_summary_section_by_variable[variable] = variable_markdown_summary_section

        return result_by_variable, markdown_section_by_variable, markdown_summary_section_by_variable

    def compute_test_dataframes(self):
        NotImplementedError

    def create_report(self, markdown_section_by_variable, markdown_summary_section_by_variable):
        figures_directory = self.figures_directory

        if self.messages:
            messages_markdown_section = """
Filtres appliqués:

""" + "\n".join(f"- {message}" for message in self.messages) + """
"""
        else:
            messages_markdown_section = ""

        table_agregats_markdown = None
        if PurePath.joinpath(figures_directory, "table_agregats.md").exists():
            with open(figures_directory / "table_agregats.md", "r", encoding = 'utf-8') as table_agregats_md_file:
                table_agregats_markdown = table_agregats_md_file.read()

        distribution_comparison_markdown = None
        if PurePath.joinpath(figures_directory, "distribution_comparison_md").exists():
            with open(figures_directory / "distribution_comparison_md", "r", encoding = 'utf-8') as distribution_comparison_md_file:
                distribution_comparison_markdown = distribution_comparison_md_file.read()

        front_sections = [messages_markdown_section, table_agregats_markdown, distribution_comparison_markdown]
        sections_by_filename = {
            "variables": markdown_section_by_variable,
            "summary_variables": markdown_summary_section_by_variable
            }

        for filename, section_by_variable in sections_by_filename.items():
            if section_by_variable is not None:
                markdown_sections = list(filter(
                    lambda x: x is not None,
                    front_sections + list(section_by_variable.values()),
                    ))
            else:
                markdown_sections = list(filter(
                    lambda x: x is not None,front_sections
                    ))
            create_output_files(
                markdown_sections,
                figures_directory,
                filename,
                )

    def filter(self, data_frame):
        for label, filter_expr in self.filter_expr_by_label.items():
            obs_before = data_frame.noind.nunique()
            selection = (data_frame
                .eval("keep = " + filter_expr)
                .groupby("noindiv")["keep"]
                .transform('all')
                )
            data_frame.drop(data_frame.index[~selection], inplace = True)
            obs_after = data_frame.noind.nunique()
            log_message = f"Applying filter '{label}': dropping {obs_before - obs_after}, keeping {obs_after} observations."
            log.info(log_message)
            self.messages.append(log_message + "\n")

    def get_survey_scenario(self, data = None, survey_name = None):

        if self.survey_scenario is not None:
            return self.survey_scenario

        return get_survey_scenario(
            year = str(self.period),
            data = data,
            survey_name = f'openfisca_erfs_fpr_{self.period}' if survey_name is None else survey_name,
            )

    def _load_test_dataframes(self, noindivs = None, idents = None):
        name = self.get_name()
        backup_directory = PurePath.joinpath(Path(config.get("paths", "backup")))
        backup_path = PurePath.joinpath(backup_directory, f"{name}_test_data.h5")
        assert backup_path.exists(), "Backup data does not exist. Try rebuild option"
        store = pd.HDFStore(backup_path)
        keys = store.keys()
        store.close()
        input_dataframe_by_entity = dict()
        target_dataframe_by_entity = dict()

        entities = ["individu", "menage"]
        for prefix in ["input", "target"]:
            for entity in entities:
                df = pd.read_hdf(backup_path, f'{prefix}_{name}_{entity}')

                if prefix ==  "input":
                    input_dataframe_by_entity[entity] = df
                elif prefix ==  "target":
                    target_dataframe_by_entity[entity] = df

        return input_dataframe_by_entity, target_dataframe_by_entity

    def _save_test_dataframes(self, input_dataframe_by_entity, target_dataframe_by_entity):
        name = self.get_name()
        backup_directory = PurePath.joinpath(Path(config.get("paths", "backup")))
        backup_path = PurePath.joinpath(backup_directory, f"{name}_test_data.h5")
        backup_path.unlink(missing_ok = True)

        for data_frame_by_entity in [input_dataframe_by_entity, target_dataframe_by_entity]:
            if data_frame_by_entity is None:
                continue
            prefix = "target" if id(data_frame_by_entity) == id(target_dataframe_by_entity) else "input"
            for entity, dataframe in data_frame_by_entity.items():
                if dataframe is None:
                    continue
                try:
                    dataframe.to_hdf(
                        backup_path,
                        f'{prefix}_{name}_{entity}',
                        )
                except NotImplementedError:
                    dataframe.to_hdf(
                        backup_path,
                        f'{prefix}_{name}_{entity}',
                        format = "table"
                        )

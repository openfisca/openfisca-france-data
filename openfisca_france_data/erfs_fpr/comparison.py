"""Compare openfisca-france-data simulation to erfs-fpr."""


import click
import logging


from openfisca_survey_manager.survey_collections import SurveyCollection
from openfisca_france_data.comparator import AbstractComparator
from openfisca_france_data.erfs_fpr import REFERENCE_YEAR
from openfisca_france_data.erfs_fpr.input_data_builder.step_01_preprocessing import build_table_by_name


log = logging.getLogger(__name__)


openfisca_by_erfs_fpr_variables = {
    "chomage_i": "chomage_imposable",
    "ident": "idmen_original",
    "noindiv": "noindiv",
    "rag_i": "rag",
    "retraites_i": "retraite_imposable",  # TODO: CHECk
    #"rev_fonciers_bruts": "f4ba",
    "ric_i": "ric",
    "rnc_i": "rnc",
    "salaires_i": "salaire_imposable",
    "logt": "statut_occupation_logement",
    "rev_fonciers_bruts": "revenu_categoriel_foncier_menage",
    "rev_valeurs_mobilieres_bruts": "revenus_capitaux_prelevement_forfaitaire_unique_ir_menage",
    "rev_financier_prelev_lib_imputes": "rev_financier_prelev_lib_imputes_menage",
    "ppa": "ppa_menage",
    "nivviem": "niveau_de_vie",
    "prest_fam_autres": "prestations_familiales_autres_menage",
    "prest_fam_petite_enfance": "paje_menage",
    "prest_logement": "aides_logement_menage",
    "prest_precarite_rsa": "rsa_menage",
    "prest_precarite_hand": "aah_menage",
    "prest_precarite_vieil": 'aspa_menage',
    "revdispm": "revenu_disponible",
    "nb_uci": "unites_consommation",
    }


class ErfsFprtoInputComparator(AbstractComparator):
    name = "erfs_fpr"
    period = None
    default_target_variables = [
        "chomage_imposable",
        "loyer",
        "rag",
        "retraite_imposable",
        "ric",
        "rnc",
       "salaire_imposable",
       #"statut_occupation_logement",
        ]

    def compute_test_dataframes(self):
        erfs_fpr_survey_collection = SurveyCollection.load(collection = "erfs_fpr")
        # infer names of the survey and data tables
        assert self.period is not None
        year = int(self.period)
        table_by_name = build_table_by_name(year, erfs_fpr_survey_collection)

        log.debug(f"Loading tables for year {year} [{table_by_name.values()}]")

        # load survey and tables
        survey = erfs_fpr_survey_collection.get_survey(table_by_name['survey'])

        fpr_individu = survey.get_values(table = table_by_name['fpr_individu'], ignorecase = True)
        fpr_menage = survey.get_values(table = table_by_name['fpr_menage'], ignorecase = True)

        openfisca_survey_collection = SurveyCollection.load(collection = "openfisca_erfs_fpr")
        openfisca_survey = openfisca_survey_collection.get_survey(f"openfisca_erfs_fpr_{year}")
        openfisca_individu = openfisca_survey.get_values(table = f"individu_{year}")
        openfisca_menage = openfisca_survey.get_values(table = f"menage_{year}")

        input_dataframe_by_entity = {
            "individu": openfisca_individu,
            "menage": openfisca_menage,
            }

        fpr_menage.loyer = 12 * fpr_menage.loyer

        target_dataframe_by_entity = {
            "individu": fpr_individu.rename(columns = openfisca_by_erfs_fpr_variables),
            "menage": fpr_menage.rename(columns = openfisca_by_erfs_fpr_variables),
            }

        return input_dataframe_by_entity, target_dataframe_by_entity


@click.command()
@click.option('-b', '--browse', is_flag = True, help = "Browse results", default = False, show_default = True)
@click.option('-l', '--load', is_flag = True, default = False, help = "Load backup results", show_default = True)
@click.option('-v', '--verbose', is_flag = True, default = False, help = "Increase output verbosity", show_default = True)
@click.option('-d', '--debug', is_flag = True, default = False, help = "Use python debugger", show_default = True)
@click.option('-p', '--period', default = REFERENCE_YEAR, help = "period(s) to treat", show_default = True)
@click.option('-t', '--target-variables', default = None, help = "target variables to inspect (None means all)", show_default = True)
@click.option('-u', '--rebuild', is_flag = True, default = False, help = "Rebuild test data", show_default = True)
@click.option('-s', '--summary', is_flag = True, default = False, help = "Produce summary figuress", show_default = True)
def compare(browse = False, load = False, verbose = True, debug = True, target_variables = None, period = None, rebuild = False, summary = False):
    """Compare openfisca-france-data simulation to erfs-fpr by generating comparison data and graphs.

    Data can be explored using D-Tale and graphs are saved as pdf files.
    """
    comparator = ErfsFprtoInputComparator(period=period)
    comparator.period = period
    comparator.compare(browse=browse, load=load, verbose=verbose, debug=debug, target_variables=target_variables, period=period, rebuild=rebuild, summary=summary, compute_divergence = True)


import logging
import os
import pyarrow
import click
import datetime
from openfisca_survey_manager.survey_collections import SurveyCollection
from openfisca_france_data.pote.input_data_builder.before_script_pote_sas_to_parquet import pote_sas_to_parquet
from openfisca_france_data.pote.input_data_builder.step_00_variables_pote import create_pote_openfisca_variables_list
from openfisca_france_data.pote.input_data_builder.step_01_create_individus import build_individus
from openfisca_france_data.pote.input_data_builder.step_02_a_create_table_presimulation import create_table_foyer_fiscal_preparation
from openfisca_france_data.pote.input_data_builder.step_02_b_simulation_credits_reductions import simulation_preparation_credits_reductions
from openfisca_france_data.pote.input_data_builder.step_02_c_create_table_foyer_fiscal import create_table_foyer_fiscal
from openfisca_france_data.pote.input_data_builder.analyse_variables import liens_variables
from openfisca_survey_manager.paths import default_config_files_directory

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
# BCO : Il ne faut pas envoyer les logs dans ""../logs" car c'est un dossier qui n'existe pas.
# /tmp à le mérite d'exister sur OSX et Linux mais pas sous Windows. Le mieux est de ne pas utiliser de fichier,
# et de rediriger la sortie console vers un fichier quand on en a besoin.
fileHandler = logging.FileHandler("/tmp/build_pote_{}.log".format(datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")))
fileHandler.setLevel(logging.DEBUG)
log.addHandler(fileHandler)

consoleHandler = logging.StreamHandler()
consoleHandler.setLevel(logging.INFO)
log.addHandler(consoleHandler)
def build_pote_input_data(year=2022,chunk_size=1000000, config_files_directory=default_config_files_directory, taux_non_null = 0.0002, rebuild_from_sas = False):
    """
    Met les données POTE dans un format de données compatible avec une simulation d'openfisca france via un survey scenario (objet d'openfisca survey manager)
    - year : année de POTE utilisé
    - chunk_size : nombre de ligne par morceau de POTE lu. Lecture par bout par contrainte de mémoire sur le CASD
    - config_files_directory : chemin du `.config/openfisca-survey-scenario`. voir dans .gitlab-ci/.gitlab-ci/pote_openfisca_survey_manager_config.ini pour un exemple
    - taux_non_null : taux minimum de valeur non nulle dans une colonne POTE pour qu'elle soit gardée. Toutes les variables ne sont pas gardées par contrainte de mémoire

    Les valeurs par défaut sont celles qui fonctionnent pour une machine avec 12 Go de RAM
    """

    log.info(f"Debut de la préparation de POTE {year} pour Openfisca France")

    survey = SurveyCollection(name = 'raw_pote', config_files_directory = config_files_directory)
    raw_data_directory = survey.config.get('data','raw_pote') # chemin vers la table POTE avec un fichier .parquet par colonne
    output_path = survey.config.get('data','output_directory') # chemin où seront enregistrées les tables finales prêtes pour la simulation
    tmp_directory = survey.config.get('data','tmp_directory')
    errors_path = survey.config.get('openfisca_france_data_pote','errors_path')

    for path in [os.path.join(output_path,"foyer_fiscal"),
                 os.path.join(output_path,"individu"),
                 survey.config.get('collections','collections_directory'),
                 os.path.join(tmp_directory,"tmp_foyer_fiscal"),
                 ]:
        if not os.path.exists(path):
            os.makedirs(path)

    if rebuild_from_sas:
        log.warnings("ATTENTION Vous avez lancé le build à partir de la table sas de POTE. Cela peut prendre plusieurs jours. Si vous avez déjà la table POTE au format parquet vous pouvez passer cette étape")
        sas_data_directory = survey.config.get('data','sas_pote')
        chunks_data_directory = survey.config.get('data','chunks_pote')

        for path in [sas_data_directory, chunks_data_directory]:
            if not os.path.exists(path):
                os.makedirs(path)

        pote_sas_to_parquet(year, sas_data_directory, chunks_data_directory, raw_data_directory)

    logging.basicConfig(filename=f"{errors_path}builder_log.log", encoding = 'utf-8')

    pote_length = pyarrow.parquet.read_table(f"{raw_data_directory}pote_aged.parquet").num_rows
    nrange = pote_length // chunk_size + 1 * (pote_length%chunk_size > 0)

    variables_individu, variables_foyer_fiscal = create_pote_openfisca_variables_list(year, errors_path, raw_data_directory)

    variables_to_compute, enfants_tot, dictionnaire_enfant_parents, dictionnaire_parent_enfants = liens_variables(year)

    build_individus(year, chunk_size, variables_individu, config_files_directory, raw_data_directory, output_path, errors_path, nrange, log)
    create_table_foyer_fiscal_preparation(raw_data_directory, year, output_path, config_files_directory, variables_to_compute, dictionnaire_parent_enfants, tmp_directory, log)
    simulation_preparation_credits_reductions(year,config_files_directory, variables_to_compute, dictionnaire_parent_enfants, tmp_directory, pote_length, log)
    create_table_foyer_fiscal(raw_data_directory, variables_foyer_fiscal, year, output_path, config_files_directory, variables_to_compute, dictionnaire_parent_enfants, tmp_directory, pote_length, taux_non_null, log)

    log.info(f"Fin de la préparation de POTE {year} pour Openfisca France !")

@click.command()
@click.option('-y', '--year', 'year', default = 2022, help = "POTE year")
@click.option('-s', '--chunk_size', 'chunk_size', default = 1000000, help = "chunk size")
@click.option('-c', '--config_files_directory', 'config_files_directory', default = default_config_files_directory, help = "config files directory")
@click.option('-t', '--taux_non_null', 'taux_non_null', default = 0.0002, help = "taux minimum de valeurs non nulle dans la colonne pour la garder dans la simulation")

def main(year=2022,chunk_size=1000000, config_files_directory=default_config_files_directory, taux_non_null = 0.0002):
    build_pote_input_data(year=year,chunk_size=chunk_size, config_files_directory=config_files_directory, taux_non_null=taux_non_null)

if __name__ == '__main__':
    main()

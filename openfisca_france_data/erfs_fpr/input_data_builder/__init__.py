import click
import configparser
import datetime
import logging
import pdb
import sys
import time
import warnings


from openfisca_france_data.erfs_fpr import REFERENCE_YEAR
#from multipledispatch import dispatch  # type: ignore

warnings.filterwarnings("ignore", ".*is an invalid version and will not be supported in a future release.*")

from openfisca_france_data.erfs_fpr.input_data_builder import (
    step_01_preprocessing as preprocessing,
    # step_02_imputation_loyer as imputation_loyer,
    step_02_menage as menage,
    step_03_variables_individuelles as variables_individuelles,
    step_04_famille as famille,
    step_06_final as final,
    )

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

# BCO : Il ne faut pas envoyer les logs dans ""../logs" car c'est un dossier qui n'existe pas.
# /tmp à le mérite d'exister sur OSX et Linux mais pas sous Windows. Le mieux est de ne pas utiliser de fichier,
# et de rediriger la sortie console vers un fichier quand on en a besoin.
fileHandler = logging.FileHandler("/tmp/build_erfs_fpr_{}.log".format(datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")))
fileHandler.setLevel(logging.DEBUG)
log.addHandler(fileHandler)

consoleHandler = logging.StreamHandler()
consoleHandler.setLevel(logging.INFO)
log.addHandler(consoleHandler)


#@dispatch(int)
def build(year: int, export_flattened_df_filepath: str = None) -> None:
    """
    Ici on va nettoyer et formatter les donnés ERFS-FPR, pour les rendre OpenFisca-like
    """

    # Step 01 : le formattage OpenFisca
    #
    # - Formattage des différentes variables
    # - On merge les tables individus / menages
    #
    # Note : c'est ici où on objectivise les hypothèses, step 1
    log.info('\n [[[ Year {} - Step 1 / 5 ]]] \n'.format(year))
    preprocessing.build_merged_dataframes(year = year)

    # Step 02 : Si on veut calculer les allocations logement, il faut faire le matching avec une autre enquête (ENL)
    #
    # openfisca_survey_collection = SurveyCollection(name = 'openfisca')
    # stata_directory = openfisca_survey_collection.config.get('data', 'stata_directory')
    # stata_file = os.path.join(stata_directory, 'log_men_ERFS.dta')
    # imputation_loyer.merge_imputation_loyer(stata_file = stata_file, year = year)
    log.info('\n [[[ Year {} - Step 2 / 5 SKIPPED ]]] \n'.format(year))
    menage.build_variables_menage(year = year)

    # Step 03 : on commence par les variables indivuelles
    log.info('\n [[[ Year {} - Step 3 / 5 ]]] \n'.format(year))
    variables_individuelles.build_variables_individuelles(year = year)

    # Step 04 : ici on va constituer foyer et famille à partir d'invididu et ménage
    #
    # - On fait individu/ménage pour pouvoir faire des familles (foyers sociaux)
    # - On va faire des suppositions pour faire les familles
    # - On va faire les foyers fiscaux à partir des familles
    # - On va faire de suppositions pour faire les foyers fiscaux
    log.info('\n [[[ Year {} - Step 4 / 5 ]]] \n'.format(year))
    famille.build_famille(year = year)

    # Affreux ! On injectait tout dans un même DataFrame !!!
    # C'est très moche !
    #
    # On crée une df par entité par période.
    # Elles sont stockées dans un fichier h5
    log.info('\n [[[ Year {} - Step 5 / 5 ]]] \n'.format(year))
    final.create_input_data_frame(year = year, export_flattened_df_filepath = export_flattened_df_filepath)


@click.command()
@click.option('-y', '--year', default = REFERENCE_YEAR, help = "ERFS-FPR year", show_default = True, type = int, required = True)
@click.option('-f', '--file', 'export_flattened_df_filepath', default = None, help = 'flattened dataframe filepath', show_default = True)
@click.option('-c', '--configfile', default = None, help = 'raw_data.ini path to read years to process.', show_default = True)
@click.option('-l', '--log', 'lg', default = "info", help = 'level of detail for log output.', show_default = True)
@click.option('-d', '--debug', 'debug', is_flag = True, default = False, help = 'debug', show_default = True)
def main(year = None, export_flattened_df_filepath = None, configfile = None, lg = "info", debug = False):
    assert year is not None
    start = time.time()
    # get level of logging
    if lg == "info":
        lgi = logging.INFO
    elif lg == "warn":
        lgi = logging.WARNING
    elif lg == "debug":
        lgi = logging.DEBUG

    logging.basicConfig(stream = sys.stdout, # filename = 'build_erfs_fpr.log', level = lgi,
        format='%(asctime)s - %(name)-12s: %(levelname)s %(module)s - %(funcName)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')

    log.info("Starting build-erfs-fpr [log: {}]".format(lg))

    # Determine which years are to be analyzed, from file if available, else parameter
    if configfile is not None:
        log.info("Reading years to process from {configfile}")
        years = []

        try:
            config = configparser.ConfigParser()
            config.read(configfile)
            for key in config['erfs_fpr']:
                if key.isnumeric():
                    years.append(int(key))
                    # log.info(f"Adding year {int(key)}")
        except KeyError:
            years = [year]
            log.warning(f"Key 'erfs_fpr' not found in {configfile}, switchin to default {years}")

        if len(years) > 1:
            log.info('Configured multiple years: [{}]'.format(';'.join([str(y) for y in years])))
        else:
            log.info('Configured single year: [{}]'.format(years))

        for year in years:
            log.info('Starting with year {}'.format(year))
            try:
                build(year = year, export_flattened_df_filepath = export_flattened_df_filepath)
            except Exception as e:
                log.warning(f" == BUILD HAS FAILED FOR YEAR {year} ==")
                log.warning(f"Error message:\n{str(e)}\nEND OF ERROR MESSAGE\n\n")
                if debug:
                    pdb.post_mortem(sys.exc_info()[2])
                raise e
    else:
        log.info('Configured single year: [{}]'.format(year))
        try:
            build(year = year, export_flattened_df_filepath = export_flattened_df_filepath)
        except Exception as e:
            log.warning(f" == BUILD HAS FAILED FOR YEAR {year} ==")
            log.warning(f"Error message:\n{str(e)}\nEND OF ERROR MESSAGE\n\n")
            if debug:
                pdb.post_mortem(sys.exc_info()[2])
            raise e

    # TODO: create_enfants_a_naitre(year = year)
    log.info("\n\n ==> Script finished after {} seconds.".format(round(time.time() - start)))


if __name__ == '__main__':
    main()

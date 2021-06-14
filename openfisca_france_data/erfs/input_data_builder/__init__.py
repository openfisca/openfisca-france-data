#! /usr/bin/env python
import logging
import os



from openfisca_france_data.erfs.input_data_builder import (  # analysis:ignore
    step_01_pre_processing as pre_processing,
    step_02_imputation_loyer as imputation_loyer,
    step_03_fip as fip,
    step_04_famille as famille,
    step_05_foyer as foyer,
    step_06_rebuild as rebuild,
    step_07_invalides as invalides,
    step_08_final as final,
    )
from openfisca_survey_manager.temporary import get_store

from openfisca_survey_manager.surveys import Survey
from openfisca_survey_manager.survey_collections import SurveyCollection


log = logging.getLogger(__name__)


def build(year = None, check = False):

    assert year is not None
    pre_processing.create_indivim_menagem(year = year)
    pre_processing.create_enfants_a_naitre(year = year)
    #    try:
    #        imputation_loyer.imputation_loyer(year = year)
    #    except Exception, e:
    #        log.info('Do not impute loyer because of the following error: \n {}'.format(e))
    #        pass
    fip.create_fip(year = year)
    famille.famille(year = year)
    foyer.sif(year = year)
    foyer.foyer_all(year = year)
    rebuild.create_totals_first_pass(year = year)
    rebuild.create_totals_second_pass(year = year)
    rebuild.create_final(year = year)
    invalides.invalide(year = year)
    final.final(year = year, check = check)

    temporary_store = get_store(file_name = 'erfs')
    data_frame = temporary_store['input_{}'.format(year)]
    # Saving the data_frame
    openfisca_survey_collection = SurveyCollection(name = "openfisca", config_files_directory = config_files_directory)
    output_data_directory = openfisca_survey_collection.config.get('data', 'output_directory')
    survey_name = "openfisca_data_{}".format(year)
    table = "input"
    hdf5_file_path = os.path.join(os.path.dirname(output_data_directory), "{}.h5".format(survey_name))
    survey = Survey(
        name = survey_name,
        hdf5_file_path = hdf5_file_path,
        )
    survey.insert_table(name = table, data_frame = data_frame)
    openfisca_survey_collection.surveys.append(survey)
    collections_directory = openfisca_survey_collection.config.get('collections', 'collections_directory')
    json_file_path = os.path.join(collections_directory, 'openfisca.json')
    openfisca_survey_collection.dump(json_file_path = json_file_path)

from openfisca_france_data.pote.survey_scenario import PoteSurveyScenario
from openfisca_survey_manager.paths import default_config_files_directory

def test_pote_survey_scenario(period=2022, config_file_directory=default_config_files_directory):
    survey_scenario = PoteSurveyScenario(period = period, config_files_directory=config_file_directory)
    assert survey_scenario.simulations['baseline'].compute_aggregate('irpp_economique', period=period, weighted = False) is not None, "La simulation ne s'est pas bien passée"


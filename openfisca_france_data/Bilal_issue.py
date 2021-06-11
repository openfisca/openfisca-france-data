#In Terminal, cd "INSERT PATH/openfisca-survey-manager/openfisca_survey_manager/scripts" :
# python build_collection.py -c erfs_fpr -d -m -s 2014

#In Python, run this file ("first_tests.py)

from openfisca_france_data import france_data_tax_benefit_system
from openfisca_france_data.erfs_fpr.get_survey_scenario import get_survey_scenario
import sys

sys.argv = ['-y 2014']

# En adaptant le chemin d'accès :
exec(open("INSERT PATH/openfisca-france-data/openfisca_france_data/erfs_fpr/input_data_builder/__init__.py").read())

tax_benefit_system = france_data_tax_benefit_system

survey_scenario = get_survey_scenario(
    tax_benefit_system = tax_benefit_system,
    year = 2014,
    rebuild_input_data = True
    )

survey_scenario.compute_aggregate(variable = 'irpp', period = 2014)

# This works. But then running all of this code for 2015 does not work. After 2015 is built, 
# neither 2015 nor 2014 can be run. I've tried running this code without building. I've tried
# running this code with rebuild_input_data = False (line 21). Each attempt generates an error.

#Error when trying to run without building
    ERROR:openfisca_survey_manager.survey_collections:No option 'erfs_fpr' in section: 'collections'
    Traceback (most recent call last):

    File "/Users/bilalchoho/opt/anaconda3/envs/taxipp/lib/python3.7/configparser.py", line 788, in get
        value = d[option]

    File "/Users/bilalchoho/opt/anaconda3/envs/taxipp/lib/python3.7/collections/__init__.py", line 916, in __getitem__
        return self.__missing__(key)            # support subclasses that define __missing__

    File "/Users/bilalchoho/opt/anaconda3/envs/taxipp/lib/python3.7/collections/__init__.py", line 908, in __missing__
        raise KeyError(key)

    KeyError: 'erfs_fpr'

    During handling of the above exception, another exception occurred:

    Traceback (most recent call last):

    File "/Users/bilalchoho/git_stuff/first_tests.py", line 13, in <module>
        exec(open("/Users/bilalchoho/git_stuff/openfisca-france-data/openfisca_france_data/erfs_fpr/input_data_builder/__init__.py").read())

    File "<string>", line 68, in <module>

    File "<string>", line 32, in build

    File "/Users/bilalchoho/git_stuff/openfisca-survey-manager/openfisca_survey_manager/temporary.py", line 38, in func_wrapper
        return func(*args, temporary_store = temporary_store, **kwargs)

    File "/Users/bilalchoho/git_stuff/openfisca-france-data/openfisca_france_data/erfs_fpr/input_data_builder/step_01_preprocessing.py", line 24, in build_merged_dataframes
        erfs_fpr_survey_collection = SurveyCollection.load(collection = "erfs_fpr")

    File "/Users/bilalchoho/git_stuff/openfisca-survey-manager/openfisca_survey_manager/survey_collections.py", line 104, in load
        json_file_path = config.get("collections", collection)

    File "/Users/bilalchoho/opt/anaconda3/envs/taxipp/lib/python3.7/configparser.py", line 791, in get
        raise NoOptionError(option, section)

    NoOptionError: No option 'erfs_fpr' in section: 'collections'

#Error when you try to run 2015, having already run 2014
    Traceback (most recent call last):

    File "/Users/bilalchoho/git_stuff/first_tests.py", line 13, in <module>
        exec(open("/Users/bilalchoho/git_stuff/openfisca-france-data/openfisca_france_data/erfs_fpr/input_data_builder/__init__.py").read())

    File "<string>", line 68, in <module>

    File "<string>", line 50, in build

    File "/Users/bilalchoho/git_stuff/openfisca-survey-manager/openfisca_survey_manager/temporary.py", line 38, in func_wrapper
        return func(*args, temporary_store = temporary_store, **kwargs)

    File "/Users/bilalchoho/git_stuff/openfisca-france-data/openfisca_france_data/erfs_fpr/input_data_builder/step_04_famille.py", line 99, in build_famille
        skip_enfants_a_naitre = skip_enfants_a_naitre)

    File "/Users/bilalchoho/git_stuff/openfisca-france-data/openfisca_france_data/erfs_fpr/input_data_builder/step_04_famille.py", line 139, in create_familles
        year = year,

    File "/Users/bilalchoho/git_stuff/openfisca-france-data/openfisca_france_data/erfs_fpr/input_data_builder/step_04_famille.py", line 679, in famille_5
        assert not famille.noindiv.duplicated().any()

    AssertionError

#Error when you try to run 2014, having already built 2015
    Traceback (most recent call last):

    File "/Users/bilalchoho/git_stuff/first_tests.py", line 13, in <module>
        exec(open("/Users/bilalchoho/git_stuff/openfisca-france-data/openfisca_france_data/erfs_fpr/input_data_builder/__init__.py").read())

    File "<string>", line 68, in <module>

    File "<string>", line 32, in build

    File "/Users/bilalchoho/git_stuff/openfisca-survey-manager/openfisca_survey_manager/temporary.py", line 38, in func_wrapper
        return func(*args, temporary_store = temporary_store, **kwargs)

    File "/Users/bilalchoho/git_stuff/openfisca-france-data/openfisca_france_data/erfs_fpr/input_data_builder/step_01_preprocessing.py", line 28, in build_merged_dataframes
        survey = erfs_fpr_survey_collection.get_survey(f"erfs_fpr_{year}")

    File "/Users/bilalchoho/git_stuff/openfisca-survey-manager/openfisca_survey_manager/survey_collections.py", line 94, in get_survey
        survey_name, self.name, available_surveys_names)

    AssertionError: Survey erfs_fpr_2014 cannot be found for survey collection erfs_fpr.
    Available surveys are :['erfs_fpr_2015']

#If you rebuild 2014 after having built 2015, this time you can run 2014
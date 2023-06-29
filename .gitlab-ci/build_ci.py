"""
Create the file `.gitlab-ci.yml` that is read by Gitlab Runner to execute the CI.

Run in project root folder:

python .gitlab-ci/build_ci.py
"""
import configparser
import yaml

# Config file use to get the available years
CONFIG = "./.gitlab-ci/openfisca_survey_manager_raw_data.ini"


def header():
    return """
################################################
# GENERATED FILE, DO NOT EDIT
# Please visit .gitlab-ci/README.md
################################################

"""


def build_input_data(year: str, stage: str = "build_input_data_all"):
    if stage == "build_input_data_all":
        prefix = "in_dt-"
    else:
        prefix = "input_data-"
    step = {
        prefix
        + year: {
            "stage": stage,
            "image": "$CI_REGISTRY_IMAGE:latest",
            "tags": ["openfisca"],
            "script": [
                'echo "build_input_data-' + year + '"',
                "mkdir -p $ROOT_FOLDER/$OUT_FOLDER",
                # Put the config from build collections step
                "cp $ROOT_FOLDER/$OUT_FOLDER/openfisca_survey_manager_config-after-build-collection.ini ~/.config/openfisca-survey-manager/config.ini",
                f"build-erfs-fpr -y {year} -f $ROOT_FOLDER/$OUT_FOLDER/data_output/erfs_flat_{year}.h5",
                "cp ~/.config/openfisca-survey-manager/config.ini $ROOT_FOLDER/$OUT_FOLDER/openfisca_survey_manager_config_input_data-after-build-erfs-fprs-"
                    + year
                    + ".ini",
            ],
        }
    }
    if stage == "build_input_data_all":
        step[prefix + year]["needs"] = ["run_on_all_years"]
    return step


def aggregates(year, stage: str = "aggregates_all", env = False):
    if stage == "aggregates_all":
        prefix = "agg-"
        prefix_input_data = "in_dt-"
    else:
        prefix = "aggregates-"
        prefix_input_data = "input_data-"
    entry = {
        prefix
        + year: {
            "stage": stage,
            "image": "$CI_REGISTRY_IMAGE:latest",
            "needs": [prefix_input_data + year],
            "tags": ["openfisca"],
            "script": [
                'echo "aggregates-' + year + '"',
                f"cp $ROOT_FOLDER/$OUT_FOLDER/openfisca_survey_manager_config_input_data-after-build-erfs-fprs-{year}.ini ~/.config/openfisca-survey-manager/config.ini",
                f"python tests/erfs_fpr/integration/test_aggregates.py --year {year}",
                "mkdir -p $ROOT_FOLDER/$OUT_FOLDER",
                "cp ./*.html $ROOT_FOLDER/$OUT_FOLDER/data_output",
                "cp ./*.csv $ROOT_FOLDER/$OUT_FOLDER/data_output",
            ],
            "artifacts": {"paths": ["./*.csv"]},
            }
        }

    if env:
        entry[prefix + year]["environment"] = {
            "name": f"Aggregates {year}",
            "url": f"https://git.leximpact.dev/benjello/openfisca-france-data/-/jobs/$CI_JOB_ID/artifacts/file/aggregates_erfs_fpr_{year}.csv",
            }

    return entry

# Warning : not used yet : test are independant for now.
def make_test_by_year(year):
    return {
        "test-"
        + year: {
            "stage": "test",
            "image": "$CI_REGISTRY_IMAGE:latest",
            "needs": ["agg-" + year],
            "tags": ["openfisca"],
            "script": [
                f"cp $ROOT_FOLDER/$OUT_FOLDER/openfisca_survey_manager_config_input_data-after-build-erfs-fprs-{year}.ini ~/.config/openfisca-survey-manager/config.ini",
                "make test",
            ],
        }
    }


def get_erfs_years():
    """
    Read raw_data.ini to find all available years.
    """
    years = []
    try:
        config = configparser.ConfigParser()
        config.read(CONFIG)
        for key in config["erfs_fpr"]:
            if key.isnumeric():
                years.append(key)
        return years
    except KeyError:
        print(f"Key 'erfs_fpr' not found in {configfile}, switchin to default {years}")
        raise KeyError


def build_gitlab_ci(erfs_years):
    gitlab_ci = header()
    # gitlab_ci += yaml.dump(make_test())
    # gitlab_ci += yaml.dump(build_and_deploy_conda_package())
    # gitlab_ci += yaml.dump(build_collections())
    gitlab_ci += yaml.dump(build_input_data("2019", stage="build_input_data"))
    gitlab_ci += yaml.dump(aggregates("2019", stage="aggregates", env = True))
    gitlab_ci += yaml.dump(build_input_data("2018", stage="build_input_data"))
    gitlab_ci += yaml.dump(aggregates("2018", stage="aggregates", env = True))

    for year in erfs_years:
        print("\t ERFS : Building for year", year)
        gitlab_ci += yaml.dump(build_input_data(year))
        gitlab_ci += yaml.dump(aggregates(year))
    # gitlab_ci += yaml.dump(build_conda_package())
    return gitlab_ci


def main():
    print("Reading survey manager config...")
    erfs_years = get_erfs_years()
    # For testing only some years
    # erfs_years = ["2016", "2017", "2018"]
    gitlab_ci = build_gitlab_ci(erfs_years)
    with open(r"./.gitlab-ci/all_years_build_and_aggregates.yml", mode="w") as file:
        file.write(gitlab_ci)
    print("Done with success!")


main()

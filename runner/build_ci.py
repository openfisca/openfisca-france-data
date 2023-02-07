"""
Create the file `.gitlab-ci.yml` that is read by Gitlab Runner to execute the CI.

Run in project root folder:

python runner/build_ci.py
"""
import configparser
import yaml

# Config file use to get the available years
CONFIG = "./runner/openfisca_survey_manager_raw_data.ini"


def header():
    return """
################################################
# GENERATED FILE, DO NOT EDIT
# Please visit runner/README.md
################################################

variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"
  CI_REGISTRY: https://index.docker.io/v1/
  CI_REGISTRY_IMAGE: leximpact/openfisca-france-data
  # OUT_FOLDER: "$CI_COMMIT_REF_NAME-$CI_COMMIT_SHORT_SHA" # For branch-commit_id
  OUT_FOLDER: "$CI_COMMIT_REF_NAME" # For just branch
  ROOT_FOLDER: "/mnt/data-out/openfisca-france-data"

cache:
  paths:
    - .cache/pip
    - ./figures/

stages:
  - docker
  - test
  - anaconda
  - build_collection
  - build_input_data
  - aggregates


before_script:
  # To be sure we are up to date even if we do not rebuild docker image
  - make install
  - cp ./runner/openfisca_survey_manager_raw_data.ini ~/.config/openfisca-survey-manager/raw_data.ini
  - echo "End of before_script"

build docker image:
  stage: docker
  tags:
    - openfisca
  image:
    name: gcr.io/kaniko-project/executor:debug
    entrypoint: [""]
  # Prevent call of before_script because it will fail in this context
  before_script:
    - ''
  script:
    # From https://github.com/GoogleContainerTools/kaniko#pushing-to-docker-hub
    - DOCKER_HUB_AUTH=$(echo -n $DOCKER_HUB_USER:$DOCKER_HUB_PASSWORD | base64)
    - echo "{\\"auths\\":{\\"$CI_REGISTRY\\":{\\"auth\\":\\"$DOCKER_HUB_AUTH\\"}}}" > /kaniko/.docker/config.json
    - /kaniko/executor --context $CI_PROJECT_DIR --dockerfile $CI_PROJECT_DIR/docker/Dockerfile --destination $CI_REGISTRY_IMAGE:latest
  # Build Docker is needed only if code as changed.
  when: manual

"""


def build_collections():
    build_collection = {
        "build_collection": {
            "stage": "build_collection",
            "image": "$CI_REGISTRY_IMAGE:latest",
            "tags": ["openfisca"],
            "script": [
                'echo "Begin with fresh config"',
                "mkdir -p $ROOT_FOLDER/data_collections/$OUT_FOLDER/",
                "rm $ROOT_FOLDER/data_collections/$OUT_FOLDER/*.json || true",  # || true to ignore error
                "cp ./runner/openfisca_survey_manager_config.ini ~/.config/openfisca-survey-manager/config.ini",
                'echo "Custom output folder"',
                'sed -i "s/data_collections/data_collections\/$OUT_FOLDER\//" ~/.config/openfisca-survey-manager/config.ini',
                "cat ~/.config/openfisca-survey-manager/config.ini",
                "#build-collection -c enquete_logement -d -m -s 2013",
                "build-collection -c erfs_fpr -d -m -v",
                'echo "Backup updated config"',
                "cp ~/.config/openfisca-survey-manager/config.ini $ROOT_FOLDER/openfisca_survey_manager_config-after-build-collection.ini",
            ],
            "when": "manual",
        }
    }
    return build_collection


def build_input_data(year):
    return {
        "in_dt-"
        + year: {
            "stage": "build_input_data",
            "image": "$CI_REGISTRY_IMAGE:latest",
            # Remove needs because it prevent execution if build_collection is in manual
            #'needs': ['build_collection'],
            "tags": ["openfisca"],
            "script": [
                'echo "build_input_data-' + year + '"',
                "mkdir -p $ROOT_FOLDER/$OUT_FOLDER",
                # Put the config from build collections step
                "cp $ROOT_FOLDER/openfisca_survey_manager_config-after-build-collection.ini ~/.config/openfisca-survey-manager/config.ini",
                f"build-erfs-fpr -y {year} -f $ROOT_FOLDER/$OUT_FOLDER/erfs_flat_{year}.h5",
                "cp ~/.config/openfisca-survey-manager/config.ini $ROOT_FOLDER/openfisca_survey_manager_config_input_data-after-build-erfs-fprs-"
                + year
                + ".ini",
            ],
        }
    }


def aggregates(year):
    return {
        "agg-"
        + year: {
            "stage": "aggregates",
            "image": "$CI_REGISTRY_IMAGE:latest",
            "needs": ["in_dt-" + year],
            "tags": ["openfisca"],
            "script": [
                'echo "aggregates-' + year + '"',
                f"cp $ROOT_FOLDER/openfisca_survey_manager_config_input_data-after-build-erfs-fprs-{year}.ini ~/.config/openfisca-survey-manager/config.ini",
                f"python tests/erfs_fpr/integration/test_aggregates.py --year {year}",
                "mkdir -p $ROOT_FOLDER/$OUT_FOLDER",
                "cp ./*.html $ROOT_FOLDER/$OUT_FOLDER",
                "cp ./*.csv $ROOT_FOLDER/$OUT_FOLDER",
            ],
            "artifacts": {"paths": ["./*.html", "./*.csv"]},
        }
    }


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
                f"cp $ROOT_FOLDER/openfisca_survey_manager_config_input_data-after-build-erfs-fprs-{year}.ini ~/.config/openfisca-survey-manager/config.ini",
                "make test",
            ],
        }
    }


def make_test():
    return {
        "test": {
            "stage": "test",
            "image": "$CI_REGISTRY_IMAGE:latest",
            "tags": ["openfisca"],
            "script": [
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


def build_conda_package():
    """
    Build conda package
    """
    return {
        "build_conda_package": {
            "stage": "anaconda",
            "before_script": [""],
            "image": "continuumio/miniconda3",
            "script": [
                "conda install -y conda-build anaconda-client",
                "conda build -c conda-forge -c openfisca --token $ANACONDA_TOKEN --user OpenFisca .conda",
            ],
            "except": ["master"],
        }
    }


def build_and_deploy_conda_package():
    """
    Build and deploy conda package
    """
    return {
        "build_and_deploy_conda_package": {
            "stage": "anaconda",
            "before_script": [""],
            "image": "continuumio/miniconda3",
            "script": [
                "conda install -y conda-build anaconda-client",
                "conda config --set anaconda_upload yes",
                "conda build -c conda-forge -c openfisca --token $ANACONDA_TOKEN --user OpenFisca .conda",
            ],
            "only": ["master"],
        }
    }


def build_gitlab_ci(erfs_years):
    gitlab_ci = header()
    gitlab_ci += yaml.dump(make_test())
    gitlab_ci += yaml.dump(build_conda_package())
    gitlab_ci += yaml.dump(build_and_deploy_conda_package())
    gitlab_ci += yaml.dump(build_collections())
    for year in erfs_years:
        print("\t ERFS : Building for year", year)
        gitlab_ci += yaml.dump(build_input_data(year))
        gitlab_ci += yaml.dump(aggregates(year))
    return gitlab_ci


def main():
    print("Reading survey manager config...")
    erfs_years = get_erfs_years()
    # For testing only some years
    erfs_years = ["2018"]
    gitlab_ci = build_gitlab_ci(erfs_years)
    with open(r".gitlab-ci.yml", mode="w") as file:
        file.write(gitlab_ci)
    print("Done with success!")


main()

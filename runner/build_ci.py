import configparser
import yaml

# Config file use to get the available years
CONFIG='./runner/openfisca_survey_manager_raw_data.ini'

def header():
    return '''
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

cache:
  paths:
    - .cache/pip
    - ./figures/

stages:
  - docker
  - build_collection
  - build_input_data
  - aggregates
  - test
  
before_script:
  - echo "I'm executed before all job's"
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

'''



def build_collections():
    build_collection = {
    'build_collection':
        {'stage': 'build_collection',
        'image': '$CI_REGISTRY_IMAGE:latest',
        'tags': ['openfisca'],
        'script': [
            'echo "Begin with fresh config"',
            'mkdir -p /mnt/data-out/data_collections/$OUT_FOLDER/',
            'rm /mnt/data-out/data_collections/$OUT_FOLDER/*.json || true',   # || true to ignore error
            'cp ./runner/openfisca_survey_manager_config.ini ~/.config/openfisca-survey-manager/config.ini',
            'echo "Custom output folder"',
            'sed -i "s/data_collections/data_collections\/$OUT_FOLDER\//" ~/.config/openfisca-survey-manager/config.ini',
            'cat ~/.config/openfisca-survey-manager/config.ini',
            '#build-collection -c enquete_logement -d -m -s 2013',
            'build-collection -c erfs_fpr -d -m -v',
            'echo "Backup updated config"',
            'cp ~/.config/openfisca-survey-manager/config.ini /mnt/data-out/openfisca-france-data/openfisca_survey_manager_config-after-build-collection.ini'

        ],
        'when': 'manual',
        }
    }
    return build_collection

def build_input_data(year):
    return {
    'in_dt-'+ year:
        {'stage': 'build_input_data',
        'image': '$CI_REGISTRY_IMAGE:latest',
        # Remove needs because it prevent execution if build_collection is in manual
        #'needs': ['build_collection'],
        'tags': ['openfisca'],
        'script': [
            'echo "build_input_data-' + year + '"',
            # Put the config from build collections step
            'cp /mnt/data-out/openfisca-france-data/openfisca_survey_manager_config-after-build-collection.ini ~/.config/openfisca-survey-manager/config.ini',
            'build-erfs-fpr -y ' + year,
            'cp ~/.config/openfisca-survey-manager/config.ini /mnt/data-out/openfisca-france-data/openfisca_survey_manager_config_input_data-after-build-erfs-fprs-' + year + '.ini',
            ],
        }
    }

def aggregates(year):
    return {
    'agg-'+ year:
        {'stage': 'aggregates',
        'image': '$CI_REGISTRY_IMAGE:latest',
        'needs': ['in_dt-' + year ],
        'tags': ['openfisca'],
        'script': [
            'echo "aggregates-' + year + '"',
            'cp /mnt/data-out/openfisca-france-data/openfisca_survey_manager_config_input_data-after-build-erfs-fprs-' + year + '.ini ~/.config/openfisca-survey-manager/config.ini',
            #'python tests/erfs_fpr/integration/test_aggregates.py --configfile ~/.config/openfisca-survey-manager/raw_data.ini',
            'python tests/erfs_fpr/integration/test_aggregates.py --year ' + year,
            'mkdir -p /mnt/data-out/$OUT_FOLDER',
            'ls ./*.csv',
            'cp ./*.csv /mnt/data-out/$OUT_FOLDER',
            ],
        'artifacts':{
            'paths': ['./*.csv']
            }
        }
    }

def make_test(year):
    return {
        'test-'+year:{
            'stage': 'test',
            'image': '$CI_REGISTRY_IMAGE:latest',
            'needs': ['agg-' + year],
            'tags': ['openfisca'],
            'before_script':[
                'echo before_script',
                'echo Coucou',
            ],
            'script':[
                'cp /mnt/data-out/openfisca-france-data/openfisca_survey_manager_config_input_data-after-build-erfs-fprs-' + year + '.ini ~/.config/openfisca-survey-manager/config.ini',
                'make test',
                ],
            }
        }


def get_erfs_years():
    years = []
    try:
        config = configparser.ConfigParser()
        config.read(CONFIG)
        for key in config['erfs_fpr']:
            if key.isnumeric():
                years.append(key)
        return years
    except KeyError:
        print(f"File {configfile} not found, switchin to default {years}")
        raise KeyError

def build_gitlab_ci(erfs_years):
    gitlab_ci = header()
    gitlab_ci += yaml.dump(build_collections())
    for year in erfs_years:
        print('\t ERFS : Building for year', year)
        gitlab_ci += yaml.dump(build_input_data(year))
        gitlab_ci += yaml.dump(aggregates(year))
        gitlab_ci += yaml.dump(make_test(year))
    return gitlab_ci

def main():
    print("Reading survey manager config...")
    erfs_years = get_erfs_years()
    gitlab_ci = build_gitlab_ci(erfs_years)
    with open(r'.gitlab-ci.yml', mode='w') as file:
        file.write(gitlab_ci)
    print("Done with success!")

main()
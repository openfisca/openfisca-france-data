# Continuous Integration (CI) script and config

This folder contains files needed for the CI.

## Building the Gitlab CI file

To separate the different years and survey files we have a script that build the CI script.

```
python ci-runner/build_ci.py
```

It will create the file `.gitlab-ci.yml` that is read by Gitlab Runner to execute the CI.

## How the LexImpact CI Work

The CI is in the LexImpact GitLab CI to not expose the survey data in public cloud service.

### Step 1: Docker Environment

To have a perfect environment we build a docker image that is stored at [Docker Hub](https://hub.docker.com/r/leximpact/openfisca-france-data).

See [docker folder](../docker) for more information.

It is a manual step because it does not to be build each time.

All following steps is run with this docker image.

### Step 2: Build collection

It is a manual step because it does not to be build each time and took a very long time : between 3 and 4 hours.

Input :
- [../ci-runner/openfisca_survey_manager_config.ini](ci-runner/openfisca_survey_manager_config.ini)
- [../ci-runner/openfisca_survey_manager_raw_data.ini](ci-runner/openfisca_survey_manager_raw_data.ini)
- All survey's files located in `/mnt/data-in/erfs-fpr/` folder that is accessible to the CI Runner.

Output :
- Updated `/mnt/data-out/openfisca-france-data/<BRANCH_NAME>/openfisca_survey_manager_config-after-build-collection.ini`
- Created `/mnt/data-out/openfisca-france-data/<BRANCH_NAME>/data_collections/master/erfs_fpr.json`
- One H5 file per year in `/mnt/data-out/openfisca-france-data/<BRANCH_NAME>/output/erfs_fpr_{year}.h5`

### Step 3: Build Input data

```
2023-02-09 09:01:08 - openfisca_france_data.erfs_fpr.input_data_builder.step_05_final: DEBUG step_05_final - create_input_data_frame: Saving to /mnt/data-out/openfisca-france-data/master/erfs_flat_2018.h5
2023-02-09 09:01:08 - openfisca_france_data.erfs_fpr.input_data_builder.step_05_final: DEBUG step_05_final - create_input_data_frame: Saving entity 'individu' in collection 'openfisca_erfs_fpr' and survey name 'openfisca_erfs_fpr_2018' with set_table_in_survey
```

Input :
- `/mnt/data-out/openfisca-france-data/<BRANCH_NAME>/openfisca_survey_manager_config-after-build-collection.ini`
- `/mnt/data-out/openfisca-france-data/<BRANCH_NAME>/data_collections/{branch}/erfs_fpr.json`
- The H5 files in `/mnt/data-out/openfisca-france-data/<BRANCH_NAME>/output/erfs_fpr_{year}.h5`


Output :
- `/mnt/data-out/openfisca-france-data/<BRANCH_NAME>/openfisca_survey_manager_config_input_data-after-build-erfs-fprs-{year}.ini`
- `/mnt/data-out/openfisca-france-data/data_collections/{branch}/openfisca_erfs_fpr.json`
ERROR ? openfisca_erfs_fpr.json ne référence pas openfisca_erfs_fpr_{year}.h5` !!!

- `/mnt/data-out/openfisca-france-data/<BRANCH_NAME>/output/openfisca_erfs_fpr_{year}.h5`
- `/mnt/data-out/openfisca-france-data/<BRANCH_NAME>/erfs_flat_{year}.h5`

### Step 4: Check Aggregates

Input :
- `/mnt/data-out/openfisca-france-data/<BRANCH_NAME>/openfisca_survey_manager_config_input_data-after-build-erfs-fprs-{year}.ini`

Output :
 - CSV and HTML files in artifact of the [CI job](https://git.leximpact.dev/benjello/openfisca-france-data/-/jobs)

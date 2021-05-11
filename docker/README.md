# Use OpenFisca France Data with Docker

This process aims at computing a unique file from all the [ERFS](https://www.insee.fr/fr/metadonnees/source/serie/s1231) FPR survey files.

Pre-requisis : only Docker and git, no needs of Python on your local machine, everything will be install in Docker.
Tested on Ubuntu Linux 20.04 with success.
Tested on one MacOSX but did not worked.

For all the commands in this readme, you have to be in the root folder of the project `openfisca-france-data`, not `openfisca-france-data/openfisca_france_data`.

```sh
git clone https://github.com/openfisca/openfisca-france-data.git
cd openfisca-france-data
```

Build the Docker image:

```sh
docker build -t openfisca-france-data --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g) . -f ./docker/Dockerfile
```

Now you have a clean Docker image prepared for OpenFisca France Data.

You could launch any command inside, but here is a demo with ERF-FPR

## Demo with data from ERFS-FPR

This script convert data from ERFS-FPR by household to a view by taxes household.

- 1 Place raw data (FPR_*.sas7bdat) in _openfisca-france-data/docker/data/data-in_ folder.
- 2 Edit _openfisca-france-data/docker/data/raw_data.ini_ to specify the year.
- 3 Run the script in Docker:
```
docker run --rm -v $PWD/docker/data:/opt/data openfisca-france-data /opt/openfisca-france-data/docker/erfs-fpr.sh
```
This will make a container from the image, mount your $PWD/docker/data in the container and launch the script `openfisca-france-data/docker/erfs-fpr.sh` inside.

Don't worry it will took a long time. Wait for the message _-- The END --_.

You will find your output file erfs_flat_<year>.h5 in the folder _docker/data/data-out_

/!\ The script erfs-fpr.sh clean up data directories, make sure you have a backup of files you want to keep.

## How to run with your codebase

You could mount you project directory to run your own code, like this:
```
docker run --rm -v $PWD/docker/data:/opt/data \
 -v $PWD/openfisca_france_data:/opt/openfisca-france-data/openfisca_france_data \
 -v $PWD/docker:/opt/openfisca-france-data/docker \
 openfisca-france-data \
 python /opt/openfisca-france-data/openfisca_france_data/erfs_fpr/input_data_builder/__init__.py
```
# Cleaning

When you are sure you will not have to do it again :
```sh
# Remove project folder
rm -r openfisca-france-data
# Remove Docker image
docker rmi $(docker images --filter=reference="openfisca-france-data:latest" -q)
```

Security note : Your data stay in _openfisca-france-data/docker/erfs/data/*_ and are not copied in the image, nor in the container.

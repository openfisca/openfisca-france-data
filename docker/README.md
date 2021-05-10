# Use OpenFisca France Data with Docker

This process aims at computing a unique file from all the [ERFS](https://www.insee.fr/fr/metadonnees/source/serie/s1231) FPR survey files.

Pre-requisis : only Docker.
Tested on Ubuntu Linux 20.04 with success.
Tested on one MacOSX but did not worked.

- Build the Docker image :

```sh
cd openfisca-france-data
docker build -t openfisca-france-data --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g) . -f ./docker/Dockerfile
```

Now you have a clean Docker image prepared for OpenFisca France Data.

You could launch any command inside, but here is a demo with ERF-FPR

## Demo with data from ERFS-FPR

This script convert data from ERFS-FPR by household to a view by taxes household.

- 1_ Place raw data (FPR_*.sas7bdat) in _openfisca-france-data/docker/data/data-in_ folder.
- 2_ Edit _openfisca-france-data/docker/data/raw_data.ini_ to specify the year.
- 3_ Run the script in Docker, you have to be in the root folder of the project `openfisca-france-data`, not `openfisca_france_data` :
```
docker run --rm -v $PWD/docker/data:/opt/data openfisca-france-data /opt/openfisca-france-data/docker/erfs-fpr.sh
```
This will make a container from the image, mount your $PWD/docker/data in the container and launch the script `openfisca-france-data/docker/erfs-fpr.sh` inside.

Don't worry it will took a long time. Wait for the message _-- The END --_.

You will find your files in the folder _docker/data/data-out_

# Cleaning

When you are sure you will not have to do it again  :
```sh
# Remove project folder
rm -r openfisca-france-data
# Remove Docker image
docker rmi $(docker images --filter=reference="openfisca-france-data:latest" -q)
```

Security note : Your data stay in _openfisca-france-data/docker/erfs/data/*_ and are not copied in the image, nor in the container.

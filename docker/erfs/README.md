# Generate flat data from ERFS-FPR with Docker

This process aims at computing a unique file from all the [ERFS](https://www.insee.fr/fr/metadonnees/source/serie/s1231) FPR survey files.

Pre-requisis : only Docker.

XXXX tester avec 2014

- 1_ Place raw data (FPR_*.sas7bdat) in _openfisca-france-data/docker/erfs/data/data-in_ folder.
- 2_ Edit _openfisca-france-data/docker/erfs/data/raw_data.ini_ to specify the year.
- 3_ Edit _openfisca-france-data/openfisca_france_data/erfs_fpr/input_data_builder/__init__.py_ to specify the year, look for _"year = 2016"_ at the end.
- 4_ Launch Docker:

```sh
cd openfisca-france-data/docker/erfs
docker build -t openfisca-france-data-erfs --build-arg USER_ID=$(id -u) --build-arg GROUP_ID=$(id -g) .
docker run --rm -v $PWD/data:/opt/erfs/data openfisca-france-data-erfs
```

Don't worry it will took time.

You will find you files in _openfisca-france-data/docker/erfs/data/data-out_

When you are sure you will not have to do it again  :
```sh
# Remove project folder
rm -r openfisca-france-data
# Remove Docker image
docker rmi $(docker images --filter=reference="openfisca-france-data-erfs:latest" -q)
```

Security note : Your data stay in _openfisca-france-data/docker/erfs/data/*_ and are not copied in the image, nor in the container.

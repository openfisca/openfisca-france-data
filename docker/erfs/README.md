# Generate flat data from ERFS-FPR with Docker

Pre-requisis : only Docker.


- 1_ Place raw data (FPR_*.sas7bdat) in _openfisca-france-data/docker/erfs/data/data-in_ folder.
- 2_ Edit _openfisca-france-data/docker/erfs/data/raw_data.ini_ to specify the year.
- 3_ Edit _openfisca-france-data/openfisca_france_data/erfs_fpr/input_data_builder/__init__.py_ to specify the year, look for _"year = 2016"_ at the end.
- 4_ Launch Docker :

```sh
cd openfisca-france-data/docker/erfs
docker build . -t openfisca-france-data-erfs
docker run --rm -v $PWD/data:/opt/erfs/data openfisca-france-data-erfs
```

You will find you files in _openfisca-france-data/docker/erfs/data/data-out_

When you are sure you will not have to do it again  :
```sh
# Remove project folder
rm -r openfisca-france-data
# Remove Docker image
docker rmi $(docker images --filter=reference="openfisca-france-data-erfs:latest" -q)
```

Security note : Your data stay in _openfisca-france-data/docker/erfs/data/*_ and are not copied in the image, nor in the container.
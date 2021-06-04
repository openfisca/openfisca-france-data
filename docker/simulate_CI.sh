#!/bin/bash

DATA_FOLDER=$PWD/docker/data
if [ -d $DATA_FOLDER  ];
then
    echo "Starting..."
else
       echo "Please run the script from the root folder of the project. For example :"
       echo "open@fisca: ~/dev/openfisca-france-data>./docker/simulate_CI.sh"
       exit 1;
fi

docker pull leximpact/openfisca-france-data:latest
DOCKER_COMMAND="docker run --rm -v $DATA_FOLDER:/mnt leximpact/openfisca-france-data:latest "

# Cleaning
echo "Cleaning directories..."
rm $DATA_FOLDER/data-out/tmp/*.h5
rm $DATA_FOLDER/data-out/*.h5
rm $DATA_FOLDER/data-out/data_collections/$OUT_FOLDER/*.json
# Clean config file
sed -i '/erfs_fpr = /d' $DATA_FOLDER/config.ini
sed -i '/openfisca_erfs_fpr = /d' $DATA_FOLDER/config.ini
cd $DATA_FOLDER
echo "Building collection in `pwd`..."
$DOCKER_COMMAND build-collection -c erfs_fpr -d -m -v 2>&1
if [ $? -eq 0 ]; then
    echo "Building collection finished."
else
    echo "ERROR in build-collection"
    echo "---------------- DONE WITH ERROR -----------------------------"
    exit 1
fi

echo "------------------------------------------------------------"
echo "-- build-erfs-fpr... --"
echo "------------------------------------------------------------"
$DOCKER_COMMAND build-erfs-fpr -y 2014 && $DOCKER_COMMAND build-erfs-fpr -y 2016
if [ $? -eq 0 ]; then
    echo "---------------- build-erfs-fpr done --------------------------"
else
    echo "ERROR in build-erfs-fpr"
    echo "---------------- DONE WITH ERROR -----------------------------"
    exit 1
fi

echo "------------------------------------------------------------"
echo "-- Test aggregates... --"
echo "------------------------------------------------------------"
$DOCKER_COMMAND python /opt/openfisca-france-data/tests/erfs_fpr/integration/test_aggregates.py --configfile /root/.config/openfisca-survey-manager/raw_data.ini
if [ $? -eq 0 ]; then
    echo "---------------- Test aggregates done. --------------------------"
else
    echo "ERROR in Test aggregates"
    echo "---------------- DONE WITH ERROR -----------------------------"
    exit 1
fi

echo "------------------------------------------------------------"
echo "-- Test (make test)... --"
echo "------------------------------------------------------------"
$DOCKER_COMMAND make test
if [ $? -eq 0 ]; then
    echo "---------------- make test done. --------------------------"
else
    echo "ERROR in make test"
    echo "---------------- DONE WITH ERROR -----------------------------"
    exit 1
fi
echo "-- The END --"

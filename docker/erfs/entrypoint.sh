#!/bin/bash
if [[ -z "${DATA_FOLDER}" ]]; then
  export DATA_FOLDER=/opt/erfs/data
fi
cd $DATA_FOLDER
# Cleaning
echo "Cleaning directories..."
rm $DATA_FOLDER/tmp/*.h5
rm $DATA_FOLDER/data-out/*.h5
rm $DATA_FOLDER/collections/*.json
# Clean config file
sed -i '/erfs_fpr = /d' $DATA_FOLDER/config.ini
sed -i '/openfisca_erfs_fpr = /d' $DATA_FOLDER/config.ini
echo "Building collection in `pwd`..."
build-collection -c erfs_fpr -d -m -v  -p $DATA_FOLDER
if [ $? -eq 0 ]; then
    echo "Building collection finished."
else
    echo "ERROR in build-collection"
    echo "Content of $DATA_FOLDER : "
    ls $DATA_FOLDER
    echo "Content of $DATA_FOLDER/data-in/: "
    ls $DATA_FOLDER/data-in/
    echo "Content of $DATA_FOLDER/data-out/ : "
    ls $DATA_FOLDER/data-out/
    echo "Content of $DATA_FOLDER/tmp/ : "
    ls $DATA_FOLDER/tmp/
    echo "---------------- DONE WITH ERROR -----------------------------"
    exit 1
fi

echo "------------------------------------------------------------"
echo "-- Generating a flattened file consumable by openfisca... --"
echo "------------------------------------------------------------"
python /opt/openfisca-france-data/openfisca_france_data/erfs_fpr/input_data_builder/__init__.py
if [ $? -eq 0 ]; then
    mv $DATA_FOLDER/erfs_flat_*.h5 $DATA_FOLDER/data-out/
else
    echo "ERROR in build-collection"
    echo "Content of $DATA_FOLDER : "
    ls $DATA_FOLDER
    echo "Content of $DATA_FOLDER/data-in/: "
    ls $DATA_FOLDER/data-in/
    echo "Content of $DATA_FOLDER/data-out/ : "
    ls $DATA_FOLDER/data-out/
    echo "Content of $DATA_FOLDER/tmp/ : "
    ls $DATA_FOLDER/tmp/
    echo "---------------- DONE WITH ERROR -----------------------------"
    exit 1
fi
echo "---------------- DONE -----------------------------"


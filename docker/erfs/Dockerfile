FROM python:3.7

RUN pip install sas7bdat tables openfisca-survey-manager==0.19.1
WORKDIR /opt
RUN git clone https://github.com/openfisca/openfisca-france-data.git
WORKDIR /opt/openfisca-france-data
RUN git checkout --track origin/erfs-data-improved
RUN pip install --upgrade pip setuptools twine wheel
RUN pip install --editable .[test] --upgrade

# build-collection can get a path of file location in parameter but not openfisca_france_data.
# That's why we create a symbolic link from the default location of config to our data path
RUN mkdir -p /root/.config
RUN ln -s  /opt/erfs/data /root/.config/openfisca-survey-manager

WORKDIR /opt/erfs
COPY entrypoint.sh .
ENTRYPOINT [ "/opt/erfs/entrypoint.sh" ]

FROM python:3.7

# Add user and group to Image to get output files with the host user ownership
ARG USER_ID
ARG GROUP_ID
RUN [ $(getent group $GROUP_ID) ] || addgroup --gid $GROUP_ID openfiscauser
RUN [ $(id $USER_ID) ] || adduser --disabled-password --gecos '' --uid $USER_ID --gid $GROUP_ID openfiscauser
RUN mkdir -p /home/openfiscauser/.local/bin
ENV PATH "$PATH:/home/openfiscauser/.local/bin"
RUN echo "PATH=$PATH:/home/openfiscauser/.local/bin" > /home/openfiscauser/.bashrc

# Install OpenFisca France Data
WORKDIR /opt
RUN git clone https://github.com/openfisca/openfisca-france-data.git
WORKDIR /opt/openfisca-france-data
RUN chown $USER_ID:$GROUP_ID -R /opt /home/openfiscauser

# Switch to the openfiscauser
USER openfiscauser
# Install dependencies
RUN python3 -m pip install --upgrade pip
RUN pip install --upgrade pip setuptools
RUN pip install --editable .[test] --upgrade
RUN pip install sas7bdat

# build-collection can get a path of file location in parameter but not openfisca_france_data.
# That's why we create a symbolic link from the default location of config to our data path
RUN mkdir -p /home/openfiscauser/.config
RUN ln -s  /opt/data /home/openfiscauser/.config/openfisca-survey-manager

WORKDIR /opt/data

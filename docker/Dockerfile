FROM python:3.7

# Add user and group to Image to get output files with the host user ownership
# ARG USER_ID=1001
# ARG GROUP_ID=1001
# RUN [ $(getent group $GROUP_ID) ] || addgroup --gid $GROUP_ID openfiscauser
# RUN [ $(id $USER_ID) ] || adduser --disabled-password --gecos '' --uid $USER_ID --gid $GROUP_ID openfiscauser
RUN mkdir -p ~/.local/bin
RUN mkdir -p ~/.config
ENV PATH "$PATH:~/.local/bin"
RUN echo "PATH=$PATH:~/.local/bin" > ~/.bashrc

# Install OpenFisca France Data
WORKDIR /opt/openfisca-france-data
# RUN https://github.com/openfisca/openfisca-france-data.git

#RUN chown $USER_ID:$GROUP_ID -R /opt ~/
COPY Makefile .
COPY setup.py .
COPY README.md .
# Switch to the openfiscauser
# USER openfiscauser
# Install dependencies
# RUN python3 -m pip install --upgrade pip
# RUN pip install --upgrade pip setuptools
# RUN pip install --editable .[test] --upgrade
RUN make install
RUN pip install sas7bdat scipy
COPY . .
# build-collection can get a path of file location in parameter but not openfisca_france_data.
# That's why we create a symbolic link from the default location of config to our data path
RUN ln -s  /mnt ~/.config/openfisca-survey-manager

WORKDIR /mnt

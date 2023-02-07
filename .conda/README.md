# Publish to conda

There are two ways to publish to conda:

- A fully automatic in CI that publish to an "openfisca" channel. See below for more information.
- A more complex for Conda-Forge.

We use both for openfisca-core but only _openfisca channel_ for _OpenFisca-France-Data_.

## Automatic upload

The CI automaticaly build the Conda package and publish it when merging on master, see the `.github/workflow.yml`, step `publish-to-conda`.

## Manual actions made to make it works the first time

- Create an account on https://anaconda.org.
- Create a token on https://anaconda.org/openfisca/settings/access with _Allow write access to the API site_. Warning, it expire on 2025/01/14.
- Put the token in a CI env variable ANACONDA_TOKEN.

## Manual actions before CI exist

To create the package you can do the following in the project root folder:

- Edit `.conda/meta.yaml` and update it if needed:
    - Version number
    - Dependencies

- Install `conda-build` to build the package and [anaconda-client](https://github.com/Anaconda-Platform/anaconda-client) to push the package to anaconda.org:
    - `conda install -c anaconda conda-build anaconda-client`

- Build & Upload package:
    - `conda build .conda`
    - `anaconda login`
    - `anaconda upload openfisca-france-data-<VERSION>-py_0.tar.bz2`

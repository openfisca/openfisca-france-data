# OpenFisca France Data

[![Slack](https://img.shields.io/badge/slack-join%20us!-blueviolet.svg?style=flat)](https://openfisca.slack.com/signup)
[![CircleCI](https://img.shields.io/circleci/project/github/openfisca/openfisca-france-data/master.svg?style=flat)](https://circleci.com/gh/openfisca/openfisca-france-data)

[OpenFisca](https://openfisca.org/doc/) is a versatile microsimulation libre software. Check the [online documentation](https://openfisca.org/doc/) for more details.

This package contains the France-Data module, allows you to work with French survey data (ERFS, ERFS-FPR, etc.) and [OpenFisca-France](https://github.com/openfisca/openfisca-france).

## Environment

OpenFisca-France-Data runs on Python 2.7, but it is being migrated to 3.7.

Backward compatibility with Python 2.7 won't be kept.

## Installation

If you want to contribute to OpenFisca-France-Data, please be welcomed! To install it locally in development mode:

```bash
git clone https://github.com/openfisca/openfisca-france-data.git
cd openfisca-france-data
make install
```

## Testing

To run the entire test suite:

```sh
make test
```

## Style

This repository adheres to a certain coding style, and we invite you to follow it for your contributions to be integrated promptly.

To run the style checker:

```sh
make check-style
```

To automatically style-format your code changes:

```sh
make format-style
```

To automatically style-format your code changes each time you commit:

```sh
touch .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit

tee -a .git/hooks/pre-commit << END
#!/bin/sh
#
# Automatically format your code before committing.
exec make format-style
END
```

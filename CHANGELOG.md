# Changelog

## 0.16.0 [#191](https://github.com/openfisca/openfisca-france-data/pull/191)

Change the requirement version for OF-France

## 0.15.0 [#190](https://github.com/openfisca/openfisca-france-data/pull/190)

* New features
  - Introduce a new weight variable for households

* Technical changes
  -  Update the SMIC parameter

### 0.14.1 [#188](https://github.com/openfisca/openfisca-france-data/pull/188)

* Technical changes
  - Fix pypi upload by fixing package description
    - Fix this [CircleCI](https://circleci.com/gh/openfisca/openfisca-france-data/663) error: `The description failed to render in the default format of reStructuredText.`

## 0.14 [#187](https://github.com/openfisca/openfisca-france-data/pull/187)

* Technical changes
  - Migrate CI from Travis to CircleCI
  - Reset `master` branch as default branch instead of `release/1.0.0`
    - Contains [#161](https://github.com/openfisca/openfisca-france-data/pull/161), [#171](https://github.com/openfisca/openfisca-france-data/pull/171), [#172](https://github.com/openfisca/openfisca-france-data/pull/172), [#173](https://github.com/openfisca/openfisca-france-data/pull/173), [#179](https://github.com/openfisca/openfisca-france-data/pull/179), [#183](https://github.com/openfisca/openfisca-france-data/pull/183), [#186](https://github.com/openfisca/openfisca-france-data/pull/186)

### 0.13.2 [#186](https://github.com/openfisca/openfisca-france-data/pull/186)

* Technical changes
  - Various cleaning
  - Introduction of MTR calculation

### 0.13.1 [#179](https://github.com/openfisca/openfisca-france-data/pull/179)

* Technical changes
  - Add `matplotlib` library to default requirements.
* Add documentation for users discovering, installing and running the module for the first time.

## 0.13.0 [177](https://github.com/openfisca/openfisca-france-data/pull/177)

- Introduce a file export that contains only one flattened table (`dummy_data.h5`) instead of exporting a file with several tables.
  - Adds `export_flattened_df` argument in `create_input_data_frame function`.
- Bump `numexpr` top version.

## 0.12.0 [173](https://github.com/openfisca/openfisca-france-data/pull/173)

- Get some cleaner stuff from IPP modifs from CASD.

### 0.11.1 [172](https://github.com/openfisca/openfisca-france-data/pull/172)

- Fix numpy dependency to deal with openfisca-survey-manager deps (see https://github.com/openfisca/openfisca-survey-manager/pull/79).

## 0.11.0 [171](https://github.com/openfisca/openfisca-france-data/pull/171)

- Adapt to new version of openfisca-survey-manager (v0.21)

## 0.10.0 [161](https://github.com/openfisca/openfisca-france-data/pull/161)

- Adapt to new version of openfisca-survey-manager (v0.20) and openfisca-core (v34)

## 0.9.0 [170](https://github.com/openfisca/openfisca-france-data/pull/170)

- Further cleanup
  - Deprecation of `new_simulation_from_array_dict`

### 0.8.4 [169](https://github.com/openfisca/openfisca-france-data/pull/169)

- Cleanup tests

### 0.8.3 [167](https://github.com/openfisca/openfisca-france-data/pull/167)

- Fix `test_build_cerfa_fields_by_column_name`

### 0.8.2 [166](https://github.com/openfisca/openfisca-france-data/pull/166)

- Replace `.iteritems()` with `.items()`
  - For Python 3 compatibility

### 0.8.1 [163](https://github.com/openfisca/openfisca-france-data/pull/163)

- Deploy to PyPi

## 0.8.0 [162](https://github.com/openfisca/openfisca-france-data/pull/162)

- Deprecate experimental tools

### 0.7.12 [159](https://github.com/openfisca/openfisca-france-data/pull/159)

- Document ERFS-FPR data processing

### 0.7.11 [158](https://github.com/openfisca/openfisca-france-data/pull/158)

- Split unit and integration tests
- Add doc to `scenario.py` and `get_survey_scenario.py`
- Add tests to `get_survey_scenario.py`
- Use `multipledispatch` to reduce code complexity

### 0.7.10 [153](https://github.com/openfisca/openfisca-france-data/pull/153)

- Import `reduce` from `functools`
  - It has been moved there in Python 3

### 0.7.9 [150](https://github.com/openfisca/openfisca-france-data/pull/150)

- Replace `nosetests` (unmaintained) with `pytest`

### 0.7.8 [151](https://github.com/openfisca/openfisca-france-data/pull/151)

- Bump openfisca-france version to 34

### 0.7.7 [145](https://github.com/openfisca/openfisca-france-data/pull/145)

- Remove `__future__` imports
  - They make sense no more as we've migrated to the Python 3 interpreter

### 0.7.6 [146](https://github.com/openfisca/openfisca-france-data/pull/146)

- Limit code coverage to the `openfisca-france-data` package

### 0.7.5 [144](https://github.com/openfisca/openfisca-france-data/pull/144)

- Change `print arg` to `print(arg)` for Python 3 compatibility

### 0.7.4 [140](https://github.com/openfisca/openfisca-france-data/pull/140)

- Add CircleCI

### 0.7.3 [138](https://github.com/openfisca/openfisca-france-data/pull/138)

- Remove licence from files

### 0.7.2 [136](https://github.com/openfisca/openfisca-france-data/pull/136)

- Remove already deprecated files

### 0.7.1 [135](https://github.com/openfisca/openfisca-france-data/pull/135)

- Update repo's instructions to help contirbutors get started

## 0.7

- Improvement of inversion script (WIP)

## 0.6

- Bump openfisca-core version to 23

### 0.5.10

- Bump openfisca-core version to 21

### 0.5.7

- Migration to the new syntax
- Deprecation of `entity_key_plural`

### 0.5.6

- Use of [RSA](https://www.legifrance.gouv.fr/affichCode.do?idArticle=LEGIARTI000031694448&idSectionTA=LEGISCTA000006178378&cidTexte=LEGITEXT000006074069&dateTexte=20190216)'s "âge limite" to constitute a family

### 0.5.5

- Add missing before_deploy (tagging)

### 0.5.4

- Activate deployment (tagging)

### 0.5.3

- Really add automatic version tagging (bump)

### 0.5.2

- Add automatic version tagging

### 0.5.1

- Improve Makefile checks

## 0.5

- Create CHANGELOG.md
- Check version and changelog when pushing

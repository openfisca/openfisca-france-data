# Changelog

## 0.7.10 [153](https://github.com/openfisca/openfisca-france-data/pull/153)

- Import `reduce` from `functools`
  - It has been moved there in Python 3

## 0.7.9 [150](https://github.com/openfisca/openfisca-france-data/pull/150)

- Replace `nosetests` (unmaintained) with `pytest`

## 0.7.8 [151](https://github.com/openfisca/openfisca-france-data/pull/151)

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

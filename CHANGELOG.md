# Changelog

### 3.4.2 [#258](https://github.com/openfisca/openfisca-france-data/pull/258)

* Technical changes
  - Ajout d'aggrégats de comparaion pour 2022
  - Corrige les tests de comparaisons et d'agrégats

### 3.4.1 [#257](https://github.com/openfisca/openfisca-france-data/pull/257)

* Technical changes
  - Met à jour la dépendance à OpenFisca France


### 3.4.0 [#252](https://github.com/openfisca/openfisca-france-data/pull/252)

* New features
  - Rend l'inversion plus robuste pour permettre de la faire de manière mois par mois
  - En particulier, donne un seuil d'exonération sur le chômage net dépendant de la période.
  - Ajoute dans l'inversion la prise en compte de l'indemnité compensatrice de csg

### 3.3.1 [#256](https://github.com/openfisca/openfisca-france-data/pull/256)

* Technical changes
  - Met à jour la version d'Openfisca France dans les dépendances


### 3.3.0 [#251](https://github.com/openfisca/openfisca-france-data/pull/251)

* New features
  - Introduce testing for income "inversion" (deduce gross from net)
* Update features
  - Corrects the inversion functions + extends the inversion of unemployment benefit's taxation

### 3.2.0 [#255](https://github.com/openfisca/openfisca-france-data/pull/255)

* New features
  - Améliore la construction des variables `contrat_de_travail` et `heures_remunerees_volumes` avec l'erfs_fpr
    - Utilisations des variables `sp00` à `sp12` qui décrivent le statut d'activité sur les douze derniers mois pour prendre en compte la part de travail connue dans l'année

### 3.1.3 [#254](https://github.com/openfisca/openfisca-france-data/pull/254)

* Technical changes
  - Met à jour la version d'openfisca france dans les dépendances

### 3.1.2 [#250](https://github.com/openfisca/openfisca-france-data/pull/250)

* Reverts #209

### 3.1.1 [#249](https://github.com/openfisca/openfisca-france-data/pull/249)

* Technical changes
  - Met à jour la version d'openfisca france dans les dépendances

### 3.1.0 [#209](https://github.com/openfisca/openfisca-france-data/pull/209)

New features
    Introduce testing for income "inversion" (deduce gross from net)
Update features
    Corrects the inversion functions + extends the inversion of unemployment benefit's taxation

### 3.0.6 [#248](https://github.com/openfisca/openfisca-france-data/pull/248)
* Technical changes
- Correction d'une typo dans la PR précédente

### 3.0.5 [#247](https://github.com/openfisca/openfisca-france-data/pull/247)
* Technical changes
- Pour corriger la publication de la librairie sur PyPi, passe à une authentification PyPi via un token


### 3.0.4 [#246](https://github.com/openfisca/openfisca-france-data/pull/246)
* Technical changes
- Augmente la version d'openfisca-france exigée en dépendance


### 3.0.3 [#244](https://github.com/openfisca/openfisca-france-data/pull/244)
* Technical changes:
- Correction dees liens des paramètres dans la fonction create_taux_csg_remplacement

### 3.0.2 [#243](https://github.com/openfisca/openfisca-france-data/pull/243)
* Technical changes:
- Ajoute la possibilité d'utiliser un tax and benefit system plus en aval dans les fonctions de utils.py

### 3.0.1 [#242](https://github.com/openfisca/openfisca-france-data/pull/242)
* Technical changes:
- Passage à Openfsca-France >= 155.0.0

### 3.0.0 [#241](https://github.com/openfisca/openfisca-france-data/pull/241)
- Breaking changes

Adapte le dépôt au passage à openfisca-survey-manager 2.0.0 qui constitue une refactorisation de l'objet survey-scenario et des simulations qui sont dedans. Cela concerne donc les parties de ce dépôts qui héritent d'objets d'openfisca-survey-manager :
- `openfisca_france_data/aggregates.py`
- `openfisca_france_data/surveys.py`
Les autres modifications sont des adaptions syntaxique mineurs du fait de cette adaptation

### 2.0.7 [#239](https://github.com/openfisca/openfisca-france-data/pull/239/files)
* New features
- Ajoute des nouveaux agrégats pour FranceAggregates

### 2.0.6 [#240](https://github.com/openfisca/openfisca-france-data/pull/240)
* Technical changes
- Rapatrie certaines réformes qui ont été supprimés dans openfisca france par la (PR 2177)[https://github.com/Supprime vieilles réformes non utilisées openfisca-france#2177] mais qui sont encore utilisées dans ce dépôt

### 2.0.5 [#238](https://github.com/openfisca/openfisca-france-data/pull/238)
* Technical changes
- Corrige le calcul du smic annuel en fonction du smic horaire dans openfisca_france_data/erfs_fpr/input_data_builder/step_04_famille.py

### 2.0.4 [#237](https://github.com/openfisca/openfisca-france-data/pull/237)
* Technical changes
- Deplace click en dependance de test

### 2.0.3 [#235](https://github.com/openfisca/openfisca-france-data/pull/235)
* Technical changes
- Passe conda dep en Jinja en suivant Openfisca-France

### 2.0.2 [#234](https://github.com/openfisca/openfisca-france-data/pull/234)
* Technical changes
- Update autopep8 et flake8 pour avoir des requirements compatibles avec les dernières versions d'openfisca-france et openfisca-survey-manager

### 2.0.1 [#232](https://github.com/openfisca/openfisca-france-data/pull/232)
* Technical changes
- Fix de #230 qui se produit quand le wokflow de CI a tourné deux fois pour le même commit, ce qui arrive quand on crée la PR. La solution est de limiter la recherche de l’artefact aux workflows lancés par un push.

# 2.0.0 [#229](https://github.com/openfisca/openfisca-france-data/pull/229)
* Technical changes
- Met à jour Python dans le setup pour compatibilité conda

# 1.3.1 [#228](https://github.com/openfisca/openfisca-france-data/pull/228)
* Technical changes
- Ajout de deux jeux de données utilisées pour les tests au paquet :
    -  'assets/aggregats/taxipp/agregats_tests_taxipp_2_0.xlsx'
    - `'assets/aggregats/ines/ines_2019.json'

# 1.3.0 [#227](https://github.com/openfisca/openfisca-france-data/pull/227)
* Technical changes
- Adapte le comparator pour effectuer plus de tests en distribution
- Permet l'utilisation d'un SurveyScenario facilement personnalisable


# 1.2.0 [#226](https://github.com/openfisca/openfisca-france-data/pull/226)
* Technical changes
- Adapte le comparator pour permettre de changer les agrégats cibles.
- Ajoute les agrégats de la note de validation d'INES

# 1.1.0 [#225](https://github.com/openfisca/openfisca-france-data/pull/225)

* Technical changes
- Ajoute des variables concernant le calcul des aides au logement, des non salariés et du handicap dans le builder de openfisca-france-data

# 1.0.0 [#224](https://github.com/openfisca/openfisca-france-data/pull/224)

* Breaking changes
- dans model/common.py/salaire_brut:
  - Retire rev_microsocial

- Détails
  - rev_microsocial n'était pas un salaire mais un CA net des cotisations sociales pour les micro-entrepreneurs optant pour le  versement libératoire de l'IR. Elle était donc à tort dans salaire_brut, d'autant plus qu'il n'y a pas d'autres rpns qui y  sont répertoriés.

## 0.27 [#223](https://github.com/openfisca/openfisca-france-data/pull/223)

* Technical changes
  - Utilise les version Python >= 3.9 des dépendances liées à openfisca
  - Contient les versions précédentes non concernées par une PR sur github

## 0.26

* Technical changes
  - Utilise les cibles de taxipp dans les agrégats

### 0.25.1

* Minor change
  - Change la version de flake8

## 0.25 [#XXX](https://github.com/openfisca/openfisca-france-data/pull/XXX)

* Technical changes
  - Amélioration du comparateur pour permettre de définir le survey_scenario

## 0.24 [#215](https://github.com/openfisca/openfisca-france-data/pull/215)

* Technical changes
  - Ajout d'un comparateur ERFS-FPR vs simulation oepnfisca
    - produit des graphes diagnostics
    - produit de un tableur ouvert dans dtale pour rechercher les cas les plus problématiques

### 0.23.1 [#213](https://github.com/openfisca/openfisca-france-data/pull/213)

* Technical changes

  - Amélioration de la CI GitLab :
    - Ajout d'une étape manuelle pour initialiser les bases de la branche à partir de la dernière CI de master.
    - Ajout d'une étape manuelle pour faire tourner sur toutes les branches.

### 0.23.0 [#212](https://github.com/openfisca/openfisca-france-data/pull/212)

* Technical changes

  - Dans openfisca_france_data/erfs_fpr/input_data_builder/step_05_final.py:
    - Corrige la création de l'identifiant unifié ménage. Celui-ci était créé dans la table individus mais n'était pas propagé dans la table ménage. Les identifiants entre les deux tables n'étaient donc pas correspondant

### 0.22.2 [#211](https://github.com/openfisca/openfisca-france-data/pull/211)

* Technical changes
  -  Better branch isolation in Gitlab CI

### 0.22.1 [#208](https://github.com/openfisca/openfisca-france-data/pull/208)

* Technical changes
  -  Remove Conda publish from Gitlab CI
  -  Put back all years in Gitlab CI

### 0.22.0 [#206](https://github.com/openfisca/openfisca-france-data/pull/206)

* Technical changes
  - Replace Circle CI by GitHub Action
  - Add publication to Conda https://anaconda.org/openfisca/openfisca-france-data

### 0.21.1 [#207](https://github.com/openfisca/openfisca-france-data/pull/207)

* Technical changes
  - Corrects two typos in the create_taux_csg_remplacement function used in the income inversion.

### 0.21 [#205](https://github.com/openfisca/openfisca-france-data/pull/205)

* Technical changes
  - Update openfisca-france dependency and fix parameters paths accordingly

### 0.20 [#204](https://github.com/openfisca/openfisca-france-data/pull/204)

* Technical changes
  - Update openfisca-france dependency and fix parameters paths accordingly


### 0.19.4 [#203](https://github.com/openfisca/openfisca-france-data/pull/203)

* Technical changes
  - Update the function create_taux_csg_remplacement and create_revenus_remplacement_bruts

### 0.19.3 [#201](https://github.com/openfisca/openfisca-france-data/pull/201)

* Technical changes
  - Fix create_salaire_de_base

### 0.19.2 [#XXX](https://github.com/openfisca/openfisca-france-data/pull/XXX)

* Technical changes
  - Update dependance for openfisca-survey-manager (again)

### 0.19.1 [#XXX](https://github.com/openfisca/openfisca-france-data/pull/XXX)

* Technical changes
  - Update dependance for openfisca-survey-manager

## 0.19.0 [#XXX](https://github.com/openfisca/openfisca-france-data/pull/XXX)

* Technical changes
  - Use Aggregates from oepnfisca-survey-manager

## 0.18.0 [#189](https://github.com/openfisca/openfisca-france-data/pull/189)

* Technical changes
  - Handles more formats of the ERFS-FPR (the files produced do not always have the exact same columns / column names) and ignore case in file name.

## 0.17.0 [#193](https://github.com/openfisca/openfisca-france-data/pull/193)

* Technical changes
  - Move smic definitions in a separate module

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

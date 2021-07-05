#! /usr/bin/env python
import gc
import logging

from pandas import DataFrame, MultiIndex, concat
import numpy as np



from openfisca_france_data.erfs.input_data_builder.base import (
    year_specific_by_generic_data_frame_name)
from openfisca_survey_manager.temporary import temporary_store_decorator
from openfisca_survey_manager.survey_collections import SurveyCollection


log = logging.getLogger(__name__)


@temporary_store_decorator(file_name = 'erfs')
def create_fip(temporary_store = None, year = None):
    assert temporary_store is not None
    assert year is not None
    # FIP : fichier d'imposition des personnes
    """
    Creates a 'fipDat' table containing all these 'fip individuals'
    """
    # Some individuals are declared as 'personne à charge' (pac) on 'tax forms'
    # but are not present in the erf or eec tables.
    # We add them to ensure consistency between concepts.

    year_specific_by_generic = year_specific_by_generic_data_frame_name(year)

    erfs_survey_collection = SurveyCollection.load(
        collection = 'erfs', config_files_directory = config_files_directory)
    survey = erfs_survey_collection.get_survey('erfs_{}'.format(year))

    log.info("Démarrage de 03_fip")

    # anaisenf is a string containing letter code of pac (F,G,H,I,J,N,R) and year of birth (example: 'F1990H1992')
    # when a child is invalid, he appears twice in anaisenf (example: F1900G1900 is a single invalid child born in 1990)
    erfFoyVar = ['declar', 'anaisenf']
    foyer = survey.get_values(table = year_specific_by_generic["foyer"], variables = erfFoyVar)
    foyer.replace({'anaisenf': {'NA': np.nan}}, inplace = True)

    log.info("Etape 1 : on récupere les personnes à charge des foyers")
    log.info("    1.1 : Création des codes des enfants")
    foyer['anaisenf'] = foyer['anaisenf'].astype('string')
    nb_pac_max = len(max(foyer['anaisenf'], key=len)) / 5
    log.info("il ya a au maximum {} pac par foyer".format(nb_pac_max))

    # Separating the string coding the pac of each "déclaration".
    # Creating a list containing the new variables.

    # Creating the multi_index for the columns
    multi_index_columns = []
    assert int(nb_pac_max) == nb_pac_max, "nb_pac_max = {} which is not an integer".format(nb_pac_max)
    nb_pac_max = int(nb_pac_max)
    for i in range(1, nb_pac_max + 1):
        pac_tuples_list = [
            (i, 'declaration'),
            (i, 'type_pac'),
            (i, 'naia')
            ]
        multi_index_columns += pac_tuples_list

    columns = MultiIndex.from_tuples(
        multi_index_columns,
        names = ['pac_number', 'variable']
        )
    fip = DataFrame(np.random.randn(len(foyer), 3 * nb_pac_max), columns = columns)

    for i in range(1, nb_pac_max + 1):  # TODO: using values to deal with mismatching indexes
        fip[(i, 'declaration')] = foyer['declar'].values
        fip[(i, 'type_pac')] = foyer['anaisenf'].str[5 * (i - 1)].values
        fip[(i, 'naia')] = foyer['anaisenf'].str[5 * (i - 1) + 1: 5 * i].values

    fip = fip.stack("pac_number")
    fip.reset_index(inplace = True)
    fip.drop(['level_0'], axis = 1, inplace = True)

    log.info("    1.2 : elimination des foyers fiscaux sans pac")
    # Clearing missing values and changing data format
    fip = fip[(fip.type_pac.notnull()) & (fip.naia != 'an') & (fip.naia != '')].copy()
    fip = fip.sort(columns = ['declaration', 'naia', 'type_pac'])
    fip.set_index(["declaration", "pac_number"], inplace = True)
    fip = fip.reset_index()
    fip.drop(['pac_number'], axis = 1, inplace = True)
    assert fip.type_pac.isin(["F", "G", "H", "I", "J", "N", "R"]).all(), \
        "Certains types de PAC ne sont pas des cases connues"

    # control(fip, debug=True, verbose=True, verbose_columns=['naia'])

    log.info("    1.3 : on enlève les individus F pour lesquels il existe un individu G")
    type_FG = fip[fip.type_pac.isin(['F', 'G'])].copy()  # Filtre pour ne travailler que sur F & G

    type_FG['same_pair'] = type_FG.duplicated(subset = ['declaration', 'naia'], take_last = True)
    type_FG['is_twin'] = type_FG.duplicated(subset = ['declaration', 'naia', 'type_pac'])
    type_FG['to_keep'] = ~(type_FG['same_pair']) | type_FG['is_twin']
    # Note : On conserve ceux qui ont des couples déclar/naia différents et les jumeaux
    #       puis on retire les autres (à la fois F et G)
    fip['to_keep'] = np.nan
    fip.update(type_FG)
    log.info("    1.4 : on enlève les H pour lesquels il y a un I")
    type_HI = fip[fip.type_pac.isin(['H', 'I'])].copy()
    type_HI['same_pair'] = type_HI.duplicated(subset = ['declaration', 'naia'], take_last = True)
    type_HI['is_twin'] = type_HI.duplicated(subset = ['declaration', 'naia', 'type_pac'])
    type_HI['to_keep'] = (~(type_HI['same_pair']) | (type_HI['is_twin'])).values

    fip.update(type_HI)
    fip['to_keep'] = fip['to_keep'].fillna(True)
    log.info("{} F, G, H or I non redundant pac kept over {} potential candidates".format(
        fip['to_keep'].sum(), len(fip))
        )
    indivifip = fip[fip['to_keep']].copy()
    del indivifip['to_keep'], fip, type_FG, type_HI
    #
    # control(indivifip, debug=True)

    log.info("Step 2 : matching indivifip with eec file")
    indivi = temporary_store['indivim_{}'.format(year)]
    pac = indivi[(indivi.persfip.notnull()) & (indivi.persfip == 'pac')].copy()
    assert indivifip.naia.notnull().all(), "Il y a des valeurs manquantes de la variable naia"

    # For safety enforce pac.naia and indivifip.naia dtypes
    pac['naia'] = pac.naia.astype('int32')
    indivifip['naia'] = indivifip.naia.astype('int32')
    pac['key1'] = zip(pac.naia, pac['declar1'].str[:29])
    pac['key2'] = zip(pac.naia, pac['declar2'].str[:29])
    indivifip['key'] = zip(indivifip.naia.values, indivifip['declaration'].str[:29].values)
    assert pac.naia.dtype == indivifip.naia.dtype, \
        "Les dtypes de pac.naia {} et indvifip.naia {} sont différents".format(pac.naia.dtype, indivifip.naia.dtype)

    fip = indivifip[~(indivifip.key.isin(pac.key1.values))].copy()
    fip = fip[~(fip.key.isin(pac.key2.values))].copy()

    log.info("    2.1 new fip created")
    # We build a dataframe to link the pac to their type and noindiv
    tmp_pac1 = pac[['noindiv', 'key1']].copy()
    tmp_pac2 = pac[['noindiv', 'key2']].copy()
    tmp_indivifip = indivifip[['key', 'type_pac', 'naia']].copy()

    pac_ind1 = tmp_pac1.merge(tmp_indivifip, left_on='key1', right_on='key', how='inner')
    log.info("{} pac dans les 1ères déclarations".format(len(pac_ind1)))
    pac_ind2 = tmp_pac2.merge(tmp_indivifip, left_on='key2', right_on='key', how='inner')
    log.info("{} pac dans les 2èms déclarations".format(len(pac_ind2)))

    log.info("{} duplicated pac_ind1".format(pac_ind1.duplicated().sum()))
    log.info("{} duplicated pac_ind2".format(pac_ind2.duplicated().sum()))

    del pac_ind1['key1'], pac_ind2['key2']

    if len(pac_ind1.index) == 0:
        if len(pac_ind2.index) == 0:
            log.info("Warning : no link between pac and noindiv for both pacInd1&2")
        else:
            log.info("Warning : pacInd1 is an empty data frame")
            pacInd = pac_ind2
    elif len(pac_ind2.index) == 0:
        log.info("Warning : pacInd2 is an empty data frame")
        pacInd = pac_ind1
    else:
        pacInd = concat([pac_ind2, pac_ind1])
    assert len(pac_ind1) + len(pac_ind2) == len(pacInd)
    log.info("{} null pac_ind2.type_pac".format(pac_ind2.type_pac.isnull().sum()))
    log.info("pacInd.type_pac.value_counts()) \n {}".format(pacInd.type_pac.value_counts(dropna = False)))

    log.info("    2.2 : pacInd created")
    log.info("doublons noindiv, type_pac {}".format(pacInd.duplicated(['noindiv', 'type_pac']).sum()))
    log.info("doublons noindiv seulement {}".format(pacInd.duplicated('noindiv').sum()))
    log.info("nb de NaN {}".format(pacInd.type_pac.isnull().sum()))

    del pacInd["key"]
    pacIndiv = pacInd[~(pacInd.duplicated('noindiv'))].copy()
    # pacIndiv.reset_index(inplace=True)
    log.info("{}".format(pacIndiv.columns))

    temporary_store['pacIndiv_{}'.format(year)] = pacIndiv

    log.info("{}".format(pacIndiv.type_pac.value_counts()))
    gc.collect()

    # We keep the fip in the menage of their parents because it is used in to
    # build the famille. We should build an individual ident (ménage) for the fip that are
    # older than 18 since they are not in their parents' menage according to the eec
    log.info("{}".format(indivi['declar1'].str[0:2].value_counts()))
    log.info("{}".format(indivi['declar1'].str[0:2].describe()))
    log.info("{}".format(indivi['declar1'].str[0:2].notnull().all()))
    log.info("{}".format(indivi.info()))
    selection = indivi['declar1'].str[0:2] != ""
    indivi['noidec'] = indivi.declar1[selection].str[0:2].astype('int32')  # To be used later to set idfoy

    individec1 = indivi[(indivi.declar1.isin(fip.declaration.values)) & (indivi.persfip == "vous")]
    individec1 = individec1[["declar1", "noidec", "ident", "rga", "ztsai", "ztsao"]].copy()
    individec1 = individec1.rename(columns = {'declar1': 'declaration'})
    fip1 = fip.merge(individec1, on = 'declaration')
    log.info("    2.3 : fip1 created")

    individec2 = indivi.loc[
        (indivi.declar2.isin(fip.declaration.values)) & (indivi['persfip'] == "vous"),
        ["declar2", "noidec", "ident", "rga", "ztsai", "ztsao"]
        ].copy()
    individec2.rename(columns = {'declar2': 'declaration'}, inplace = True)
    fip2 = fip.merge(individec2)
    log.info("    2.4 : fip2 created")

    fip1.duplicated().value_counts()
    fip2.duplicated().value_counts()

    fip = concat([fip1, fip2])

    fip['persfip'] = 'pac'
    fip['year'] = year
    fip['year'] = fip['year'].astype('float')  # BUG; pas de colonne année dans la DF
    fip['noi'] = 99
    fip['noicon'] = None
    fip['noindiv'] = fip['declaration'].copy()
    fip['noiper'] = None
    fip['noimer'] = None
    fip['declar1'] = fip['declaration'].copy()
    fip['naim'] = 99
    fip['lien'] = None
    fip['quelfic'] = 'FIP'
    fip['acteu'] = None
    fip['agepf'] = fip['year'] - fip.naia.astype('float')
    fip['lpr'] = (fip['agepf'] <= 20) * 3 + (fip['agepf'] > 20) * 4
    fip['stc'] = None
    fip['contra'] = None
    fip['titc'] = None
    fip['mrec'] = None
    fip['forter'] = None
    fip['rstg'] = None
    fip['retrai'] = None
    fip['cohab'] = None
    fip['sexe'] = None
    fip['persfip'] = "pac"
    fip['agepr'] = None
    fip['actrec'] = (fip['agepf'] <= 15) * 9 + (fip['agepf'] > 15) * 5

    # TODO: probleme actrec des enfants fip entre 16 et 20 ans : on ne sait pas s'ils sont étudiants ou salariés */
    # TODO problème avec les mois des enfants FIP : voir si on ne peut pas remonter à ces valeurs: Alexis: clairement non

    # Reassigning noi for fip children if they are more than one per foyer fiscal
    fip["noi"] = fip["noi"].astype("int64")
    fip["ident"] = fip["ident"].astype("int64")

    fip_tmp = fip[['noi', 'ident']]

    while any(fip.duplicated(subset = ['noi', 'ident'])):
        fip_tmp = fip.loc[:, ['noi', 'ident']]
        dup = fip_tmp.duplicated()
        tmp = fip.loc[dup, 'noi']
        log.info("{}".format(len(tmp)))
        fip.loc[dup, 'noi'] = tmp.astype('int64') - 1

    fip['idfoy'] = 100 * fip['ident'] + fip['noidec']
    fip['noindiv'] = 100 * fip['ident'] + fip['noi']
    fip['type_pac'] = 0
    fip['key'] = 0

    log.info("Number of duplicated fip: {}".format(fip.duplicated('noindiv').value_counts()))
    temporary_store['fipDat_{}'.format(year)] = fip
    del fip, fip1, individec1, indivifip, indivi, pac
    log.info("fip sauvegardé")


if __name__ == '__main__':
    year = 2009
    logging.basicConfig(level = logging.INFO, filename = 'step_03.log', filemode = 'w')
    create_fip(year = year)
    log.info("etape 03 fichier des personnes imposables terminée")

#! /usr/bin/env python
import gc

import logging
import numpy as np
from numpy import where, NaN, random
from pandas import read_csv
import os



from openfisca_survey_manager.temporary import temporary_store_decorator
from openfisca_france_data.utils import (
    check_structure,
    control,
    normalizes_roles_in_entity,
    id_formatter,
    print_id,
    rectify_dtype,
    set_variables_default_value,
    )

log = logging.getLogger(__name__)


@temporary_store_decorator(file_name = 'erfs')
def final(temporary_store = None, year = None, check = True):

    assert temporary_store is not None
    assert year is not None

    log.info(u'08_final: derniers réglages')

    # On définit comme célibataires les individus dont on n'a pas retrouvé la déclaration
    final = temporary_store['final_{}'.format(year)]

    if year == 2009:
        final = normalizes_roles_in_entity(final, 'foy')
        final = normalizes_roles_in_entity(final, 'men')

    if check:
        check_structure(final)

    final.statmarit.fillna(2, inplace = True)

    # activite des fip
    log.info('    gestion des FIP de final')
    final_fip = final.loc[final.quelfic.isin(["FIP", "FIP_IMP"]), ["choi", "sali", "alr", "rsti", "age"]].copy()

    log.info(set(["choi", "sali", "alr", "rsti"]).difference(set(final_fip.columns)))
    for var in ["choi", "sali", "alr", "rsti"]:
        final_fip[var].fillna(0, inplace = True)
        assert final_fip[var].notnull().all(), "Some NaN are remaining in column {}".format(var)

    final_fip["activite"] = 2  # TODO comment choisr la valeur par défaut ?
    final_fip.activite = where(final_fip.choi > 0, 1, final_fip.activite)
    final_fip.activite = where(final_fip.sali > 0, 0, final_fip.activite)
    final_fip.activite = where(final_fip.age > 21, 2, final_fip.activite)  # ne peuvent être rattachés que les étudiants

    final.update(final_fip)
    temporary_store['final_{}'.format(year)] = final
    log.info("final has been updated with fip")

    menagem = temporary_store['menagem_{}'.format(year)]
    assert 'ident' in menagem.columns
    assert 'so' in menagem.columns
    menagem.rename(
        columns = dict(ident = "idmen", so = "statut_occupation"),
        inplace = True
        )
    menagem["cstotpragr"] = np.floor(menagem["cstotpr"] / 10)

    # 2008 tau99 removed TODO: check ! and check incidence
    variables = [
        "champm",
        "cstotpragr",
        "ddipl",
        "idmen",
        "nbinde",
        "pol99",
        "reg",
        "statut_occupation",
        "tau99",
        "tu99",
        "typmen15",
        "wprm",
        "zthabm",
        ]
    if year == 2008:
        variables.remove("tau99")
    famille_variables = ["m_afeamam", "m_agedm", "m_clcam", "m_colcam", 'm_mgamm', 'm_mgdomm']

    if 'loyer' in menagem.columns:
        variables.append('loyer')
# if ("naf16pr" %in% names(menagem)) {
#   naf16pr <- factor(menagem$naf16pr)
#   levels(naf16pr) <-  0:16
#   menagem$naf16pr <- as.character(naf16pr)
#   menagem[is.na(menagem$naf16pr), "naf16pr" ] <- "-1"  # Sans objet
#   variables <- c(variables,"naf16pr")
# } else if ("nafg17npr" %in% names(menagem)) {
#   # TODO: pb in 2008 with xx
#   if (year == "2008"){
#     menagem[ menagem$nafg17npr == "xx" & !is.na(menagem$nafg17npr), "nafg17npr"] <- "00"
#   }
#   nafg17npr <- factor(menagem$nafg17npr)
#   levels(nafg17npr) <-  0:17
#   menagem$nafg17npr <- as.character(nafg17npr)
#   menagem[is.na(menagem$nafg17npr), "nafg17npr" ] <- "-1"  # Sans objet
# }
#
# TODO: pytohn translation needed
#    if "naf16pr" in menagem.columns:
#        naf16pr <- factor(menagem$naf16pr)
#   levels(naf16pr) <-  0:16
#   menagem$naf16pr <- as.character(naf16pr)
#   menagem[is.na(menagem$naf16pr), "naf16pr" ] <- "-1"  # Sans objet
#   variables <- c(variables,"naf16pr")
# } else if ("nafg17npr" %in% names(menagem)) {
#   # TODO: pb in 2008 with xx
#   if (year == "2008"){
#     menagem[ menagem$nafg17npr == "xx" & !is.na(menagem$nafg17npr), "nafg17npr"] <- "00"
#   }
#   nafg17npr <- factor(menagem$nafg17npr)
#   levels(nafg17npr) <-  0:17
#   menagem$nafg17npr <- as.character(nafg17npr)
#   menagem[is.na(menagem$nafg17npr), "nafg17npr" ] <- "-1"  # Sans objet
# }
    # TODO: 2008tau99 is not present should be provided by 02_loy.... is it really needed
    all_variables = variables + famille_variables

    log.info("liste de toutes les variables : {}".format(all_variables))
    log.info(menagem.info())
    available_variables = list(set(all_variables).intersection(set(menagem.columns)))
    log.info("liste des variables à extraire de menagem: {}".format(available_variables))
    loyersMenages = menagem[available_variables].copy()
#
# # Recodage de typmen15: modalités de 1:15
# table(loyersMenages$typmen15, useNA="ifany")
# loyersMenages <- within(loyersMenages, {
#   typmen15[typmen15==10 ] <- 1
#   typmen15[typmen15==11 ] <- 2
#   typmen15[typmen15==21 ] <- 3
#   typmen15[typmen15==22 ] <- 4
#   typmen15[typmen15==23 ] <- 5
#   typmen15[typmen15==31 ] <- 6
#   typmen15[typmen15==32 ] <- 7
#   typmen15[typmen15==33 ] <- 8
#   typmen15[typmen15==41 ] <- 9
#   typmen15[typmen15==42 ] <- 10
#   typmen15[typmen15==43 ] <- 11
#   typmen15[typmen15==44 ] <- 12
#   typmen15[typmen15==51 ] <- 13
#   typmen15[typmen15==52 ] <- 14
#   typmen15[typmen15==53 ] <- 15
# })
#
#
# TODO: MBJ UNNECESSARY ?
#
# # Pb avec ddipl, pas de modalités 2: on décale les chaps >=3
# # Cependant on fait cela après avoir fait les traitement suivants
# table(loyersMenages$ddipl, useNA="ifany")
# # On convertit les ddipl en numeric
# loyersMenages$ddipl <- as.numeric(loyersMenages$ddipl)
# table(loyersMenages$ddipl, useNA="ifany")
# #   On met les non renseignés ie, NA et "" à sans diplome (modalité 7)
# loyersMenages[is.na(loyersMenages$ddipl), "ddipl"] <- 7
#
# loyersMenages[loyersMenages$ddipl>1, "ddipl"] <- loyersMenages$ddipl[loyersMenages$ddipl>1]-1
#
    log.info("loyersMenages \n {}".format(loyersMenages.info()))
    loyersMenages.ddipl = where(loyersMenages.ddipl.isnull(), 7, loyersMenages.ddipl)
    loyersMenages.ddipl = where(loyersMenages.ddipl > 1,
                                loyersMenages.ddipl - 1,
                                loyersMenages.ddipl)
    loyersMenages.ddipl = loyersMenages.ddipl.astype("int32")

    final['act5'] = NaN
    final.act5 = where(final.actrec == 1, 2, final.act5)  # indépendants
    final.act5 = where(final.actrec.isin([2, 3]), 1, final.act5)  # salariés

    final.act5 = where(final.actrec == 4, 3, final.act5)  # chômeur
    final.act5 = where(final.actrec == 7, 4, final.act5)  # retraité
    final.act5 = where(final.actrec == 8, 5, final.act5)  # autres inactifs

    log.info("Valeurs prises par act5: \n {}".format(final.act5.value_counts()))

#     assert final.act5.notnull().all(), 'there are NaN inside final.act5'
# final$wprm <- NULL # with the intention to extract wprm from menage to deal with FIPs
# final$taxe_habitation <- final$zthabm # rename zthabm to taxe_habitation
# final$zthabm <- NULL
#
# final2 <- merge(final, loyersMenages, by="idmen", all.x=TRUE)
    log.info('    création de final2')
    del final["wprm"]
    gc.collect()
    final.rename(columns = dict(zthabm = "taxe_habitation"), inplace = True)  # rename zthabm to taxe_habitation
    final2 = final.merge(loyersMenages, on = "idmen", how = "left")  # TODO: Check
    log.info("{}".format(loyersMenages.head()))
    gc.collect()
    print_id(final2)
# # TODO: merging with patrimoine
    log.info('    traitement des zones apl')
    import pkg_resources
    openfisca_france_data_location = pkg_resources.get_distribution('openfisca-france-data').location
    zone_apl_imputation_data_file_path = os.path.join(
        openfisca_france_data_location,
        'openfisca_france_data',
        'zone_apl_data',
        'zone_apl',
        'zone_apl_imputation_data.csv',
        )
    apl_imp = read_csv(zone_apl_imputation_data_file_path)

    log.info("{}".format(apl_imp.head(10)))
    if year == 2008:
        zone_apl = final2.xs(["tu99", "pol99", "reg"], axis = 1)
    else:
        zone_apl = final2.xs(["tu99", "pol99", "tau99", "reg"], axis = 1)

    for i in range(len(apl_imp["TU99"])):
        tu = apl_imp["TU99"][i]
        pol = apl_imp["POL99"][i]
        tau = apl_imp["TAU99"][i]
        reg = apl_imp["REG"][i]

    if year == 2008:
        indices = (final2["tu99"] == tu) & (final2["pol99"] == pol) & (final2["reg"] == reg)
        selection = (apl_imp["TU99"] == tu) & (apl_imp["POL99"] == pol) & (apl_imp["REG"] == reg)
    else:
        indices = (final2["tu99"] == tu) & (final2["pol99"] == pol) & (final2["tau99"] == tau) & (final2["reg"] == reg)
        selection = (
            (apl_imp["TU99"] == tu) &
            (apl_imp["POL99"] == pol) &
            (apl_imp["TAU99"] == tau) &
            (apl_imp["REG"] == reg)
            )

    z = random.uniform(size=indices.sum())
    log.info(len(z))
    log.info(len(indices))
    log.info(len(indices) / len(z))
    probs = apl_imp[["proba_zone1", "proba_zone2"]][selection].copy()
    log.info(probs)
    log.info(probs['proba_zone1'].values)
    proba_zone_1 = probs['proba_zone1'].values[0]
    proba_zone_2 = probs['proba_zone2'].values[0]

    final2["zone_apl"] = 3
    final2.zone_apl.loc[indices] = (
        1 + (z > proba_zone_1) + (z > (proba_zone_1 + proba_zone_2))
        )
    del indices, probs

    log.info('    performing cleaning on final2')
    log.info('{} sali nuls'.format(len(final2[final2['sali'].isnull()])))
    log.info("{} individus d'âges nuls".format(len(final2[final2.age.isnull()])))
    log.info("longueur de final2 avant purge : {}".format(len(final2)))
    log.info('check doublons : {}'.format(len(final2[final2.duplicated(['noindiv'])])))
    log.info("{}".format(final2.age.isnull().sum()))

    print_id(final2)

    control(final2, debug = True)
    temporary_store['final2'] = final2
    log.info("Nombre de personne d'âge NaN: {} ".format(final2.age.isnull().sum()))
    final2 = final2.drop_duplicates(subset = 'noindiv')

    log.info('    Filter to manage the new 3-tables structures:')
    # On récupère les foyer, famille, ménages qui ont un chef :
    # On ne conserve dans final2 que ces foyers là :
    log.info('final2 avant le filtrage {}'.format(len(final2)))
    print_id(final2)


    liste_fam = final2.loc[final2['quifam'] == 0, 'idfam'].unique()
    log.info("Dropping {} famille".format((~final2.idfam.isin(liste_fam)).sum()))
    final2 = final2.loc[final2.idfam.isin(liste_fam)].copy()

    if check:
        check_structure(final2)

    temporary_store['final2bis'] = final2

    liste_foy = final2.loc[final2['quifoy'] == 0, 'idfoy'].unique()
    log.info("Dropping {} foyers".format((~final2.idfoy.isin(liste_foy)).sum()))
    final2 = final2.loc[final2.idfoy.isin(liste_foy)].copy()


    liste_men = final2.loc[final2['quimen'] == 0, 'idmen'].unique()
    log.info(u"Dropping {} ménages".format((~final2.idmen.isin(liste_men)).sum()))
    final2 = final2.loc[final2.idmen.isin(liste_men)].copy()

    log.info('final2 après le filtrage {}'.format(len(final2)))
    print_id(final2)
    rectify_dtype(final2, verbose = False)
    #    home = os.path.expanduser("~")
    #    test_filename = os.path.join(home, filename + ".h5")
    #    if os.path.exists(test_filename):
    #        import warnings
    #        import datetime
    #        time_stamp = datetime.datetime.now().strftime('%Y_%m_%d_%H_%M')
    #        renamed_file = os.path.join(DATA_SOURCES_DIR, filename + "_" + time_stamp + ".h5")
    #        warnings.warn("A file with the same name already exists \n Renaming current output and saving to " + renamed_file)
    #        test_filename = renamed_file
    data_frame = final2

    temporary_store['final3'] = data_frame

    assert not data_frame.duplicated(['idmen', 'quimen']).any(), 'bad ménages indexing'


    if year == 2006:  # Hack crade pur régler un problème rémanent
        data_frame = data_frame[data_frame.idfam != 602177906].copy()

    for id_variable in ['idfam', 'idfoy', 'idmen', 'noi', 'quifam', 'quifoy', 'quimen']:
        data_frame[id_variable] = data_frame[id_variable].astype('int')

    gc.collect()

    if check:
        check_structure(data_frame)
    temporary_store['final4'] = data_frame

    assert not data_frame.duplicated(['idmen', 'quimen']).any(), 'bad ménages indexing'

    gc.collect()
    for entity_id in ['idmen', 'idfoy', 'idfam']:
        log.info('Reformat ids: {}'.format(entity_id))
        data_frame = id_formatter(data_frame, entity_id)

    assert not data_frame.duplicated(['idmen', 'quimen']).any(), 'bad ménages indexing'

    log.info('Dealing with loyer')
    if 'loyer' in data_frame.columns:
        assert 'loyer' in data_frame.columns
        data_frame.loyer = data_frame.loyer * 12.0
    log.info('Set variables to their default values')
    set_variables_default_value(data_frame, year)
    print_id(data_frame)
    temporary_store['input_{}'.format(year)] = data_frame
    return data_frame


if __name__ == '__main__':
    logging.basicConfig(level = logging.INFO, filename = 'step_08.log', filemode = 'w')
    year = 2009
    final(year = year)

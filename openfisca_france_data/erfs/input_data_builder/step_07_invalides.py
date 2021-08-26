#! /usr/bin/env python
import logging


from openfisca_france_data.utils import control, print_id
from openfisca_survey_manager.temporary import temporary_store_decorator


log = logging.getLogger(__name__)


@temporary_store_decorator(file_name = 'erfs')
def invalide(temporary_store = None, year = None):

    assert temporary_store is not None
    assert year is not None

    log.info("Entering 07_invalides: construction de la variable invalide")
# # # Invalides
# # #invalide = caseP (vous), caseF (conj) ou case G, caseI, ou caseR (pac)

# # loadTmp("final.Rdata")
# # invalides <- final[,c("noindiv","idmen","caseP","caseF","idfoy","quifoy")]
# # invalides <- within(invalides,{
# #   caseP <- ifelse(is.na(caseP),0,caseP)
# #   caseF <- ifelse(is.na(caseF),0,caseF)
# #   invalide <- FALSE})
# # # Les "vous" invalides
# # table(invalides[,c("caseF","quifoy")],useNA="ifany")
# # invalides[(invalides$caseP==1) & (invalides$quifoy=="vous"),"invalide"] <- TRUE
# #

    log.info("Etape 1 : création de la df invalides")
    log.info("    1.1 : déclarants invalides")
    final = temporary_store['final_{}'.format(year)]
    if "invalide" in final:
        # on drop les colonnes inv et alt au cas ou on aurait déjà lancé le step07
        final.drop(["invalide", "alt"], axis = 1, inplace = True)

    invalides_vars = [
        "caseF",
        "caseP",
        "idfoy",
        "idmen",
        "noindiv",
        "quifoy",
        ]

    aah_eec_variables = ["rc1rev", "maahe"]
    aah_eec = False

    if set(aah_eec_variables) < set(final.columns):
        aah_eec = True
        invalides_vars += aah_eec_variables

    assert set(invalides_vars) < set(final.columns), \
        "Variables {} are missing".format(set(invalides_vars).difference(set(final.columns)))

    invalides = final.xs(invalides_vars, axis = 1).copy()

    invalides['invalide'] = False
    invalides['alt'] = False
    for var in ["caseP", "caseF"]:
        assert invalides[var].notnull().all(), 'NaN values in {}'.format(var)

    # Les déclarants invalides
    invalides.loc[(invalides['caseP'] == 1) & (invalides['quifoy'] == 0), 'invalide'] = True
    log.info("Il y a {} invalides déclarants".format(invalides["invalide"].sum()))

    # Les personnes qui touchent l'aah dans l'enquête emploi
    if aah_eec:
        log.info("Inspecting rc1rev")
        log.info(invalides['rc1rev'].value_counts())
        invalides.loc[invalides.maahe > 0, 'invalide'] = True
        invalides.loc[invalides.rc1rev == 4, 'invalide'] = True  # TODO: vérifier le format.
#  TODO:      invalides.rc1rev.astype("str") voir mai mahdi pour pendre en compte 14 24 etc

        log.info("Il y a {} invalides qui touchent des alloc".format(invalides["invalide"].sum()))

    print_id(invalides)

# # # Les conjoints invalides
# #
# # #men_inv_conj <- invalides[c("idmen","caseF","quifoy")]
# # #men_inv_conj <- rename(men_inv_conj, c("caseF"="invalide"))
# # #table(men_inv_conj[men_inv_conj$inv==1 ,c("invalide","quifoy")],useNA="ifany")
# # # Il y a des caseF suir des conjoints cela vint des doubles d?clarations TODO: shoumd clean this
# # #toto <- invalides[invalides$caseF==1 & invalides$quifoy=="conj","idmen"]
# # #load(indm)
# # #titi <- indivim[(indivim$ident %in% toto) & (indivim$persfip=="vous" |indivim$persfip=="conj") ,c("ident","noindiv","declar1","declar2","persfip","quelfic")]
# # #titi <- titi[order(titi$ident),]
# # foy_inv_conj <- invalides[,c("idfoy","caseF","quifoy")]
# # foy_inv_conj <- rename(foy_inv_conj, c("caseF"="invalide"))
# # table(foy_inv_conj[ ,c("invalide","quifoy")],useNA="ifany")
# # # On ne garde donc que les caseF des "vous"

# # foy_inv_conj   <- foy_inv_conj[foy_inv_conj$quifoy=="vous",c("idfoy","invalide")]
# # table(foy_inv_conj[ ,c("invalide")],useNA="ifany")
# # invalides_conj <- invalides[invalides$quifoy=="conj",c("idfoy","noindiv")]
# # invalides_conj <- merge(invalides_conj, foy_inv_conj, by="idfoy", all.x=TRUE)
# # table(invalides_conj$inv) # TODO en 2006 On en a 316 au lieu de 328 il doit y avoir de idfoy avec caseF qui n'ont pas de vous because double déclaration'
# # invalides[invalides$quifoy=="conj",c("idfoy","noindiv","invalide")] <- invalides_conj
# # table(invalides[,c("invalide","quifoy")],useNA="ifany")
# # rm(invalides_conj,foy_inv_conj)

    # On récupère les idfoy des foyers avec une caseF cochée
    log.info('    1.2 : Les conjoints invalides')
    idfoy_inv_conj = final.idfoy[final.caseF].copy()
    inv_conj_condition = (invalides.idfoy.isin(idfoy_inv_conj) & (invalides.quifoy == 1))
    invalides.loc[inv_conj_condition, "invalide"] = True

    log.info("Il y a {} invalides conjoints".format(len(invalides[inv_conj_condition])))
    log.info(" Il y a {} invalides déclarants et invalides conjoints".format(invalides["invalide"].sum()))

    # Enfants invalides et garde alternée
    # #
    # # loadTmp("pacIndiv.Rdata")
    # # foy_inv_pac <- invalides[!(invalides$quifoy %in% c("vous","conj")),c("invalide","noindiv")]
    # # foy_inv_pac <- merge(foy_inv_pac, pacIndiv[,c("noindiv","typ","naia")], by="noindiv",all.x =TRUE)
    # # names(foy_inv_pac)
    # # table(foy_inv_pac[,c("typ","naia")],useNA="ifany")
    # # table(foy_inv_pac[,c("typ")],useNA="ifany")
    # # foy_inv_pac <- within(foy_inv_pac,{
    # #   invalide  <- (typ=="G") | (typ=="R") | (typ=="I") | (typ=="F" & (as.numeric(year)-naia>18))
    # #   alt  <- (typ=="H") | (typ=="I")
    # #   naia <- NULL
    # #   typ  <- NULL})
    # #
    # # table(foy_inv_pac[ ,c("invalide")],useNA="ifany")
    # # table(foy_inv_pac[ ,c("alt")],useNA="ifany")
    # # invalides$alt <- 0
    # # foy_inv_pac[is.na(foy_inv_pac$alt),"alt"] <- 0
    # # invalides[!(invalides$quifoy %in% c("vous","conj")),c("noindiv","invalide","alt")] <- foy_inv_pac
    log.info("    1.3 : enfants invalides et en garde alternée (variables inv et alt)")
    pacIndiv = temporary_store['pacIndiv_{}'.format(year)]
    log.info(pacIndiv.type_pac.value_counts())

    foy_inv_pac = invalides[['noindiv', 'invalide']][~(invalides.quifoy.isin([0, 1]))].copy()
    # pac = pacIndiv.ix[:, ["noindiv", "type_pac", "naia"]]
    log.info("{}".format(len(foy_inv_pac)))

    log.info("{}".format(pacIndiv.columns))
    foy_inv_pac = foy_inv_pac.merge(
        pacIndiv[['noindiv', 'type_pac', 'naia']].copy(),
        on = 'noindiv',
        how = 'left',
        )
    foy_inv_pac['invalide'] = (
        foy_inv_pac['type_pac'].isin(['G', 'R', 'I']) |
        (
            (foy_inv_pac.type_pac == "F") & ((year - foy_inv_pac.naia) > 18)
            )
        )
    foy_inv_pac['alt'] = ((foy_inv_pac.type_pac == "H") | (foy_inv_pac.type_pac == "I"))
    del foy_inv_pac['naia']
    del foy_inv_pac['type_pac']
    foy_inv_pac['alt'] = foy_inv_pac['alt'].fillna(False)

    log.info("{}".format(foy_inv_pac['invalide'].describe()))
    invalides.loc[:, 'alt'] = False
    invalides.loc[~(invalides.quifoy.isin([0, 1])), ["alt", "invalide"]] = foy_inv_pac[["alt", "invalide"]].copy().values
    invalides = invalides[["noindiv", "invalide", 'alt']].copy()
    invalides['alt'].fillna(False, inplace = True)

    log.info(invalides.invalide.value_counts())
    # invalides = invalides.drop_duplicates(['noindiv', 'invalide', 'alt'], take_last = True)
    del foy_inv_pac, pacIndiv

    # Initialisation des NA sur alt et inv
    # invalides[is.na(invalides$inv), "invalide"] <- 0
    # table(invalides[,c("alt","invalide")],useNA="ifany")
    #
    # final <- merge(final, invalides[,c("noindiv","invalide","alt")], by="noindiv",all.x=TRUE)
    # table(final[, c("invalide","alt")],useNA="ifany")

    log.info('Etape 2 : Initialisation des NA sur alt et inv')
    assert invalides.invalide.notnull().all() & invalides.alt.notnull().all()
    final.set_index('noindiv', inplace = True, verify_integrity = True)
    invalides.set_index('noindiv', inplace = True, verify_integrity = True)
    final = final.join(invalides)
    final.reset_index(inplace = True)
    del invalides

    log.info("{}".format(final.invalide.value_counts()))
    control(final, debug = True)

    temporary_store['final_{}'.format(year)] = final
    log.info(u'final complétée et sauvegardée')

if __name__ == '__main__':
    logging.basicConfig(level = logging.INFO, filename = 'step_07.log', filemode = 'w')
    year = 2009
    invalide(year = year)
    log.info("étape 07 création des invalides terminée")

#! /usr/bin/env python
# -*- coding: utf-8 -*-


# OpenFisca -- A versatile microsimulation software
# By: OpenFisca Team <contact@openfisca.fr>
#
# Copyright (C) 2011, 2012, 2013, 2014 OpenFisca Team
# https://github.com/openfisca
#
# This file is part of OpenFisca.
#
# OpenFisca is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# OpenFisca is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
from numpy import where, array
from pandas import concat, DataFrame


from openfisca_france_data.build_openfisca_survey_data import load_temp, save_temp
from openfisca_france_data.build_openfisca_survey_data.utilitaries import assert_dtype

log = logging.getLogger(__name__)

# Retreives the families
# Creates 'idfam' and 'quifam' variables


def control_04(dataframe, base):
    log.info(u"longueur de la dataframe après opération :".format(len(dataframe.index)))
    log.info(u"contrôle des doublons : il y a {} individus en double".format(any(dataframe.duplicated(cols='noindiv'))))
    log.info(u"contrôle des colonnes : il y a {} colonnes".format(len(dataframe.columns)))
    log.info(u"Il y a {} de familles différentes".format(len(set(dataframe.noifam.values))))
    log.info(u"contrôle: {} noifam are NaN:".format(len(dataframe[dataframe['noifam'].isnull()])))
    log.info(u"{} lignes dans dataframe vs {} lignes dans base".format(len(dataframe.index), len(base.index)))
    assert len(dataframe.index) <= len(base.index), u"dataframe has too many rows compared to base"


def subset_base(base, famille):
    """
    Generates a dataframe containing the values of base that are not already in famille
    """
    return base[~(base.noindiv.isin(famille.noindiv.values))].copy()


def famille(year = 2006):

    log.info('step_04_famille: construction de la table famille')

### On suit la méthode décrite dans le Guide ERF_2002_rétropolée page 135
    # TODO: extraire ces valeurs d'un fichier de paramètres de législation
    if year == 2006:
        smic = 1254
    elif year == 2007:
        smic = 1280
    elif year == 2008:
        smic = 1308
    elif year == 2009:
        smic = 1337
    else:
        print("smic non défini")

## TODO check if we can remove acteu forter etc since dealt with in 01_pre_proc

    print 'Etape 1 : préparation de base'
    print '    1.1 : récupération de indivi'
    indivi = load_temp(name="indivim", year=year)

    indivi['year'] = year
    indivi["noidec"] = indivi["declar1"].str[0:2]
    indivi["agepf"] = (
        (indivi.naim < 7) * (indivi.year - indivi.naia)
        + (indivi.naim >= 7) * (indivi.year - indivi.naia - 1)
        ).astype(object)  # TODO: naia has some NaN but naim do not and then should be an int

    indivi = indivi[ ~(
        (indivi.lien == 6) & (indivi.agepf < 16) & (indivi.quelfic == "EE")
        )].copy()

    assert_dtype(indivi.year, "int64")
    for series_name in ['agepf', 'noidec']:  # integer with NaN
        assert_dtype(indivi[series_name], "object")

    log.info('    1.2 : récupération des enfants à naître')
    individual_variables = [
        'acteu',
        'actrec',
        'agepf',
        'agepr',
        'cohab',
        'contra',
        'declar1',
        'forter',
        'ident',
        'lien',
        'lpr',
        'mrec',
        'naia',
        'naim',
        'noi',
        'noicon',
        'noidec',
        'noimer',
        'noindiv',
        'noiper',
        'persfip',
        'quelfic',
        'retrai',
        'rga',
        'rstg',
        'sexe',
        'stc',
        'titc',
        'year',
        'ztsai',
        ]
    enfants_a_naitre = load_temp(name = 'enfants_a_naitre', variables = individual_variables, year = year)
    enfants_a_naitre.drop_duplicates('noindiv', inplace = True)
    log.info(u""""
    Il y a {} enfants à naitre avant de retirer ceux qui ne sont pas enfants
    de la personne de référence
    """.format(len(enfants_a_naitre.index)))
    enfants_a_naitre = enfants_a_naitre[enfants_a_naitre.lpr == 3].copy()
    enfants_a_naitre = enfants_a_naitre[~(enfants_a_naitre.noindiv.isin(indivi.noindiv.values))].copy()
    log.info(u""""
    Il y a {} enfants à naitre après avoir retiré ceux qui ne sont pas enfants
    de la personne de référence
    """.format(len(enfants_a_naitre.index)))
    # PB with vars "agepf"  "noidec" "year"  NOTE: quels problèmes ? JS
    log.info(u"    1.3 : création de la base complète")
    base = concat([indivi, enfants_a_naitre])
    log.info(u"base contient {} lignes ".format(len(base.index)))
    base['noindiv'] = (100 * base['ident'] + base['noi']).astype(int)
    base['m15'] = base['agepf'] < 16
    base['p16m20'] = (base['agepf'] >= 16) & (base['agepf'] <= 20)
    base['p21'] = base['agepf'] >= 21
    base['ztsai'].fillna(0, inplace = True)
    base['smic55'] = base['ztsai'] >= (smic * 12 * 0.55)  # 55% du smic mensuel brut
    base['famille'] = 0
    base['kid'] = False
    for series_name in ['kid', 'm15', 'p16m20', 'p21', 'smic55']:
        assert_dtype(base[series_name], "bool")
    assert_dtype(base.famille, "int")
    assert_dtype(base.ztsai, "int")

    log.info(u"Etape 2 : On cherche les enfants ayant père et/ou mère")
    personne_de_reference = base[['ident', 'noi']][base['lpr'] == 1].copy()
    personne_de_reference['noifam'] = (100 * personne_de_reference['ident'] + personne_de_reference['noi']).astype(int)
    personne_de_reference = personne_de_reference[['ident', 'noifam']].copy()
    log.info(u"length personne_de_reference : {}".format(len(personne_de_reference.index)))
    nof01 = base[(base.lpr.isin([1, 2])) | ((base.lpr == 3) & (base.m15)) |
                 ((base.lpr == 3) & (base.p16m20) & (~base.smic55))].copy()
    log.info('longueur de nof01 avant merge : {}'.format(len(nof01.index)))
    nof01 = nof01.merge(personne_de_reference, on='ident', how='outer')
    nof01['famille'] = 10
    nof01['kid'] = (
        (nof01.lpr == 3) & (nof01.m15)
        ) | (
            (nof01.lpr == 3) & (nof01.p16m20) & ~(nof01.smic55)
            )
    for series_name in ['famille', 'noifam']:
        assert_dtype(nof01[series_name], "int")
    assert_dtype(nof01.kid, "bool")
    famille = nof01.copy()
    del nof01
    control_04(famille, base)

    log.info(u"    2.1 : identification des couples")
    # l'ID est le noi de l'homme

    hcouple = subset_base(base, famille)
    hcouple = hcouple[(hcouple.cohab == 1) & (hcouple.lpr >= 3) & (hcouple.sexe == 1)].copy()
    hcouple['noifam'] = (100 * hcouple.ident + hcouple.noi).astype(int)
    hcouple['famille'] = 21
    for series_name in ['famille', 'noifam']:
        assert_dtype(hcouple[series_name], "int")
    log.info(u"longueur hcouple : ".format(len(hcouple.index)))

    log.info(u"    2.2 : attributing the noifam to the wives")
    fcouple = base[~(base.noindiv.isin(famille.noindiv.values))].copy()
    fcouple = fcouple[(fcouple.cohab == 1) & (fcouple.lpr >= 3) & (fcouple.sexe == 2)].copy()
    # l'identifiant de la famille est celui du conjoint de la personne de référence du ménage
    fcouple['noifam'] = (100 * fcouple.ident + fcouple.noicon).astype(int)
    fcouple['famille'] = 22
    for series_name in ['famille', 'noifam']:
        assert_dtype(fcouple[series_name], "int")
    log.info(u"Il y a {} enfants avec parents en fcouple".format(len(fcouple.index)))

    famcom = fcouple.merge(hcouple, on='noifam', how='outer')
    log.info(u"longueur fancom après fusion : {}".format(len(famcom.index)))
    fcouple = fcouple.merge(famcom)  # TODO : check s'il ne faut pas faire un inner merge sinon présence de doublons
    log.info(u"longueur fcouple après fusion : {}".format(len(fcouple.index)))
    famille = concat([famille, hcouple, fcouple], join='inner')
    control_04(famille, base)

    log.info(u"Etape 3: Récupération des personnes seules")
    log.info(u"    3.1 : personnes seules de catégorie 1")
    seul1 = base[~(base.noindiv.isin(famille.noindiv.values))].copy()
    seul1 = seul1[(seul1.lpr.isin([3, 4])) & ((seul1.p16m20 & seul1.smic55) | seul1.p21) & (seul1.cohab == 1) &
                  (seul1.sexe == 2)].copy()
    if len(seul1.index) > 0:
        seul1['noifam'] = (100 * seul1.ident + seul1.noi).astype(int)
        seul1['famille'] = 31
        for series_name in ['famille', 'noifam']:
            assert_dtype(seul1[series_name], "int")
        famille = concat([famille, seul1])
    control_04(famille, base)

    log.info(u"    3.1 personnes seules de catégorie 2")
    seul2 = base[~(base.noindiv.isin(famille.noindiv.values))].copy()
    seul2 = seul2[(seul2.lpr.isin([3, 4])) & seul2.p16m20 & seul2.smic55 & (seul2.cohab != 1)].copy()
    seul2['noifam'] = (100 * seul2.ident + seul2.noi).astype(int)
    seul2['famille'] = 32
    for series_name in ['famille', 'noifam']:
        assert_dtype(seul2[series_name], "int")
    famille = concat([famille, seul2])
    control_04(famille, base)

    log.info(u"    3.3 personnes seules de catégorie 3")
    seul3 = subset_base(base, famille)
    seul3 = seul3[(seul3.lpr.isin([3, 4])) & seul3.p21 & (seul3.cohab != 1)].copy()
    # TODO: CHECK erreur dans le guide méthodologique ERF 2002 lpr 3,4 au lieu de 3 seulement
    seul3['noifam'] = (100 * seul3.ident + seul3.noi).astype(int)
    seul3['famille'] = 33
    for series_name in ['famille', 'noifam']:
        assert_dtype(seul3[series_name], "int")
    famille = concat([famille, seul3])
    control_04(famille, base)

    log.info(u"    3.4 : personnes seules de catégorie 4")
    seul4 = subset_base(base, famille)
    seul4 = seul4[(seul4.lpr == 4) & seul4.p16m20 & ~(seul4.smic55) & (seul4.noimer.isnull()) &
                  (seul4.persfip == 'vous')].copy()
    if len(seul4.index) > 0:
        seul4['noifam'] = (100 * seul4.ident + seul4.noi).astype(int)
        seul4['famille'] = 34
        famille = concat([famille, seul4])
        for series_name in ['famille', 'noifam']:
            assert_dtype(seul4[series_name], "int")
    control_04(famille, base)

# # message('Etape 4')
# # message(' 4.1 enfant avec mère')
# # avec_mere <- base[(!base$noindiv %in% famille$noindiv),]
# # avec_mere <- subset(avec_mere,((lpr=4) & ( (p16m20=1) | (m15=1))) & noimer!=0)
# #
# # avec_mere <- within(avec_mere,{noifam=100*ident + noimer
# #              famille=41
# #              kid=TRUE})
# #
# # ## on récupère les mères */
# # mereid <- upData(avec_mere['noifam'], rename = c(noifam = 'noindiv'));
# # mereid <- unique(mereid)
# #
# # mere <- merge(mereid,base)
# # mere <- within(mere,{noifam=100*ident + noi
# #                      famille=42})
# #
# # dim(mereid)
# # dim(mere)
# # # TODO on préfère  donc enlever leurs enfants
# # avec_mere <- avec_mere[avec_mere$noifam %in% mere$noifam,]
# #

    log.info(u"Etape 4 : traitement des enfants")
    log.info(u"    4.1 : enfant avec mère")
    avec_mere = subset_base(base,famille)

    avec_mere = avec_mere[((avec_mere.lpr == 4) & ((avec_mere.p16m20 == 1) | (avec_mere.m15 == 1)) &
                           (avec_mere.noimer.notnull()))].copy()

    avec_mere['noifam'] = (100 * avec_mere.ident + avec_mere.noimer).astype(int)
    avec_mere['famille'] = 41
    avec_mere['kid'] = True
    for series_name in ['famille', 'noifam']:
        assert_dtype(avec_mere[series_name], "int")
    assert_dtype(avec_mere.kid, "bool")

    # On récupère les mères des enfants
    mereid = avec_mere['noifam'].copy()
    # Ces mères peuvent avoir plusieurs enfants, or il ne faut unicité de l'identifiant
    mereid.rename({'noifam': 'noindiv'}, inplace=True)
    mereid = mereid.drop_duplicates()
    mere = mereid.merge(base)
    mere['noifam'] = 100 * mere.ident + mere.noi
    mere['famille'] = 42 #H2G2 nous voilà
    avec_mere = avec_mere[avec_mere.noifam.isin(mereid.noindiv.values)]
    print 'contrôle df mère'
    control_04(mere, base)

# # conj_mere <- merge(conj_mereid,base)
# # conj_mere$famille <- 43
# #
# # famille <- famille[(!famille$noindiv %in% mere$noindiv),]
# #
# # ## on récupère les conjoints des mères */
# # conj_mereid <- mere[mere$noicon!=0,c('ident','noicon','noifam')]
# #
# # conj_mereid$noindiv = 100*conj_mereid$ident + conj_mereid$noicon
# # conj_mereid <- conj_mereid[c('noindiv','noifam')]
# #
# # conj_mere <- merge(conj_mereid,base)
# # conj_mere$famille <- 43
# #
# # famille <- famille[(!famille$noindiv %in% conj_mere$noindiv),]
# # famille <- rbind(famille,avec_mere,mere,conj_mere)
# #

    famille = famille[~(famille.noindiv.isin(mere.noindiv.values))]
    control_04(famille, base)

    #on retrouve les conjoints des mères
    conj_mereid = mere[mere['noicon']!=0].loc[:, ['ident', 'noicon', 'noifam']]
    conj_mereid['noindiv'] = 100*conj_mereid['ident'] + conj_mereid['noicon']
    conj_mereid = conj_mereid.loc[:, ['noindiv', 'noifam']]
    conj_mereid = conj_mereid.merge(base)
    control_04(conj_mereid, base)

    conj_mere = conj_mereid.merge(base)
    conj_mere['famille'] = 43

    famille = famille[~(famille.noindiv.isin(conj_mere.noindiv.values))]
    famille = concat([famille, avec_mere, mere, conj_mere])
    control_04(famille, base)
    del avec_mere, mere, conj_mere, mereid, conj_mereid

# # message(' 4.2 enfants avec père')
# # avec_pere <- base[(!base$noindiv %in% famille$noindiv),]
# # avec_pere <- subset(avec_pere,((lpr=4) & ( (p16m20=1) | (m15=1))) & noiper!=0)
# # avec_pere <- within(avec_pere,{noifam=100*ident + noiper
# #              famille=44
# #              kid=TRUE})
# #
# # ## on récupère les pères  pour leur attribuer une famille propre */
# # pereid <- upData(avec_pere['noifam'], rename = c(noifam = 'noindiv'));
# # pereid <- unique(pereid)
# # pere <- merge(pereid,base)
# # pere <- within(pere,{noifam=100*ident + noi
# #                        famille=45})
# #
# # famille <- famille[(!famille$noindiv %in% pere$noindiv),]
# #
# # ## on récupère les conjoints des pères */
# # conj_pereid <- pere[pere$noicon!=0,c('ident','noicon','noifam')]
# # conj_pereid$noindiv = 100*conj_pereid$ident + conj_pereid$noicon
# # conj_pereid <- conj_pereid[c('noindiv','noifam')]
# #
# # conj_pere <- merge(conj_pereid,base)
# # if (nrow(conj_pere) >0) conj_pere$famille <- 46
# # # 2006: erreur pas de conjoint de père ?
# #
# # famille <- famille[(!famille$noindiv %in% conj_pere$noindiv),]
# # famille <- rbind(famille,avec_pere,pere,conj_pere)

    print '    4.2 : enfants avec père'
    avec_pere = subset_base(base,famille)
    avec_pere = avec_pere[(avec_pere['lpr']==4) &
                          ((avec_pere['p16m20']==1) | (avec_pere['m15']==1)) &
                          (avec_pere['noiper'].notnull())]
    avec_pere['noifam'] = 100*avec_pere['ident'] + avec_pere['noiper']
    avec_pere['famille'] = 44
    avec_pere['kid'] = True
    print 'presence of NaN in avec_pere ?', avec_pere['noifam'].isnull().any()


    pereid = DataFrame(avec_pere['noifam']); pereid.columns = ['noindiv']
    pereid = pereid.drop_duplicates()
    pere = base.merge(pereid, on='noindiv', how='inner')

    pere['noifam'] = 100*pere['ident'] + pere['noi']
    pere['famille'] = 45
    famille = famille[~(famille.noindiv.isin(pere.noindiv.values))]

    #On récupère les conjoints des pères
    conj_pereid = pere.loc[array(pere['noicon']!=0), ['ident','noicon','noifam']]
    conj_pereid['noindiv'] = 100*conj_pereid['ident'] + conj_pereid['noicon']
    conj_pereid = conj_pereid.loc[:, ['noindiv','noifam']]

    conj_pere = base.merge(conj_pereid, on=['noindiv'] ,how='inner')
    control_04(conj_pere, base)
    if len(conj_pere.index)>0 : conj_pere['famille'] = 46

    famille = famille[~(famille.noindiv.isin(conj_pere.noindiv.values))]
    famille = concat([famille, avec_pere, pere, conj_pere])
    print 'contrôle de famille après ajout des pères'
    control_04(famille, base)
    del avec_pere,pere,pereid,conj_pere,conj_pereid

# # ##* 42. enfants avec déclarant */
# # avec_dec <- base[(!base$noindiv %in% famille$noindiv),]
# # avec_dec <- subset(avec_dec,(persfip=="pac") & (lpr=4) &  ( (p16m20&!smic55) | (m15=1 )))
# # avec_dec <- within(avec_dec,{noifam = 100*ident + noidec
# #             famille=47
# #             kid=TRUE})
# #
# # ## on récupère les déclarants pour leur attribuer une famille propre */
# # decid <- upData(avec_dec['noifam'], rename = c(noifam = 'noindiv'));
# # decid <- unique(decid)
# #
# # dec <- merge(decid,base)
# # dec <- within(dec,{noifam=100*ident + noi
# #                    famille=48})
# #
# # famille <- famille[(!famille$noindiv %in% dec$noindiv),]
# # famille <- rbind(famille,avec_dec,dec)

    print '    4.3 : enfants avec déclarant'
    avec_dec = subset_base(base,famille)
    avec_dec = avec_dec[(avec_dec['persfip']=="pac") & (avec_dec['lpr']==4) &
                    ( (avec_dec['p16m20'] & ~(avec_dec['smic55'])) | (avec_dec['m15']==1 ))]
    avec_dec['noifam'] = 100*avec_dec['ident'] + avec_dec['noidec'].astype('float')
    avec_dec['famille'] = 47
    avec_dec['kid'] = True
    control_04(avec_dec, base)

    #on récupère les déclarants pour leur attribuer une famille propre
    decid = DataFrame(avec_dec['noifam']) ; decid.columns = ['noindiv']
    decid = decid.drop_duplicates()
    dec = base.merge(decid, how='inner')
    dec['noifam'] = 100*dec['ident'] + dec['noi']
    dec['famille'] = 48

    famille = famille[~(famille.noindiv.isin(dec.noindiv.values))]
    famille = concat([famille, avec_dec, dec])
    del dec, decid, avec_dec
    control_04(famille, base)

# # ## famille etape 5 : enfants fip */
# # message('Etape 5 : enfants fip')
# # # On rajoute les enfants fip
# # # (on le fait ici pour que cela n'interfère pas avec les recherches précédentes)
# # fip <- LoadIn(fipDat)
# #
# # indVar = c('noi','noicon','noindiv','noiper','noimer','ident','declar1','naia','naim','lien','quelfic','acteu','stc','contra','titc','mrec',
# #             'forter','rstg','retrai','lpr','cohab','ztsai','sexe','persfip','agepr','rga')
# #
# # fip <- fip[c(indVar,'actrec','agepf','noidec','year')]
# #
# # table(duplicated(fip$noindiv))
# #
# # ## Variables auxilaires présentes dans base qu'il faut rajouter aux fip'
# # ## WARNING les noindiv des fip sont construits sur les ident des déclarants
# # ## pas d'orvelap possible avec les autres noindiv car on a des noi =99, 98, 97 ,...'
# # names(fip)
# #
# # fip <- within(fip,{
# #   m15 <- (agepf<16)
# #   p16m20 <- ((agepf>=16) & (agepf<=20))
# #   p21 <- (agepf>=21)
# #   ztsai[is.na(ztsai)] <- 0
# #   smic55 <- (ztsai >= smic*12*0.55)   ## 55% du smic mensuel brut */
# #   famille <- 0
# #   kid <- FALSE
# # })

    print ''
    print 'Etape 5 : récupération des enfants fip-----------'
    print '    5.1 : création de la df fip'
    fip = load_temp(name='fipDat', year=year)
    indVar_fip = ['noi','noicon','noindiv','noiper','noimer','ident','declar1','naia','naim','lien','quelfic','acteu','stc','contra','titc','mrec',
            'forter','rstg','retrai','lpr','cohab','ztsai','sexe','persfip','agepr','rga','actrec','agepf','noidec','year']
    fip = fip.loc[:, indVar_fip]

    # Variables auxilaires présentes dans base qu'il faut rajouter aux fip'
    # WARNING les noindiv des fip sont construits sur les ident des déclarants
    # pas d'orvelap possible avec les autres noindiv car on a des noi =99, 98, 97 ,...'
    fip['m15'] = (fip['agepf']<16)
    fip['p16m20'] = ((fip['agepf']>=16) & (fip['agepf']<=20))
    fip['p21'] = (fip['agepf']>=21)
#     fip['ztsai'][fip['ztsai'] is None] = 0 #there are alrdy zeros
    fip['smic55'] = (fip['ztsai'] >= smic*12*0.55)
    fip['famille'] = 0
    fip['kid'] = False
    print fip['ztsai'].isnull().describe()

# # base <- rbind(base,fip)
# # table(base$quelfic)

# # enfant_fip <- base[(!base$noindiv %in% famille$noindiv),]
# # enfant_fip <- subset(enfant_fip, (quelfic=="FIP") & (( (agepf %in% c(19,20)) & !smic55 ) | (naia==year & rga=='6')) )  # TODO check year ou year-1 !
# # enfant_fip <- within(enfant_fip,{
# #                      noifam=100*ident+noidec
# #                      famille=50
# #                      kid=TRUE})
# # #                     ident=NA}) # TODO : je ne sais pas quoi mettre un NA fausse les manips suivantes
# # famille <- rbind(famille,enfant_fip)
# #
# # # TODO: En 2006 on peut faire ce qui suit car tous les parents fip sont déjà dans une famille
# # parent_fip <- famille[famille$noindiv %in% enfant_fip$noifam,]
# # any(enfant_fip$noifam %in% parent_fip$noindiv)
# # parent_fip <- within(parent_fip,{
# #                      noifam <- noindiv
# #                      famille <- 51
# #                      kid <- FALSE})
# # famille[famille$noindiv %in% enfant_fip$noifam,] <- parent_fip
# # # TODO quid du conjoint ?

    print "    5.2 : extension de base avec les fip"
    print fip[['noindiv', 'noidec', 'ztsai']].describe()
    base_ = concat([base, fip])
    print len(base.index)

    enfant_fip = subset_base(base_, famille)
    print enfant_fip.ix[enfant_fip['quelfic']=="FIP","agepf"].describe()

    enfant_fip = enfant_fip[(enfant_fip['quelfic']=="FIP") &
                            ((enfant_fip.agepf.isin([19,20]) & ~(enfant_fip['smic55'])) |
                            ((enfant_fip['naia']==enfant_fip['year']-1) & (enfant_fip['rga'].astype('int')==6)))]

    enfant_fip['noifam'] = 100*enfant_fip['ident'] + enfant_fip['noidec']
    enfant_fip['famille'] = 50
    enfant_fip['kid'] = True
    enfant_fip['ident'] = None
    control_04(enfant_fip, base)

    famille = concat([famille, enfant_fip])
    base = concat([base, enfant_fip])
    parent_fip = famille[famille.noindiv.isin(enfant_fip.noifam.values)].copy()
    print type(parent_fip)
    assert (enfant_fip.noifam.isin(parent_fip.noindiv.values)).any(), "{} doublons entre enfant_fip et parent fip !".format((enfant_fip.noifam.isin(parent_fip.noindiv.values)).sum())

    parent_fip['noifam'] = parent_fip['noindiv'].values.copy()
    parent_fip['famille'] = 51
    parent_fip['kid'] = False
    print 'contrôle de parent_fip'
    control_04(parent_fip, base)

    print 'famille defore merge and clearing'
    control_04(famille, base)

    famille = famille.merge(parent_fip, how='outer'); famille['famille'] = famille['famille'].astype('int')
    famille = famille.drop_duplicates(cols='noindiv', take_last=True)

    print 'famille after merge and clearing'
    print set(famille.famille.values)
    control_04(famille, base)
    print famille.loc[famille.noindiv.isin(enfant_fip.noifam), 'famille'].describe()
    del enfant_fip, fip, parent_fip

# # message('Etape 6 : non attribué')
# # non_attribue1 <- base[(!base$noindiv %in% famille$noindiv),]
# # non_attribue1 <- subset(non_attribue1,
# #                         (quelfic!="FIP") & (m15 | (p16m20&(lien %in% c(1,2,3,4) & agepr>=35)))
# #                         )
# # # On rattache les moins de 15 ans avec la PR (on a déjà éliminé les enfants en nourrice)
# # non_attribue1 <- merge(pr,non_attribue1)
# # non_attribue1 <- within(non_attribue1,{
# #   famille <- ifelse(m15,61,62)
# #     kid <- TRUE })
# #
# # rm(pr)
# # famille <- rbind(famille,non_attribue1)
# # dup <- duplicated(famille$noindiv)
# # table(dup)
# # rm(non_attribue1)
# # table(famille$famille, useNA="ifany")
# #
# # non_attribue2 <- base[(!base$noindiv %in% famille$noindiv) & (base$quelfic!="FIP"),]
# # non_attribue2 <- within(non_attribue2,{
# #   noifam <- 100*ident+noi # l'identifiant est celui du jeune */
# #     kid<-FALSE
# #     famille<-63})
# #
# # famille <- rbind(famille,non_attribue2)
    print ''
    print 'Etape 6 : gestion des non attribués'
    print '    6.1 : non attribués type 1'
    non_attribue1 = subset_base(base,famille)
    non_attribue1 = non_attribue1[~(non_attribue1['quelfic'] != 'FIP') & (non_attribue1['m15'] |
                                    (non_attribue1['p16m20'] & (non_attribue1.lien.isin(range(1,5))) &
                                     (non_attribue1['agepr']>=35)))]
    # On rattache les moins de 15 ans avec la PR (on a déjà éliminé les enfants en nourrice)
    non_attribue1 = personne_de_reference.merge(non_attribue1)
    control_04(non_attribue1, base)
    non_attribue1['famille'] = where(non_attribue1['m15'], 61, 62)
    non_attribue1['kid'] = True

    famille = concat([famille, non_attribue1])
    control_04(famille, base)
    del personne_de_reference, non_attribue1

    print '    6.2 : non attribué type 2'
    non_attribue2 = base[(~(base.noindiv.isin(famille.noindiv.values)) & (base['quelfic']!="FIP"))].copy()
    non_attribue2['noifam'] = 100*non_attribue2['ident'] + non_attribue2['noi']
    non_attribue2['noifam'] = non_attribue2['noifam'].astype('int')
    non_attribue2['kid'] = False
    non_attribue2['famille'] = 63

    famille = concat([famille, non_attribue2], join='inner')
    control_04(famille, base)
    del non_attribue2

# # ## Sauvegarde de la table famille */
# #
# # # TODO: nettoyer les champs qui ne servent plus à rien
# #
    print ''
    print 'Etape 7 : Sauvegarde de la table famille'
    print '    7.1 : Mise en forme finale'
    famille['idec'] = famille['declar1'].str[3:11]
    print famille['declar1'].notnull().describe()
    famille['idec'].apply(lambda x: str(x)+'-')
    famille['idec'] += famille['declar1'].str[0:2]
    famille['chef'] = (famille['noifam'] == famille['ident']*100+famille['noi'])

    famille.reset_index(inplace=True)
    print famille['idec'].isnull().describe()

    control_04(famille, base)

    print '    7.2 : création de la colonne rang'
    famille['rang'] = famille['kid'].astype('int')

    while any(famille[(famille['rang']!=0)].duplicated(cols=['rang', 'noifam'])):
        famille["rang"][famille['rang']!=0] = where(
                                    famille[famille['rang']!=0].duplicated(cols=["rang", 'noifam']),
                                    famille["rang"][famille['rang']!=0] + 1,
                                    famille["rang"][famille['rang']!=0])
        print "nb de rangs différents", len(set(famille.rang.values))

    log.info(u"    7.3 : création de la colonne quifam et troncature")

    log.info(u"value_counts chef : \n {}".format(famille['chef'].value_counts()))
    log.info(u"value_counts kid :' \n {}".format(famille['kid'].value_counts()))


    famille['quifam'] = -1
 #   famille['quifam'] = famille['quifam'].where(famille['chef'].values, 0)
    famille.quifam[famille['chef']] = 0
    famille.quifam[famille['kid']] = 1 + famille.rang[famille['kid']].values
#    famille['quifam'] = famille['quifam'].where(famille['kid'].values, 1 + famille['rang'].values)
    famille.quifam[(~(famille['chef'])) & (~(famille['kid']))] = 1
#    famille['quifam'] = famille['quifam'].where(~(famille['chef'].values) & ~(famille['kid'].values), 1)


    famille['noifam'] = famille['noifam'].astype('int')

    print famille.sort(columns=['noifam','quifam'])
    print famille['quifam'].value_counts()
    print famille['noifam'].value_counts()
    famille_check = famille.copy()
    famille = famille.loc[:, ['noindiv', 'quifam', 'noifam']].copy()
    print famille.info()
    print famille.describe()
    print famille
    famille.rename(columns = {'noifam': 'idfam'}, inplace = True)
    print 'Vérifications sur famille'
    assert len(famille_check.loc[famille_check['chef'], :]) == len(set(famille.idfam.values)), \
      'the number of family chiefs {} is different from the number of families {}'.format(
          len(famille_check.loc[famille_check['chef'], :]),
          (set(famille.idfam.values))
          )
    assert not(any(famille.duplicated(cols=['idfam', 'quifam']))), \
      'There are {} duplicates of quifam inside famille'.format(sum((famille.duplicated(cols=['idfam', 'quifam']))))
    assert famille['quifam'].notnull().all(), 'there are missing values in quifam'
    assert famille['idfam'].notnull().all(), 'there are missing values in idfam'
#    control(famille, debug=True, verbose=True, verbose_columns=['idfam', 'quifam'])

    print '    Sauvegarde de famille'
    save_temp(famille, name="famc", year=year)
    del famille_check, indivi, enfants_a_naitre

if __name__ == '__main__':
    famille()

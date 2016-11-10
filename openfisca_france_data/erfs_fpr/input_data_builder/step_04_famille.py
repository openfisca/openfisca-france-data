#!/usr/bin/env python
# -*- coding: utf-8 -*-


import gc
import logging
import numpy as np
import pandas as pd

from openfisca_france_data.temporary import temporary_store_decorator
from openfisca_france_data.utils import assert_dtype

log = logging.getLogger(__name__)


@temporary_store_decorator(file_name = 'erfs_fpr')
def create_famille(temporary_store = None, year = None):
    """
    Création des familles
    Création des variables 'idfam' and 'quifam'
    """

    assert temporary_store is not None
    assert year is not None

    skip_enfants_a_naitre = True
    kind = 'erfs_fpr'

    log.info('step_04_famille: construction de la table famille')
    # TODO: extraire ces valeurs d'un fichier de paramètres de législation
    if year == 2006:
        smic = 1254
    elif year == 2007:
        smic = 1280
    elif year == 2008:
        smic = 1308
    elif year == 2009:
        smic = 1337
    elif year == 2012:
        smic = int(1398.37)
    else:
        log.info("smic non défini")

    # TODO check if we can remove acteu forter etc since dealt with in 01_pre_proc

    log.info('Etape 1 : préparation de base')
    log.info('    1.1 : récupération de indivi')
    indivi = temporary_store['individus_{}'.format(year)]

    indivi['year'] = year
    # indivi["noidec"] = indivi["declar1"].str[0:2].copy()  # Not converted to int because some NaN are present

    indivi["agepf"] = (
        (indivi.naim < 7) * (indivi.year - indivi.naia) +
        (indivi.naim >= 7) * (indivi.year - indivi.naia - 1)
        )

    # Enfant en nourrice exclus
    selection_enfant_en_nourrice = (indivi.lien == 6) & (indivi.agepf < 16)
    nb_enfants_en_nourrice = selection_enfant_en_nourrice.sum()
    if nb_enfants_en_nourrice > 0:
        indivi = indivi[~(selection_enfant_en_nourrice)].copy()
        log.info(u"{} enfants en nourrice sont exlus".format(nb_enfants_en_nourrice.sum()))

    assert_dtype(indivi.year, "int64")
    for series_name in ['agepf']:  # , 'noidec']:  # integer with NaN
        assert_dtype(indivi[series_name], "object")

    if skip_enfants_a_naitre:
        log.info(u"    1.2 : On ne récupère pas d'enfants à naître")
    else:
        log.info(u"    1.2 : récupération des enfants à naître")
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
            'wprm',
            ]

        enfants_a_naitre = temporary_store['enfants_a_naitre_{}'.format(year)][individual_variables].copy()
        enfants_a_naitre.drop_duplicates('noindiv', inplace = True)
        log.info(u""""
    Il y a {} enfants à naitre avant de retirer ceux qui ne sont pas enfants
    de la personne de référence
    """.format(len(enfants_a_naitre.index)))
        enfants_a_naitre = enfants_a_naitre.loc[enfants_a_naitre.lpr == 3].copy()
        enfants_a_naitre = enfants_a_naitre.loc[~(enfants_a_naitre.noindiv.isin(indivi.noindiv.values))].copy()
        log.info(u""""
        Il y a {} enfants à naitre après avoir retiré ceux qui ne sont pas enfants
        de la personne de référence
        """.format(len(enfants_a_naitre.index)))

    # PB with vars "agepf"  "noidec" "year"  NOTE: quels problèmes ? JS
    log.info(u"    1.3 : création de la base complète")
    if skip_enfants_a_naitre:
        base = indivi.copy()
    else:
        base = pd.concat([indivi, enfants_a_naitre])

    log.info(u"base contient {} lignes ".format(len(base.index)))
    base['noindiv'] = (100 * base.ident + base['noi']).astype(int)
    base['m15'] = base.agepf < 16
    base['p16m20'] = (base.agepf >= 16) & (base.agepf <= 20)
    base['p21'] = base.agepf >= 21

    if kind == 'erfs_fpr':
        base['salaire_imposable'].fillna(0, inplace = True)
        base['smic55'] = base.salaire_imposable >= (smic * 12 * 0.55)  # 55% du smic mensuel brut
    else:
        base['ztsai'].fillna(0, inplace = True)
        base['smic55'] = base.ztsai >= (smic * 12 * 0.55)  # 55% du smic mensuel brut

    base['famille'] = 0
    base['kid'] = False
    for series_name in ['kid', 'm15', 'p16m20', 'p21', 'smic55']:
        assert_dtype(base[series_name], "bool")
    assert_dtype(base.famille, "int")
    # TODO: remove or clean from NA assert_dtype(base.ztsai, "int")

    log.info(u"Etape 2 : On cherche les enfants ayant père et/ou mère comme personne de référence et conjoint")
    personne_de_reference = base.loc[base.lpr == 1, ['ident', 'noi']].copy()
    personne_de_reference['noifam'] = (100 * personne_de_reference.ident + personne_de_reference['noi']).astype(int)
    personne_de_reference = personne_de_reference[['ident', 'noifam']].copy()
    log.info(u"length personne_de_reference : {}".format(len(personne_de_reference.index)))
    nof01 = base.loc[
        base.lpr.isin([1, 2]) |
        ((base.lpr == 3) & (base.m15)) |
        ((base.lpr == 3) & base.p16m20 & (~base.smic55))
        ].copy()
    log.info('longueur de nof01 avant merge: {}'.format(len(nof01.index)))
    nof01 = nof01.merge(personne_de_reference, on = 'ident', how = 'outer')
    nof01['famille'] = 10
    nof01['kid'] = (
        ((nof01.lpr == 3) & (nof01.m15)) |
        ((nof01.lpr == 3) & (nof01.p16m20) & ~(nof01.smic55))
        )
    for series_name in ['famille', 'noifam']:
        assert_dtype(nof01[series_name], "int")
    assert_dtype(nof01.kid, "bool")
    famille = nof01.copy()
    del nof01
    control_04(famille, base)

    log.info(u"    2.1 : Identification des couples non personne de référence ou conjoint de celle-ci")
    # On adopte une approche non genrée
    couple = subset_base(base, famille)
    couple = couple[(couple.cohab == 1) & (couple.lpr >= 3)].copy()
    # l'identifiant famille est lié au noi de le plus bas
    couple['noifam'] = np.minimum(
        (100 * couple.ident + couple.noi).astype(int),
        (100 * couple.ident + couple.noicon).astype(int)
        )

    # Recherche la présence de polyandes/polygames
    noindiv_conjoint = (100 * base.ident + base.noicon).astype(int)
    conjoints = base.loc[
        base.noindiv.isin(noindiv_conjoint),
        ['noindiv', 'ident', 'noi', 'lpr', 'noicon']
        ]
    if conjoints.noindiv.duplicated().sum() > 0:
        log.info(u"Nombre de personnes polyandres/polygames: {}".format(
            conjoints.duplicated().sum()
        ))
    del noindiv_conjoint

    couple['famille'] = 20
    for series_name in ['famille', 'noifam']:
        assert_dtype(couple[series_name], "int")

    log.info(u"""Nombre de personnes vivant en couple sans être personne de référence ou conjoint:
    {} dont {} sans conjoints dans la base
""".format(
        len(couple),
        len(couple.loc[
            ~(
                (100 * couple.ident + couple.noicon).astype(int).isin(base.noindiv)
                )
            ])
        ))
    famille = pd.concat([famille, couple])
    control_04(famille, base)

    log.info(u"Etape 3: Récupération des personnes seules")
    log.info(u"    3.1 : personnes seules de catégorie 1")
    seul1 = base[~(base.noindiv.isin(famille.noindiv.values))].copy()
    seul1 = seul1[
        (seul1.lpr.isin([3, 4])) & ((seul1.p16m20 & seul1.smic55) | seul1.p21) & (seul1.cohab == 1) &
        (seul1.sexe == 2)].copy()
    log.info(u"Il y a {} personnes seules de catégorie 1".format(
        len(seul1.index)))
    if len(seul1.index) > 0:
        seul1['noifam'] = (100 * seul1.ident + seul1.noi).astype(int)
        seul1['famille'] = 31
        for series_name in ['famille', 'noifam']:
            assert_dtype(seul1[series_name], "int")
        famille = pd.concat([famille, seul1])
        control_04(famille, base)

    log.info(u"    3.1 personnes seules de catégorie 2")
    seul2 = base[~(base.noindiv.isin(famille.noindiv.values))].copy()
    seul2 = seul2[(seul2.lpr.isin([3, 4])) & seul2.p16m20 & seul2.smic55 & (seul2.cohab != 1)].copy()
    log.info(u"Il y a {} personnes seules de catégorie 2".format(
        len(seul2.index)))
    if len(seul2.index) > 0:
        seul2['noifam'] = (100 * seul2.ident + seul2.noi).astype(int)
        seul2['famille'] = 32

        for series_name in ['famille', 'noifam']:
            assert_dtype(seul2[series_name], "int")
        famille = pd.concat([famille, seul2])
        control_04(famille, base)

    log.info(u"    3.3 personnes seules de catégorie 3")
    seul3 = subset_base(base, famille)
    seul3 = seul3[(seul3.lpr.isin([3, 4])) & seul3.p21 & (seul3.cohab != 1)].copy()
    # TODO: CHECK erreur dans le guide méthodologique ERF 2002 lpr 3,4 au lieu de 3 seulement
    log.info(u"Il y a {} personnes seules de catégorie 3".format(
        len(seul3.index)))
    if len(seul3.index) > 0:
        seul3['noifam'] = (100 * seul3.ident + seul3.noi).astype(int)
        seul3['famille'] = 33
        for series_name in ['famille', 'noifam']:
            assert_dtype(seul3[series_name], "int")
        famille = pd.concat([famille, seul3])
        control_04(famille, base)

    log.info(u"    3.4 : personnes seules de catégorie 4")
    seul4 = subset_base(base, famille)

    assert seul4.noimer.notnull().all()
    if kind == 'erfs_fpr':
        seul4 = seul4[
            (seul4.lpr == 4) &
            seul4.p16m20 &
            (~(seul4.smic55)) &
            # (seul4.noiper == 0) &
            (seul4.noimer == 0)
            ].copy()
    else:
        seul4 = seul4[
            (seul4.lpr == 4) &
            seul4.p16m20 &
            (~(seul4.smic55)) &
            # (seul4.noiper == 0) &
            (seul4.noimer == 0) &
            (seul4.persfip == 'vous')
            ].copy()
    log.info(u"Il y a {} personnes seules de catégorie 4".format(
        len(seul4.index)))

    if len(seul4.index) > 0:
        seul4['noifam'] = (100 * seul4.ident + seul4.noi).astype(int)
        seul4['famille'] = 34
        famille = pd.concat([famille, seul4])
        for series_name in ['famille', 'noifam']:
            assert_dtype(seul4[series_name], "int")
    control_04(famille, base)

    log.info(u"Etape 4 : traitement des enfants")
    log.info(u"    4.1 : enfant avec mère")
    avec_mere = subset_base(base, famille)
    avec_mere = avec_mere[
        (avec_mere.lpr == 4) &
        (avec_mere.p16m20 | avec_mere.m15) &
        (avec_mere.noimer > 0)
        ].copy()
    log.info(u"Il y a {} enfants rattachés à leur mère".format(
        len(avec_mere.index)))

    if len(avec_mere.index) > 0:
        avec_mere['noifam'] = (100 * avec_mere.ident + avec_mere.noimer).astype(int)
        avec_mere['famille'] = 41
        avec_mere['kid'] = True
        for series_name in ['famille', 'noifam']:
            assert_dtype(avec_mere[series_name], "int")

    # On récupère les mères des enfants (elles peuvent avoir plusieurs enfants et il faut unicité de l'identifiant)
    mere = (pd.DataFrame(avec_mere['noifam'].copy())
        .rename(columns = {'noifam': 'noindiv'})
        .drop_duplicates()
        .merge(base)
        )
    log.info(u"qui sont au nombre de {}".format(
        len(mere)))

    mere['noifam'] = (100 * mere.ident + mere.noi).astype(int)
    mere['famille'] = 42
    for series_name in ['famille', 'noifam']:
        assert_dtype(mere[series_name], "int")
    avec_mere = avec_mere[avec_mere.noifam.isin(mere.noindiv)].copy()
    famille = famille[~(famille.noindiv.isin(mere.noindiv.values))].copy()  # Avoid duplication in famille

    # On retrouve les conjoints des mères
    assert mere.noicon.notnull().all()
    conjoint_mere_id = mere.loc[mere.noicon > 0, ['ident', 'noicon', 'noifam']].copy()
    conjoint_mere_id['noindiv'] = (100 * conjoint_mere_id.ident + conjoint_mere_id.noicon).astype(int)
    log.info(u"et dont les conjoints sont au nombre de {}".format(
        len(conjoint_mere_id)))
    conjoint_mere = (conjoint_mere_id[['noindiv', 'noifam']].copy()
        .merge(base)
        )
    conjoint_mere['famille'] = 43
    for series_name in ['famille', 'noifam']:
        assert_dtype(conjoint_mere[series_name], "int")

    famille = famille[~(famille.noindiv.isin(conjoint_mere.noindiv.values))].copy()  # Avoid duplication in famille
    famille = pd.concat([famille, avec_mere, mere, conjoint_mere])
    del avec_mere, mere, conjoint_mere, conjoint_mere_id
    control_04(famille, base)

    log.info(u"    4.2 : enfants avec père")
    avec_pere = subset_base(base, famille)
    assert avec_pere.noiper.notnull().all()
    avec_pere = avec_pere[
        (avec_pere.lpr == 4) &
        (avec_pere.p16m20 | avec_pere.m15) &
        (avec_pere.noiper > 0)
        ].copy()
    log.info(u"Il y a {} enfants rattachés à leur père".format(
        len(avec_pere.index)))
    avec_pere['noifam'] = (100 * avec_pere.ident + avec_pere.noiper).astype(int)
    avec_pere['famille'] = 44
    avec_pere['kid'] = True
    assert avec_pere['noifam'].notnull().all(), 'presence of NaN in avec_pere'
    for series_name in ['famille', 'noifam']:
        assert_dtype(avec_pere[series_name], "int")
    assert_dtype(avec_pere.kid, "bool")

    pere = (pd.DataFrame(avec_pere['noifam'])
        .rename(columns = {'noifam': 'noindiv'})
        .drop_duplicates()
        .merge(base)
        )
    pere['noifam'] = (100 * pere.ident + pere.noi).astype(int)
    pere['famille'] = 45
    famille = famille[~(famille.noindiv.isin(pere.noindiv.values))].copy()  # Avoid duplication in famille

    # On récupère les conjoints des pères
    assert pere.noicon.notnull().all()
    conjoint_pere_id = pere.loc[pere.noicon > 0, ['ident', 'noicon', 'noifam']].copy()
    log.info(u"et dont les conjoints sont au nombre de {}".format(
        len(conjoint_pere_id)))

    if len(conjoint_pere_id.index) > 0:
        conjoint_pere_id['noindiv'] = (100 * conjoint_pere_id.ident + conjoint_pere_id.noicon).astype(int)
        conjoint_pere = (conjoint_pere_id[['noindiv', 'noifam']].copy()
            .merge(base)
            )
        conjoint_pere['famille'] = 46
        for series_name in ['famille', 'noifam']:
            assert_dtype(conjoint_pere[series_name], "int")

        famille = famille[~(famille.noindiv.isin(conjoint_pere.noindiv.values))].copy()  # Avoid duplication in famille
        famille = pd.concat([famille, avec_pere, pere, conjoint_pere])
    else:
        conjoint_pere = None
        famille = pd.concat([famille, avec_pere, pere])

    control_04(famille, base)

    del avec_pere, pere, conjoint_pere, conjoint_pere_id

    if kind == 'erfs_fpr':
        log.info(u"    4.3 : enfants avec déclarant (ignorée dans erfs_fpr)")
        pass
    else:
        log.info(u"    4.3 : enfants avec déclarant")
        avec_dec = subset_base(base, famille)
        avec_dec = avec_dec[
            (avec_dec.persfip == "pac") &
            (avec_dec.lpr == 4) &
            (
                (avec_dec.p16m20 & ~(avec_dec.smic55)) | (avec_dec.m15 == 1)
                )
            ]
        avec_dec['noifam'] = (100 * avec_dec.ident + avec_dec.noidec.astype('int')).astype('int')
        avec_dec['famille'] = 47
        avec_dec['kid'] = True
        for series_name in ['famille', 'noifam']:
            assert_dtype(avec_dec[series_name], "int")
        assert_dtype(avec_dec.kid, "bool")
        control_04(avec_dec, base)
        # on récupère les déclarants pour leur attribuer une famille propre
        declarant_id = pd.DataFrame(avec_dec['noifam'].copy()).rename(columns={'noifam': 'noindiv'})
        declarant_id.drop_duplicates(inplace = True)
        dec = declarant_id.merge(base)
        dec['noifam'] = (100 * dec.ident + dec.noi).astype(int)
        dec['famille'] = 48
        for series_name in ['famille', 'noifam']:
            assert_dtype(dec[series_name], "int")
        famille = famille[~(famille.noindiv.isin(dec.noindiv.values))].copy()
        famille = pd.concat([famille, avec_dec, dec])
        del dec, declarant_id, avec_dec
        control_04(famille, base)

    if kind == 'erfs_fpr':
        log.info(u"Etape 5 : Récupération des enfants fip (ignorée dans erfs_fpr)")
        pass
    else:
        log.info(u"Etape 5 : Récupération des enfants fip")
        log.info(u"    5.1 : Création de la df fip")
        individual_variables_fip = [
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
        fip = temporary_store['fipDat_{}'.format(year)][individual_variables_fip].copy()
        # Variables auxilaires présentes dans base qu'il faut rajouter aux fip'
        # WARNING les noindiv des fip sont construits sur les ident des déclarants
        # pas d'orvelap possible avec les autres noindiv car on a des noi =99, 98, 97 ,...'
        fip['m15'] = (fip.agepf < 16)
        fip['p16m20'] = ((fip.agepf >= 16) & (fip.agepf <= 20))
        fip['p21'] = (fip.agepf >= 21)
        fip['smic55'] = (fip.ztsai >= smic * 12 * 0.55)
        fip['famille'] = 0
        fip['kid'] = False
        for series_name in ['kid', 'm15', 'p16m20', 'p21', 'smic55']:
            assert_dtype(fip[series_name], "bool")
        for series_name in ['famille']:
            assert_dtype(fip[series_name], "int")

        log.info(u"    5.2 : extension de base avec les fip")
        base_ = pd.concat([base, fip])
        enfant_fip = subset_base(base_, famille)
        enfant_fip = enfant_fip[
            (enfant_fip.quelfic == "FIP") & (
                (enfant_fip.agepf.isin([19, 20]) & ~(enfant_fip.smic55)) |
                ((enfant_fip.naia == enfant_fip.year - 1) & (enfant_fip.rga.astype('int') == 6))
                )
            ].copy()
        enfant_fip['noifam'] = (100 * enfant_fip.ident + enfant_fip.noidec).astype(int)
        enfant_fip['famille'] = 50
        enfant_fip['kid'] = True
        enfant_fip['ident'] = None  # TODO: should we really do this ?
        assert_dtype(enfant_fip.kid, "bool")
        for series_name in ['famille', 'noifam']:
            assert_dtype(enfant_fip[series_name], "int")
        control_04(enfant_fip, base)
        famille = pd.concat([famille, enfant_fip])
        base = pd.concat([base, enfant_fip])
        parent_fip = famille[famille.noindiv.isin(enfant_fip.noifam.values)].copy()
        assert (enfant_fip.noifam.isin(parent_fip.noindiv.values)).any(), \
            "{} doublons entre enfant_fip et parent fip !".format(
                (enfant_fip.noifam.isin(parent_fip.noindiv.values)).sum())
        parent_fip['noifam'] = parent_fip['noindiv'].values.copy()
        parent_fip['famille'] = 51
        parent_fip['kid'] = False
        log.info(u"Contrôle de parent_fip")
        control_04(parent_fip, base)
        control_04(famille, base)
        famille = famille.merge(parent_fip, how='outer')
        del enfant_fip, fip, parent_fip

    assert not famille.duplicated().any()
    assert not famille.noindiv.duplicated().any()
    control_04(famille, base)

    log.info(u"Etape 6 : gestion des non attribués")
    log.info(u"    6.1 : non attribués type 1")
    non_attribue1 = subset_base(base, famille)
    if kind == 'erfs_fpr':
        non_attribue1 = non_attribue1[
            non_attribue1.m15 |
            (
                non_attribue1.p16m20 &
                (non_attribue1.lien.isin(range(1, 5))) &
                (non_attribue1.agepr >= 35)
                )
            ].copy()

    else:
        non_attribue1 = non_attribue1[
            (~(non_attribue1.quelfic != 'FIP')) &
            (
                non_attribue1.m15 |
                (
                    non_attribue1.p16m20 &
                    (non_attribue1.lien.isin(range(1, 5))) &
                    (non_attribue1.agepr >= 35)
                    )
                )
            ].copy()
    # On rattache les moins de 15 ans avec la PR (on a déjà éliminé les enfants en nourrice)
    log.info(u"Il y a {} enfants non attribués de type 1".format(
        len(non_attribue1.index)))

    if len(non_attribue1.index) > 0:
        non_attribue1 = non_attribue1.merge(personne_de_reference)
        non_attribue1['famille'] = 61 * non_attribue1.m15 + 62 * ~(non_attribue1.m15)
        non_attribue1['kid'] = True
        assert_dtype(non_attribue1.kid, "bool")
        assert_dtype(non_attribue1.famille, "int")
        famille = pd.concat([famille, non_attribue1])
        control_04(famille, base)
        del personne_de_reference, non_attribue1

    log.info(u"    6.2 : non attribué type 2")
    if kind == 'erfs_fpr':
        non_attribue2 = base[~(base.noindiv.isin(famille.noindiv.values))].copy()
    else:
        non_attribue2 = base[(~(base.noindiv.isin(famille.noindiv.values)) & (base.quelfic != "FIP"))].copy()

    log.info(u"Il y a {} enfants non attribués de type 2".format(
        len(non_attribue2.index)))
    if len(non_attribue2.index) > 0:
        non_attribue2['noifam'] = (100 * non_attribue2.ident + non_attribue2.noi).astype(int)
        non_attribue2['kid'] = False
        non_attribue2['famille'] = 63
        assert_dtype(non_attribue2.kid, "bool")
        for series_name in ['famille', 'noifam']:
            assert_dtype(non_attribue2[series_name], "int")
        famille = pd.concat([famille, non_attribue2])
        control_04(famille, base)
        del non_attribue2

    log.info(u"Etape 7 : Sauvegarde de la table famille")

    log.info(u"    7.1 : Mise en forme finale")
    famille['chef'] = (famille.noifam == (100 * famille.ident + famille.noi))
    assert_dtype(famille.chef, "bool")

    famille.reset_index(inplace = True)
    control_04(famille, base)

    log.info(u"    7.2 : création de la colonne rang")
    famille['rang'] = famille.kid.astype(int)
    while any(famille.loc[famille.rang != 0].duplicated(subset = ['rang', 'noifam'])):
        famille.loc[famille.rang != 0, 'rang'] += (
            famille[
                famille.rang != 0
                ]
            .duplicated(subset = ["rang", 'noifam']).values
            )
        # log.info(u"nb de rangs différents : {}".format(famille.rang.value_counts().sort_index()))

    log.info(u"    7.3 : création de la colonne quifam et troncature")
    log.info(u"value_counts chef : \n {}".format(famille['chef'].value_counts()))
    log.info(u"value_counts kid :' \n {}".format(famille['kid'].value_counts()))

    famille['quifam'] = -1
    famille['quifam'] = famille['quifam'].where(famille['chef'].values, 0)
    famille.quifam = (
        0 +
        ((~famille.chef) & (~famille.kid)).astype(int) +
        famille.kid * (famille.rang + 1)
        ).astype('int')

    assert (famille.groupby('noifam')['chef'].sum() <= 1).all(), "Il y a plusieurs chefs par famille"

    if not (famille.groupby('noifam')['chef'].sum() == 1).all():
        log.info(u"Il y a {} familles qui n'ont pas de chef de famille".format(
            (famille.groupby('noifam')['chef'].sum() == 0).sum()
            ))
        absence_chef = (famille.groupby('noifam')['chef'].sum() == 0)
        noifam_absence_chef = absence_chef.loc[absence_chef].index
        idents = famille.loc[famille.noifam.isin(noifam_absence_chef), 'ident'].unique()
        log.info(u'Il y a {} ménages contenant des familles sans chefs. on les retire'.format(
            len(idents)))
        famille = famille.loc[~famille.ident.isin(idents)].copy()
        control_04(famille, base)

    log.info(u"value_counts quifam : \n {}".format(famille['quifam'].value_counts().sort_index()))
    famille = famille[['noindiv', 'quifam', 'noifam']].copy()
    famille.rename(columns = {'noifam': 'idfam'}, inplace = True)
    log.info(u"Vérifications sur famille")

    duplicated_famillle = famille.duplicated(subset = ['idfam', 'quifam'], keep = False)
    if duplicated_famillle.sum() > 0:
        log.info(u"There are {} duplicates of quifam inside famille".format(
            duplicated_famillle.sum()))
        raise
    individus = indivi.merge(famille, on = ['noindiv'], how = "inner")
    if skip_enfants_a_naitre:
        del indivi, base
    else:
        del indivi, enfants_a_naitre, base
    gc.collect()

    temporary_store['individus_{}'.format(year)] = individus


# helpers

def control_04(dataframe, base):
    log.info(u"longueur de la dataframe après opération : {}".format(len(dataframe)))

    if any(dataframe.duplicated(subset = 'noindiv')):
        log.info(u"contrôle des doublons : il y a {} individus en double".format(
            dataframe.duplicated(subset = 'noindiv').sum()))
    # log.info(u"contrôle des colonnes : il y a {} colonnes".format(len(dataframe.columns)))
    log.info(u"Il y a {} identifiants de familles différentes".format(len(dataframe.noifam.unique())))
    assert not dataframe.noifam.isnull().any(), u"{} noifam are NaN".format(dataframe.noifam.isnull().sum())

    log.info(u"{} lignes dans dataframe vs {} lignes dans base".format(len(dataframe.index), len(base.index)))
    assert len(dataframe.index) <= len(base.index), u"dataframe has too many rows compared to base"
    assert set(dataframe.noifam.unique()).issubset(set(base.noindiv)), \
        "The following {} are not in the dataframe: \n {}".format(
            len(dataframe.loc[~dataframe.noifam.isin(base.noindiv)]),
            dataframe.loc[~dataframe.noifam.isin(base.noindiv), ['noifam', 'famille']],
            )

    if 'quifam' in dataframe:
        famille_population = dataframe.query('quifam == 0').groupby('famille')['wprm'].sum()
        log.info("famille :\n{}".format(
            famille_population / famille_population.sum()
            ))


def subset_base(base, famille):
    """
    Generates a dataframe containing the values of base that are not already in famille
    """
    return base.loc[~(base.noindiv.isin(famille.noindiv.values))].copy()


if __name__ == '__main__':
    import sys
    logging.basicConfig(level = logging.INFO, stream = sys.stdout)
    # logging.basicConfig(level = logging.INFO, filename = 'step_04.log', filemode = 'w')
    year = 2012
    create_famille(year = year)
    log.info(u"étape 04 famille terminée")

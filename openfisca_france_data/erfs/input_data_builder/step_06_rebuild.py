#! /usr/bin/env python
import gc
import logging

from pandas import Series, concat
import numpy as np
from numpy import where

from openfisca_survey_manager.temporary import temporary_store_decorator

from openfisca_france_data.utils import print_id, control


log = logging.getLogger(__name__)


@temporary_store_decorator(file_name = 'erfs')
def create_totals_first_pass(temporary_store = None, year = None):
    assert temporary_store is not None
    assert year is not None

    # On part de la table individu de l'ERFS
    # on renomme les variables
    log.info("Creating Totals")
    log.info("Etape 1 : Chargement des données")

    indivim = temporary_store['indivim_{}'.format(year)]

    assert not indivim.duplicated(['noindiv']).any(), "Présence de doublons"

    # Deals individuals with imputed income : some individuals are in 'erf individu table' but
    # not in the 'foyer' table. We need to create a foyer for them.
    selection = Series()
    for var_i in ["zsali", "zchoi", "zrsti", "zalri", "zrtoi", "zragi", "zrici", "zrnci"]:
        var_o = var_i[:-1] + "o"
        test = indivim[var_i] != indivim[var_o]
        if selection.empty:
            selection = test
        else:
            selection = test | selection

    indivi_i = indivim[selection].copy()
    indivi_i.rename(
        columns = {
            "ident": "idmen",
            "persfip": "quifoy",
            "zsali": "sali",  # Inclu les salaires non imposables des agents d'assurance
            "zchoi": "choi",
            "zrsti": "rsti",
            "zalri": "alr"
            },
        inplace = True,
        )
    assert indivi_i.quifoy.notnull().all()
    indivi_i.loc[indivi_i.quifoy == "", "quifoy"] = "vous"
    indivi_i.quelfic = "FIP_IMP"

   # We merge them with the other individuals
    indivim.rename(
        columns = dict(
            ident = "idmen",
            persfip = "quifoy",
            zsali = "sali",  # Inclu les salaires non imposables des agents d'assurance
            zchoi = "choi",
            zrsti = "rsti",
            zalri = "alr",
            ),
        inplace = True,
        )

    if not (set(list(indivim.noindiv)) > set(list(indivi_i.noindiv))):
        raise Exception("Individual ")
    indivim.set_index("noindiv", inplace = True, verify_integrity = True)
    indivi_i.set_index("noindiv", inplace = True, verify_integrity = True)
    indivi = indivim
    del indivim
    indivi.update(indivi_i)
    indivi.reset_index(inplace = True)
    assert not(indivi.noindiv.duplicated().any()), "Doublons"

    log.info("Etape 2 : isolation des FIP")
    fip_imp = indivi.quelfic == "FIP_IMP"
    indivi["idfoy"] = (
        indivi.idmen.astype('int') * 100 +
        (indivi.declar1.str[0:2]).convert_objects(convert_numeric=True)
        )

    # indivi.loc[fip_imp, "idfoy"] = np.nan
    # Certains FIP (ou du moins avec revenus imputés) ont un numéro de déclaration d'impôt ( pourquoi ?)
    assert indivi_i.declar1.notnull().all()
    assert (indivi_i.declar1 == "").sum() > 0
    fip_has_declar = (fip_imp) & (indivi.declar1 != "")

    indivi.loc[fip_has_declar, "idfoy"] = (
        indivi.idmen * 100 + indivi.declar1.str[0:2].convert_objects(convert_numeric = True))
    del fip_has_declar

    fip_no_declar = (fip_imp) & (indivi.declar1 == "")
    del fip_imp
    indivi.loc[fip_no_declar, "idfoy"] = 100 * indivi.loc[fip_no_declar, "idmen"] + indivi.loc[fip_no_declar, "noi"]
    # WAS indivi["idmen"] * 100 + 50

    indivi_fnd = indivi.loc[fip_no_declar, ["idfoy", "noindiv"]].copy()

    while any(indivi_fnd.duplicated(subset = ["idfoy"])):
        indivi_fnd["idfoy"] = where(
            indivi_fnd.duplicated(subset = ["idfoy"]),
            indivi_fnd["idfoy"] + 1,
            indivi_fnd["idfoy"]
            )

    # assert indivi_fnd["idfoy"].duplicated().value_counts()[False] == len(indivi_fnd["idfoy"].values), \
    #    "Duplicates remaining"
    assert not(indivi.noindiv.duplicated().any()), "Doublons"

    indivi.idfoy.loc[fip_no_declar] = indivi_fnd.idfoy.copy()
    del indivi_fnd, fip_no_declar

    log.info("Etape 3 : Récupération des EE_NRT")
    nrt = indivi.quelfic == "EE_NRT"
    indivi.loc[nrt, 'idfoy'] = indivi.loc[nrt, 'idmen'] * 100 + indivi.loc[nrt, 'noi']
    indivi.loc[nrt, 'quifoy'] = "vous"
    del nrt

    pref_or_cref = indivi.lpr.isin([1, 2])
    adults = (indivi.quelfic.isin(["EE", "EE_CAF"])) & (pref_or_cref)
    pref = adults & (indivi.lpr == 1)
    cref = adults & (indivi.lpr == 2)
    indivi.loc[adults, "idfoy"] = indivi.loc[adults, 'idmen'] * 100 + indivi.loc[adults, 'noiprm']
    indivi.loc[pref, "quifoy"] = "vous"
    indivi.loc[cref, "quifoy"] = "conj"
    del adults, pref, cref
    assert indivi.idfoy[indivi.lpr.dropna().isin([1, 2])].all()

    idfoyList = indivi.loc[indivi.quifoy == "vous", 'idfoy'].unique()
    indivi_without_idfoy = ~indivi.idfoy.isin(idfoyList)
    log.info("Il reste {} idfoy problématiques".format(
        indivi_without_idfoy.sum()
        ))

    # Conjoints qui dont il n'existe pas de vous avec leur idfoy.
    # Problème de double déclaration: si leur conjoint à un noindiv à leur idfoy on switch les déclarants
    log.info("{} conj without a valid idfoy".format(
        (indivi_without_idfoy & indivi.idfoy.notnull() & indivi.quifoy.isin(['conj'])).sum()
        ))

    if (indivi_without_idfoy & indivi.idfoy.notnull() & indivi.quifoy.isin(['conj'])).any():
        # On traite les gens qui ont quifoy=conj mais dont l'idfoy n'a pas de vous
        # 1) s'ils ont un conjoint et qu'il est vous avec un idfoy valide on leur attribue son idfoy:
        avec_conjoint = (
            indivi_without_idfoy &
            indivi.idfoy.notnull() &
            indivi.quifoy.isin(['conj']) &
            (indivi.noicon != 0) &
            (100 * indivi.idmen + indivi.noicon).isin(idfoyList)
            )
        indivi.loc[avec_conjoint, 'idfoy'] = (
            100 * indivi.loc[avec_conjoint, 'idmen'] + indivi.loc[avec_conjoint, 'noicon']
            )
        indivi_without_idfoy = ~indivi.idfoy.isin(idfoyList)  # mise à jour des cas problématiques
        del avec_conjoint

    if (indivi_without_idfoy & indivi.idfoy.notnull() & indivi.quifoy.isin(['conj'])).any():
        # 2) sinon ils deviennent vous
        devient_vous = (
            indivi_without_idfoy &
            indivi.idfoy.notnull() &
            indivi.quifoy.isin(['conj']) &
            (indivi.noicon == 0)
            )
        indivi.loc[devient_vous, 'idfoy'] = indivi.loc[devient_vous, 'noindiv'].copy()
        indivi.loc[devient_vous, 'quifoy'] = 'vous'
        idfoyList = indivi.loc[indivi.quifoy == "vous", 'idfoy'].unique()
        indivi_without_idfoy = ~indivi.idfoy.isin(idfoyList)  # Mise à jour des cas problématiques
        del devient_vous

    problem = (indivi_without_idfoy & indivi.idfoy.notnull() & indivi.quifoy.isin(['conj']))
    if problem.sum() > 0:
        log.info("Dropping {} conj without valid idfoy".format(
            problem.sum()
        ))
        indivi.drop(indivi[problem].index, inplace = True)
        indivi_without_idfoy = ~indivi.idfoy.isin(idfoyList)  # Mise à jour des cas problématiques
        problem = (indivi_without_idfoy & indivi.idfoy.notnull() & indivi.quifoy.isin(['conj']))
        assert not problem.any()

    idfoyList = indivi.loc[indivi.quifoy == "vous", 'idfoy'].unique()
    indivi_without_idfoy = ~indivi.idfoy.isin(idfoyList)
    log.info("Remainning {} non valid idfoy".format(
        indivi_without_idfoy.sum()
        ))
    # Les personnes à charge de personnes repérées comme conjoint idfoy = conj_noindiv
    # (problème des doubles déclarations) doivent récupérer l'idfoy de celles-ci
    pac = (
        indivi_without_idfoy & indivi.idfoy.notnull() & indivi.quifoy.isin(['pac'])
        )
    log.info("Dealing with {} non valid idfoy of pacs".format(
        pac.sum()
        ))
    conj_noindiv = indivi.idfoy[pac].copy()
    new_idfoy_by_old = indivi.loc[
        indivi.noindiv.isin(conj_noindiv), ['noindiv', 'idfoy']
        ].astype('int').set_index('noindiv').squeeze().to_dict()
    indivi.loc[pac, 'idfoy'] = indivi.loc[pac, 'idfoy'].map(new_idfoy_by_old)
    del pac
    indivi_without_idfoy = ~indivi.idfoy.isin(idfoyList)  # Mise à jour des cas problématiques
    assert not (indivi_without_idfoy & indivi.idfoy.notnull() & indivi.quifoy.isin(['pac'])).any()

    # Il faut traiter les idfoy non attribués
    indivi_without_idfoy = ~indivi.idfoy.isin(idfoyList)
    assert (indivi_without_idfoy == indivi.idfoy.isnull()).all()
    log.info("Il faut traiter les {} idfoy non attribués".format(
        indivi_without_idfoy.sum()
        ))

    # Adultes non enfants avec conjoints déclarants
    married_adult_with_vous = (
        indivi_without_idfoy &
        ((indivi.noiper == 0) | (indivi.noimer == 0)) &
        (indivi.age >= 25) &
        (indivi.noicon > 0) &
        (100 * indivi.idmen + indivi.noicon).isin(idfoyList)
        )
    indivi.loc[married_adult_with_vous, 'idfoy'] = (
        100 * indivi.loc[married_adult_with_vous, 'idmen'] + indivi.loc[married_adult_with_vous, 'noicon']
        )
    indivi.loc[married_adult_with_vous, 'quifoy'] = 'conj'
    log.info(
        """Il y a {} adultes > 25 ans non enfants avec conjoints déclarants""".format(
            married_adult_with_vous.sum()
            )
        )

    # Les deux membres du couples n'ont pas d'idfoy
    married_adult_without_vous = (
        indivi_without_idfoy &
        ((indivi.noiper == 0) | (indivi.noimer == 0)) &
        (indivi.age >= 18) &
        (indivi.noicon > 0) &
        (~married_adult_with_vous)
        )
    # On les groupes par ménages, on vérifie qu'ils ne sont que deux
    couple_by_idmen = (
        (indivi.loc[
            married_adult_without_vous, ['idmen', 'noindiv']
            ].groupby('idmen').agg('count')) == 2).astype('int').squeeze().to_dict()

    couple_idmens = list(idmen for idmen in couple_by_idmen.keys() if couple_by_idmen[idmen])
    # On crée un foyer vous-conj si couple
    vous = married_adult_without_vous & (
        ((indivi.sexe == 1) & indivi.idmen.isin(couple_idmens)) |
        (~indivi.idmen.isin(couple_idmens))
        )
    conj = married_adult_without_vous & (~vous) & indivi.idmen.isin(couple_idmens)
    indivi.loc[vous, 'idfoy'] = indivi.loc[vous, 'noindiv'].copy()
    indivi.loc[vous, 'quifoy'] = 'vous'
    indivi.loc[conj, 'idfoy'] = 100 * indivi.loc[conj, 'idmen'] + indivi.loc[conj, 'noicon']
    indivi.loc[conj, 'quifoy'] = 'conj'
    del vous, conj
    log.info(
        """Il y a {} adultes > 25 ans non enfants sans conjoints déclarants: on crée un foyer""".format(
            married_adult_without_vous.sum()
            )
        )

    idfoyList = indivi.loc[indivi.quifoy == "vous", 'idfoy'].unique()
    indivi_without_idfoy = ~indivi.idfoy.isin(idfoyList)

    # Cas des enfants agés sans conjoint >= 25 ans
    non_married_aged_kids = (
        indivi_without_idfoy &
        ((indivi.noiper > 0) | (indivi.noimer > 0)) &
        (indivi.age >= 25) &
        (indivi.noicon == 0)
        )
    indivi.loc[non_married_aged_kids, 'idfoy'] = indivi.loc[non_married_aged_kids, 'noindiv'].copy()
    indivi.loc[non_married_aged_kids, 'quifoy'] = 'vous'
    log.info(
        """On crée un foyer fiscal indépendants pour les {} enfants agés de plus de 25 ans sans conjoint
vivant avec leurs parents""".format(
            non_married_aged_kids.sum()
            )
        )
    del non_married_aged_kids
    idfoyList = indivi.loc[indivi.quifoy == "vous", 'idfoy'].unique()
    indivi_without_idfoy = ~indivi.idfoy.isin(idfoyList)

    # Cas des enfants agés avec conjoint >= 18 ans
    married_aged_kids = (
        indivi_without_idfoy &
        ((indivi.noiper > 0) | (indivi.noimer > 0)) &
        (indivi.age >= 18) &
        (indivi.noicon != 0)
        )

    # Cas des enfants agés avec conjoint >= 18 ans
    married_aged_kids = (
        indivi_without_idfoy &
        ((indivi.noiper > 0) | (indivi.noimer > 0)) &
        (indivi.age >= 18) &
        (indivi.noicon != 0)
        )
    noiconjs = 100 * indivi.idmen + indivi.noicon
    quifoy_by_noiconj = indivi.loc[
        indivi.noindiv.isin(noiconjs[married_aged_kids]), ['noindiv', 'quifoy']
        ].set_index('noindiv').dropna().squeeze().to_dict()
    is_conj_vous = noiconjs.map(quifoy_by_noiconj) == "vous"
    indivi.loc[married_aged_kids & is_conj_vous, 'quifoy'] = "conj"
    indivi.loc[married_aged_kids & is_conj_vous, 'idfoy'] = noiconjs[married_aged_kids & is_conj_vous].copy()

    log.info("""Il y a {} enfants agés de plus de 25 ans avec conjoint
vivant avec leurs parents qui ne sont pas traités""".format(
        married_aged_kids.sum()
        ))  # Il n'y en a pas en 2009
    del married_aged_kids, noiconjs, is_conj_vous

    # Colocations
    if indivi_without_idfoy.any():
        potential_idmens = indivi.loc[indivi_without_idfoy, 'idmen'].copy()
        colocs = indivi.loc[indivi.idmen.isin(potential_idmens), ['idmen', 'age', 'quifoy']].copy()
        coloc_by_idmen = colocs.groupby('idmen').agg({
            'age':
                lambda x:
                    (abs((x.min() - x.max())) < 20) & (x.min() >= 18),
            'quifoy':
                lambda x:
                    (x == 'vous').sum() >= 1,
                }
            )
        coloc_dummy_by_idmen = (coloc_by_idmen.age * coloc_by_idmen.quifoy)
        coloc_idmens = coloc_dummy_by_idmen.index[coloc_dummy_by_idmen.astype('bool')].tolist()
        colocataires = indivi_without_idfoy & indivi.idmen.isin(coloc_idmens)
        indivi.loc[colocataires, 'quifoy'] = 'vous'
        indivi.loc[colocataires, 'idfoy'] = indivi.loc[colocataires, 'noindiv'].copy()
        log.info("Il y a {} colocataires".format(
            colocataires.sum()
            ))
        del colocataires, coloc_dummy_by_idmen, coloc_by_idmen, coloc_idmens, colocs

    idfoyList = indivi.loc[indivi.quifoy == "vous", 'idfoy'].unique()
    indivi_without_idfoy = ~indivi.idfoy.isin(idfoyList)

    # On met le reste des adultes de plus de 25 ans dans des foyers uniques
    other_adults = indivi_without_idfoy & (indivi.age >= 25)
    if indivi_without_idfoy.any():
        indivi.loc[other_adults, 'quifoy'] = 'vous'
        indivi.loc[other_adults, 'idfoy'] = indivi.loc[other_adults, 'noindiv'].copy()
        log.info("Il y a {} autres adultes seuls à qui l'on crée un foyer individuel".format(
            other_adults.sum()
            ))
        del other_adults

    idfoyList = indivi.loc[indivi.quifoy == "vous", 'idfoy'].unique()
    indivi_without_idfoy = ~indivi.idfoy.isin(idfoyList)

    # Cas des enfants jeunes < 25 ans
    kids = (
        indivi_without_idfoy &
        (indivi.age < 25) &
        ((indivi.noiper > 0) | (indivi.noimer > 0))
        )
    # On rattache les enfants au foyer de leur pères s'il existe
    log.info("On traite le cas des {} enfants (noiper ou noimer non nuls) repérés non rattachés".format(
        kids.sum()
        ))
    if kids.any():
        pere_declarant_potentiel = kids & (indivi.noiper > 0)
        indivi['pere_noindiv'] = (100 * indivi.idmen.fillna(0) + indivi.noiper.fillna(0)).astype('int')
        pere_noindiv = (
            100 * indivi.loc[pere_declarant_potentiel, 'idmen'].fillna(0) +
            indivi.loc[pere_declarant_potentiel, 'noiper'].fillna(0)
            ).astype('int')
        idfoy_by_noindiv = indivi.loc[
            indivi.noindiv.isin(pere_noindiv), ['noindiv', 'idfoy']
            ].dropna().astype('int').set_index('noindiv').squeeze().to_dict()
        pere_declarant_potentiel_idfoy = indivi['pere_noindiv'].map(idfoy_by_noindiv)
        pere_veritable_declarant = pere_declarant_potentiel & pere_declarant_potentiel_idfoy.isin(idfoyList)
        indivi.loc[pere_veritable_declarant, 'idfoy'] = (
            pere_declarant_potentiel_idfoy[pere_veritable_declarant].astype('int')
            )
        indivi.loc[pere_veritable_declarant, 'quifoy'] = 'pac'
    log.info("{} enfants rattachés au père ".format(
        pere_veritable_declarant.sum()
        ))
    del pere_declarant_potentiel, pere_declarant_potentiel_idfoy, pere_noindiv, \
        pere_veritable_declarant, idfoy_by_noindiv

    idfoyList = indivi.loc[indivi.quifoy == "vous", 'idfoy'].unique()
    indivi_without_idfoy = ~indivi.idfoy.isin(idfoyList)
    kids = (
        indivi_without_idfoy &
        (indivi.age < 25) &
        ((indivi.noiper > 0) | (indivi.noimer > 0))
        )
    log.info("Il reste {} enfants (noimer non nuls) repérés non rattachés".format(
        kids.sum()
        ))
    # Et de leurs mères sinon
    if kids.any():
        mere_declarant_potentiel = kids & (indivi.noimer > 0)
        indivi['mere_noindiv'] = (100 * indivi.idmen.fillna(0) + indivi.noimer.fillna(0)).astype('int')
        mere_noindiv = (
            100 * indivi.loc[mere_declarant_potentiel, 'idmen'].fillna(0) +
            indivi.loc[mere_declarant_potentiel, 'noimer'].fillna(0)
            ).astype('int')
        idfoy_by_noindiv = indivi.loc[
            indivi.noindiv.isin(mere_noindiv), ['noindiv', 'idfoy']
            ].dropna().astype('int').set_index('noindiv').squeeze().to_dict()
        mere_declarant_potentiel_idfoy = indivi['mere_noindiv'].map(idfoy_by_noindiv)
        mere_veritable_declarant = mere_declarant_potentiel & mere_declarant_potentiel_idfoy.isin(idfoyList)
        indivi.loc[mere_veritable_declarant, 'idfoy'] = (
            mere_declarant_potentiel_idfoy[mere_veritable_declarant].astype('int')
            )
        indivi.loc[mere_veritable_declarant, 'quifoy'] = 'pac'
    log.info("{} enfants rattachés à la mère".format(
        mere_veritable_declarant.sum()
        ))
    del mere_declarant_potentiel, mere_declarant_potentiel_idfoy, mere_noindiv, \
        mere_veritable_declarant, idfoy_by_noindiv

    idfoyList = indivi.loc[indivi.quifoy == "vous", 'idfoy'].unique()
    indivi_without_idfoy = ~indivi.idfoy.isin(idfoyList)

    # Enfants avec parents pas indiqués (noimer et noiper = 0)
    if indivi_without_idfoy.any():
        potential_idmens = indivi.loc[indivi_without_idfoy, 'idmen'].copy()
        parents = indivi.loc[indivi.idmen.isin(potential_idmens), [
            'idmen', 'age', 'quifoy', 'lpr', 'noiper', 'noimer']].copy()
        parents_by_idmen = parents.groupby('idmen').agg({
            'quifoy':
                lambda quifoy: (quifoy == 'vous').sum() == 1,
            }
        )
        parents_dummy_by_idmen = parents_by_idmen.quifoy.copy()
        parents_idmens = parents_dummy_by_idmen.index[
            parents_dummy_by_idmen.astype('bool')].tolist()
        parents_idfoy_by_idmem = indivi.loc[
            indivi.idmen.isin(parents_idmens) & (indivi.quifoy == 'vous'),
            ['idmen', 'noindiv']].dropna().astype('int').set_index('idmen').squeeze().to_dict()
        avec_parents = (
            indivi_without_idfoy &
            indivi.idmen.isin(parents_idmens) &
            (
                (indivi.age < 18) |
                (
                    (indivi.age < 25) &
                    (indivi.sali == 0) &
                    (indivi.choi == 0) &
                    (indivi.alr == 0)
                    )
                ) &
            (indivi.lpr == 4) &
            (indivi.noiper == 0) &
            (indivi.noimer == 0) &
            (indivi.lpr == 4)
            )
        indivi.loc[avec_parents, 'idfoy'] = (
            indivi.loc[avec_parents, 'idmen'].map(parents_idfoy_by_idmem))
        indivi.loc[avec_parents, 'quifoy'] = 'pac'

        log.info("Il y a {} enfants sans noiper ni noimer avec le seul vous du ménage".format(
            avec_parents.sum()
            ))
        del parents, parents_by_idmen, parents_dummy_by_idmen, parents_idfoy_by_idmem, parents_idmens

    idfoyList = indivi.loc[indivi.quifoy == "vous", 'idfoy'].unique()
    indivi_without_idfoy = ~indivi.idfoy.isin(idfoyList)

    if indivi_without_idfoy.any():
        potential_idmens = indivi.loc[indivi_without_idfoy, 'idmen'].copy()
        parents_non_pr = indivi.loc[
            indivi.idmen.isin(potential_idmens) & (indivi.quifoy == 'vous'),
            ['idmen', 'quifoy', 'noindiv', 'lpr']].copy()
        parents_by_idmen = parents_non_pr.groupby('idmen').filter(
            lambda df: (
                ((df.quifoy == 'vous').sum() >= 1) &
                (df.lpr > 2).any()
            )).query('lpr > 2')
        parents_idfoy_by_idmem = parents_by_idmen[
            ['idmen', 'noindiv']
            ].dropna().astype('int').set_index('idmen').squeeze().to_dict()
        avec_parents_non_pr = (
            indivi_without_idfoy &
            indivi.idmen.isin(parents_idfoy_by_idmem.keys()) &
            (indivi.age < 18) &
            (indivi.lpr == 4) &
            (indivi.noiper == 0) &
            (indivi.noimer == 0)
            )
        indivi.loc[avec_parents_non_pr, 'idfoy'] = (
            indivi.loc[avec_parents_non_pr, 'idmen'].map(parents_idfoy_by_idmem))
        indivi.loc[avec_parents_non_pr, 'quifoy'] = 'pac'

        log.info("Il y a {} enfants sans noiper ni noimer avec le seul vous du ménage".format(
            avec_parents_non_pr.sum()
            ))
        del parents_non_pr, parents_by_idmen, parents_idfoy_by_idmem, avec_parents_non_pr

    idfoyList = indivi.loc[indivi.quifoy == "vous", 'idfoy'].unique()
    indivi_without_idfoy = ~indivi.idfoy.isin(idfoyList)

    if indivi_without_idfoy.any():
        other_enfants = indivi_without_idfoy & (indivi.age < 18)
        potential_idmens = indivi.loc[other_enfants, 'idmen'].copy()
        declarants = indivi.loc[
            indivi.idmen.isin(potential_idmens) & (indivi.quifoy == 'vous'),
            ['idmen', 'idfoy']].dropna().astype('int').copy()
        declarants_by_idmen = declarants.groupby('idmen').agg({
            'idfoy': 'max'
            }).squeeze().to_dict()
        indivi.loc[other_enfants, 'idfoy'] = indivi.loc[other_enfants, 'idmen'].copy().map(declarants_by_idmen)
        indivi.loc[other_enfants, 'quifoy'] = 'pac'

        log.info("Il y a {} autres enfants que l'on met avec un vous du ménage".format(
            other_enfants.sum()
            ))

    idfoyList = indivi.loc[indivi.quifoy == "vous", 'idfoy'].unique()
    indivi_without_idfoy = ~indivi.idfoy.isin(idfoyList)

    if indivi_without_idfoy.any():
        other_grands_enfants = indivi_without_idfoy & (indivi.age >= 18)
        indivi.loc[other_grands_enfants, 'idfoy'] = indivi.loc[other_grands_enfants, 'noindiv']
        indivi.loc[other_grands_enfants, 'quifoy'] = 'vous'

        log.info("Il y a {} autres grans enfants (>= 18) que l'on met avec un vous du ménage".format(
            other_grands_enfants.sum()
            ))

    idfoyList = indivi.loc[indivi.quifoy == "vous", 'idfoy'].unique()
    indivi_without_idfoy = ~indivi.idfoy.isin(idfoyList)

    temporary_store['indivi_step_06_{}'.format(year)] = indivi

    assert not indivi_without_idfoy.any()

    log.info("    4.2 : On enlève les individus pour lesquels il manque le déclarant")
    fip = temporary_store['fipDat_{}'.format(year)]
    fip["declar"] = np.nan
    fip["agepf"] = np.nan

    fip.drop(["actrec", "year", "noidec"], axis = 1, inplace = True)
    fip.naia = fip.naia.astype("int32")
    fip.rename(
        columns = dict(
            ident = "idmen",
            persfip = "quifoy",
            zsali = "sali",  # Inclu les salaires non imposables des agents d'assurance
            zchoi = "choi",
            zrsti = "rsti",
            zalri = "alr"),
        inplace = True)

    is_fip_19_25 = ((year - fip.naia - 1) >= 19) & ((year - fip.naia - 1) < 25)

    # TODO: BUT for the time being we keep them in thier vous menage so the following lines are commented
    # The idmen are of the form 60XXXX we use idmen 61XXXX, 62XXXX for the idmen of the kids over 18 and less than 25

    indivi = concat([indivi, fip.loc[is_fip_19_25].copy()])
    temporary_store['indivi_step_06_{}'.format(year)] = indivi

    assert not(indivi.noindiv.duplicated().any())

    del is_fip_19_25
    indivi['age'] = year - indivi.naia - 1
    indivi['age_en_mois'] = 12 * indivi.age + 12 - indivi.naim

    indivi["quimen"] = 0
    assert indivi.lpr.notnull().all()
    indivi.loc[indivi.lpr == 1, 'quimen'] = 0
    indivi.loc[indivi.lpr == 2, 'quimen'] = 1
    indivi.loc[indivi.lpr == 3, 'quimen'] = 2
    indivi.loc[indivi.lpr == 4, 'quimen'] = 3
    indivi['not_pr_cpr'] = None  # Create a new row
    indivi.loc[indivi.lpr <= 2, 'not_pr_cpr'] = False
    indivi.loc[indivi.lpr > 2, 'not_pr_cpr'] = True

    assert indivi.not_pr_cpr.isin([True, False]).all()

    log.info("    4.3 : Creating non pr=0 and cpr=1 idmen's")

    indivi.set_index('noindiv', inplace = True, verify_integrity = True)
    test1 = indivi.loc[indivi.not_pr_cpr, ['quimen', 'idmen']].copy()
    test1['quimen'] = 2

    j = 2
    while any(test1.duplicated(['quimen', 'idmen'])):
        test1.loc[test1.duplicated(['quimen', 'idmen']), 'quimen'] = j + 1
        j += 1
    print_id(indivi)
    indivi.update(test1)
    indivi.reset_index(inplace = True)
    print_id(indivi)

    temporary_store['indivi_step_06_{}'.format(year)] = indivi
    gc.collect()
    return


@temporary_store_decorator(file_name = 'erfs')
def create_totals_second_pass(temporary_store = None, year = None):
    assert temporary_store is not None
    assert year is not None

    log.info("    5.1 : Elimination idfoy restant")
    # Voiture balai
    # On a plein d'idfoy vides, on fait 1 ménage = 1 foyer fiscal
    indivi = temporary_store['indivi_step_06_{}'.format(year)]
    idfoyList = indivi.loc[indivi.quifoy == "vous", 'idfoy'].unique()
    indivi_without_idfoy = ~indivi.idfoy.isin(idfoyList)

    indivi.loc[indivi_without_idfoy, 'quifoy'] = "pac"

    indivi.loc[indivi_without_idfoy & (indivi.quimen == 0) & (indivi.age >= 18), 'quifoy'] = "vous"
    indivi.loc[indivi_without_idfoy & (indivi.quimen == 0) & (indivi.age >= 18), 'idfoy'] = (
        indivi.loc[indivi_without_idfoy, "idmen"].astype('int') * 100 + 51
        )
    indivi.loc[indivi_without_idfoy & (indivi.quimen == 1) & (indivi.age >= 18), 'quifoy'] = "conj"

    del idfoyList
    print_id(indivi)

    # Sélectionne les variables à garder pour les steps suivants
    variables = [
        "actrec",
        "age",
        "age_en_mois",
        "chpub",
        "encadr",
        "idfoy",
        "idmen",
        "nbsala",
        "noi",
        "noindiv",
        "prosa",
        "quelfic",
        "quifoy",
        "quimen",
        "statut",
        "titc",
        "txtppb",
        "wprm",
        "rc1rev",
        "maahe",
        "sali",
        "rsti",
        "choi",
        "alr",
        "wprm",
        ]

    assert set(variables).issubset(set(indivi.columns)), \
        "Manquent les colonnes suivantes : {}".format(set(variables).difference(set(indivi.columns)))

    dropped_columns = [variable for variable in indivi.columns if variable not in variables]
    indivi.drop(dropped_columns, axis = 1, inplace = True)

    #  see http://stackoverflow.com/questions/11285613/selecting-columns
    indivi.reset_index(inplace = True)
    gc.collect()

    # TODO les actrec des fip ne sont pas codées (on le fera à la fin quand on aura rassemblé
    # les infos provenant des déclarations)
    log.info("Etape 6 : Création des variables descriptives")
    log.info("    6.1 : Variable activité")
    log.info("Variables présentes; \n {}".format(indivi.columns))

    indivi['activite'] = np.nan
    indivi.loc[indivi.actrec <= 3, 'activite'] = 0
    indivi.loc[indivi.actrec == 4, 'activite'] = 1
    indivi.loc[indivi.actrec == 5, 'activite'] = 2
    indivi.loc[indivi.actrec == 7, 'activite'] = 3
    indivi.loc[indivi.actrec == 8, 'activite'] = 4
    indivi.loc[indivi.age <= 13, 'activite'] = 2  # ce sont en fait les actrec=9
    log.info("Valeurs prises par la variable activité \n {}".format(indivi['activite'].value_counts(dropna = False)))
    # TODO: MBJ problem avec les actrec
    # TODO: FIX AND REMOVE
    indivi.loc[indivi.actrec.isnull(), 'activite'] = 5
    indivi.loc[indivi.titc.isnull(), 'titc'] = 0
    assert indivi.titc.notnull().all(), \
        "Problème avec les titc"  # On a 420 NaN pour les varaibels statut, titc etc

    log.info("    6.2 : Variable statut")
    indivi.loc[indivi.statut.isnull(), 'statut'] = 0
    indivi.statut = indivi.statut.astype('int')
    indivi.loc[indivi.statut == 11, 'statut'] = 1
    indivi.loc[indivi.statut == 12, 'statut'] = 2
    indivi.loc[indivi.statut == 13, 'statut'] = 3
    indivi.loc[indivi.statut == 21, 'statut'] = 4
    indivi.loc[indivi.statut == 22, 'statut'] = 5
    indivi.loc[indivi.statut == 33, 'statut'] = 6
    indivi.loc[indivi.statut == 34, 'statut'] = 7
    indivi.loc[indivi.statut == 35, 'statut'] = 8
    indivi.loc[indivi.statut == 43, 'statut'] = 9
    indivi.loc[indivi.statut == 44, 'statut'] = 10
    indivi.loc[indivi.statut == 45, 'statut'] = 11
    assert indivi.statut.isin(range(12)).all(), "statut value over range"
    log.info("Valeurs prises par la variable statut \n {}".format(
        indivi['statut'].value_counts(dropna = False)))

    log.info("    6.3 : variable txtppb")
    indivi.loc[indivi.txtppb.isnull(), 'txtppb'] = 0
    assert indivi.txtppb.notnull().all()
    indivi.loc[indivi.nbsala.isnull(), 'nbsala'] = 0
    indivi.nbsala = indivi.nbsala.astype('int')
    indivi.loc[indivi.nbsala == 99, 'nbsala'] = 10
    assert indivi.nbsala.isin(range(11)).all()
    log.info("Valeurs prises par la variable txtppb \n {}".format(
        indivi['txtppb'].value_counts(dropna = False)))

    log.info("    6.4 : variable chpub et CSP")
    indivi.loc[indivi.chpub.isnull(), 'chpub'] = 0
    indivi.chpub = indivi.chpub.astype('int')
    assert indivi.chpub.isin(range(11)).all()

    indivi['cadre'] = 0
    indivi.loc[indivi.prosa.isnull(), 'prosa'] = 0
    assert indivi.prosa.notnull().all()
    log.info("Valeurs prises par la variable encadr \n {}".format(indivi['encadr'].value_counts(dropna = False)))

    # encadr : 1=oui, 2=non
    indivi.loc[indivi.encadr.isnull(), 'encadr'] = 2
    indivi.loc[indivi.encadr == 0, 'encadr'] = 2
    assert indivi.encadr.notnull().all()
    assert indivi.encadr.isin([1, 2]).all()

    indivi.loc[indivi.prosa.isin([7, 8]), 'cadre'] = 1
    indivi.loc[(indivi.prosa == 9) & (indivi.encadr == 1), 'cadre'] = 1
    assert indivi.cadre.isin(range(2)).all()

    log.info(
        "Etape 7: on vérifie qu'il ne manque pas d'info sur les liens avec la personne de référence"
        )
    log.info(
        "nb de doublons idfoy/quifoy {}".format(len(indivi[indivi.duplicated(subset = ['idfoy', 'quifoy'])]))
        )

    log.info("On crée les n° de personnes à charge dans le foyer fiscal")
    assert indivi.idfoy.notnull().all()
    print_id(indivi)
    indivi['quifoy_bis'] = 2
    indivi.loc[indivi.quifoy == 'vous', 'quifoy_bis'] = 0
    indivi.loc[indivi.quifoy == 'conj', 'quifoy_bis'] = 1
    indivi.loc[indivi.quifoy == 'pac', 'quifoy_bis'] = 2
    del indivi['quifoy']
    indivi['quifoy'] = indivi.quifoy_bis.copy()
    del indivi['quifoy_bis']

    print_id(indivi)
    pac = indivi.loc[indivi['quifoy'] == 2, ['quifoy', 'idfoy', 'noindiv']].copy()
    print_id(pac)

    j = 2
    while pac.duplicated(['quifoy', 'idfoy']).any():
        pac.loc[pac.duplicated(['quifoy', 'idfoy']), 'quifoy'] = j
        j += 1

    print_id(pac)
    indivi = indivi.merge(pac, on = ['noindiv', 'idfoy'], how = "left")
    indivi['quifoy'] = indivi['quifoy_x']
    indivi['quifoy'] = where(indivi['quifoy_x'] == 2, indivi['quifoy_y'], indivi['quifoy_x'])
    del indivi['quifoy_x'], indivi['quifoy_y']
    print_id(indivi)
    del pac
    assert len(indivi[indivi.duplicated(subset = ['idfoy', 'quifoy'])]) == 0, \
        "Il y a {} doublons idfoy/quifoy".format(
            len(indivi[indivi.duplicated(subset = ['idfoy', 'quifoy'])])
            )
    print_id(indivi)

    log.info("Etape 8 : création des fichiers totaux")
    famille = temporary_store['famc_{}'.format(year)]

    log.info("    8.1 : création de tot2 & tot3")
    tot2 = indivi.merge(famille, on = 'noindiv', how = 'inner')
    # TODO: MBJ increase in number of menage/foyer when merging with family ...
    del famille

    control(tot2, debug = True, verbose = True)
    assert tot2.quifam.notnull().all()

    temporary_store['tot2_{}'.format(year)] = tot2
    del indivi
    log.info("    tot2 saved")
    tot2 = tot2[tot2.idmen.notnull()].copy()

    print_id(tot2)
    tot3 = tot2
    # TODO: check where they come from
    log.info("Avant élimination des doublons noindiv: {}".format(len(tot3)))

    tot3 = tot3.drop_duplicates(subset = 'noindiv')
    log.info("Après élimination des doublons noindiv: {}".format(len(tot3)))

    # Block to remove any unwanted duplicated pair

    control(tot3, debug = True, verbose = True)
    tot3 = tot3.drop_duplicates(subset = ['idfoy', 'quifoy'])
    log.info("Après élimination des doublons idfoy, quifoy: {}".format(len(tot3)))
    tot3 = tot3.drop_duplicates(subset = ['idfam', 'quifam'])
    log.info("Après élimination des doublons idfam, 'quifam: {}".format(len(tot3)))
    tot3 = tot3.drop_duplicates(subset = ['idmen', 'quimen'])
    log.info("Après élimination des doublons idmen, quimen: {}".format(len(tot3)))
    tot3 = tot3.drop_duplicates(subset = ['noindiv'])
    control(tot3)

    log.info("    8.2 : On ajoute les variables individualisables")

    allvars = temporary_store['ind_vars_to_remove_{}'.format(year)]
    vars2 = set(tot3.columns).difference(set(allvars))
    tot3 = tot3[list(vars2)]
    log.info("{}".format(len(tot3)))

    assert not(tot3.duplicated(subset = ['noindiv']).any()), "doublon dans tot3['noindiv']"
    lg_dup = len(tot3[tot3.duplicated(['idfoy', 'quifoy'])])
    assert lg_dup == 0, "{} pairs of idfoy/quifoy in tot3 are duplicated".format(lg_dup)

    temporary_store['tot3_{}'.format(year)] = tot3
    control(tot3)

    del tot2, allvars, tot3, vars2
    gc.collect()
    log.info("tot3 sauvegardé")


@temporary_store_decorator(file_name = 'erfs')
def create_final(temporary_store = None, year = None):

    assert temporary_store is not None
    assert year is not None

    log.info("création de final")
    foy_ind = temporary_store['foy_ind_{}'.format(year)]
    tot3 = temporary_store['tot3_{}'.format(year)]

    log.info("Stats on tot3")
    print_id(tot3)
    log.info("Stats on foy_ind")
    print_id(foy_ind)
    foy_ind.set_index(['idfoy', 'quifoy'], inplace = True, verify_integrity = True)
    tot3.set_index(['idfoy', 'quifoy'], inplace = True, verify_integrity = True)

    # tot3 = concat([tot3, foy_ind], join_axes=[tot3.index], axis=1, verify_integrity = True)

    # TODO improve this
    foy_ind.drop([u'alr', u'rsti', u'sali', u'choi'], axis = 1, inplace = True)
    tot3 = tot3.join(foy_ind)
    tot3.reset_index(inplace = True)
    foy_ind.reset_index(inplace = True)

    # tot3 = tot3.drop_duplicates(subset=['idfam', 'quifam'])
    control(tot3, verbose=True)
    final = tot3.loc[tot3.idmen.notnull(), :].copy()

    control(final, verbose=True)
    del tot3, foy_ind
    gc.collect()

    log.info("    loading fip")
    sif = temporary_store['sif_{}'.format(year)]
    log.info("Columns from sif dataframe: {}".format(sif.columns))
    log.info("    update final using fip")
    final.set_index('noindiv', inplace = True, verify_integrity = True)

    # TODO: IL FAUT UNE METHODE POUR GERER LES DOUBLES DECLARATIONS
    #  On ne garde que les sif.noindiv qui correspondent à des idfoy == "vous"
    #  Et on enlève les duplicates
    idfoys = final.loc[final.quifoy == 0, "idfoy"]
    sif = sif[sif.noindiv.isin(idfoys) & ~(sif.change.isin(['M', 'S', 'Z']))].copy()
    sif.drop_duplicates(subset = ['noindiv'], inplace = True)
    sif.set_index('noindiv', inplace = True, verify_integrity = True)
    final = final.join(sif)
    final.reset_index(inplace = True)

    control(final, debug=True)

    final['caseP'] = final.caseP.fillna(False)
    final['caseF'] = final.caseF.fillna(False)
    print_id(final)

    temporary_store['final_{}'.format(year)] = final
    log.info("final sauvegardé")
    del sif, final

if __name__ == '__main__':
    year = 2009
    logging.basicConfig(level = logging.INFO, filename = 'step_06.log', filemode = 'w')
    create_totals_first_pass(year = year)
    create_totals_second_pass(year = year)
    create_final(year = year)
    log.info("étape 06 remise en forme des données terminée")

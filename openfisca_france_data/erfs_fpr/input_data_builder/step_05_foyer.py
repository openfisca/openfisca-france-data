import gc
import logging
import numpy as np
import pandas as pd

from openfisca_survey_manager.temporary import temporary_store_decorator  # type: ignore


log = logging.getLogger(__name__)


@temporary_store_decorator(file_name = 'erfs_fpr')
def build_foyer(temporary_store = None, year = None):
    assert temporary_store is not None
    assert year is not None
    if year >= 2021:
        statut = 'etamatri_y_comp'
    else:
        statut = 'matri'
    individus = temporary_store['individus_{}'.format(year)]


    individus['idfoy'] = individus['idfam']
    individus['quifoy'] = individus['quifam']
    id_couples = individus[individus['quifam'] == 1].idfam
    celibataires = individus[~individus['idfam'].isin(id_couples)]
    couples = individus[individus['idfam'].isin(id_couples)]

    decls = pd.merge(
        couples[couples.quifam == 0][['idfam',statut]].rename(columns={statut:'statut_decl1'}),
        couples[couples.quifam == 1][['idfam',statut]].rename(columns={statut:'statut_decl2'}),
        on = 'idfam',
        how = "inner"
        )

    decls['statut_decl1'] = np.where(
        (decls.statut_decl1 != decls.statut_decl2),
        np.where(
            decls.statut_decl1.isin([1,2]) | decls.statut_decl2.isin([1,2]),
            1,
            8
            ),
        decls.statut_decl1
        )

    assert len(couples[couples.quifam.isin([0])]) == len(decls)
    couples = pd.merge(couples,decls[['idfam',"statut_decl1"]],on = 'idfam', how = 'inner')
    assert len(couples[couples.quifam.isin([0])]) == len(decls)
    
    couples_concubinage = couples[couples['statut_decl1'].isin([3,4,5,6,7,8])]
    couples_maries = couples[~couples['statut_decl1'].isin([3,4,5,6,7,8])] ## les couples avec de la non réponses sur le statut marital sont mis en mariés

    couples_concubinage['idfoy'] = np.where(couples_concubinage.quifam == 1,couples_concubinage.idfoy + len(individus),couples_concubinage.idfoy)
    couples_concubinage['quifoy'] = np.where(couples_concubinage.quifam == 1,0,couples_concubinage.quifam)
    # pour l'instant on met les conjoints dans un autre foyer seul, on ne s'occupe pas de dispatcher les personnes à charge
    tag = couples_concubinage[couples_concubinage.quifam == 1].noindiv
    assert len(individus) == (len(celibataires) + len(couples_maries) + len(couples_concubinage))

    individus['idfoy'] = np.where(individus.noindiv.isin(tag),individus.idfoy +len(individus),individus.idfoy)
    individus['quifoy'] = np.where(individus.noindiv.isin(tag),0,individus.quifoy)

    ids = individus[['idfam','idfoy']].drop_duplicates().sort_values(by =['idfam','idfoy'])
    ids['new_idfoy'] = range(len(ids))
    individus = pd.merge(individus,ids,on = ['idfam','idfoy'], how = 'inner')

    individus.drop('idfoy',axis = 1,inplace = True)
    individus.rename(columns = {'new_idfoy':'idfoy'},inplace = True, errors="raise")

    temporary_store['individus_{}'.format(year)] = individus


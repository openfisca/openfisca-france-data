# -*- coding: utf-8 -*-


import gc
import logging


from openfisca_france_data.utils import (
    id_formatter, print_id, normalizes_roles_in_entity,
    )
from openfisca_france_data.temporary import temporary_store_decorator

log = logging.getLogger(__name__)


@temporary_store_decorator(file_name = 'erfs_fpr')
def create_input_data_frame(temporary_store = None, year = None):
    assert temporary_store is not None
    assert year is not None

    log.info('step_05_create_input_data_frame: Etape finale ')
    individus = temporary_store['individus_{}'.format(year)]
    variables = [
        'activite',
        'age',
        'age_en_mois',
        'chomage_imposable',
        'categorie_salarie',
        'pensions_alimentaires_percues',
        'rag',
        'retraite_imposable',
        'ric',
        'rnc',
        'salaire_imposable',
        'idmen',
        'quimen',
        'idfoy',
        'quifoy',
        'idfam',
        'quifam',
        'noindiv',
        ]

    data_frame = create_ids_and_roles(individus)[variables].copy()
    del individus
    gc.collect()

    menages = temporary_store['menages_{}'.format(year)][['ident', 'wprm']].copy()
    menages.rename(columns = dict(ident = 'idmen'), inplace = True)

    data_frame = data_frame.merge(menages, on = 'idmen')

    for entity_id in ['idmen', 'idfoy', 'idfam']:
        log.info('Reformat ids: {}'.format(entity_id))
        data_frame = id_formatter(data_frame, entity_id)
    data_frame.reset_index(inplace = True)
    data_frame = normalizes_roles_in_entity(data_frame, 'foy')
    data_frame = normalizes_roles_in_entity(data_frame, 'men')
    print_id(data_frame)
    temporary_store['input_{}'.format(year)] = data_frame


def create_ids_and_roles(individus):
    old_by_new_variables = {
        'ident': 'idmen',
        }
    individus.rename(
        columns = old_by_new_variables,
        inplace = True,
        )
    individus['quimen'] = 9
    individus.loc[individus.lpr == 1, 'quimen'] = 0
    individus.loc[individus.lpr == 2, 'quimen'] = 1
    individus['idfoy'] = individus['idfam'].copy()
    individus['quifoy'] = individus['quifam'].copy()
    return individus.copy()


if __name__ == '__main__':
    import sys
    logging.basicConfig(level = logging.INFO, stream = sys.stdout)
    year = 2012
    create_input_data_frame(year = year)

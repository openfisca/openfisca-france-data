#from numpy import where, NaN, random
from openfisca_france.data.erf.build_survey import show_temp, load_temp, save_temp
from openfisca_france.data.erf.build_survey.utils import print_id, control, check_structure
from pandas import read_csv, HDFStore
from openfisca_france import DATA_SOURCES_DIR
import os


def final_check(year=2006):
    test_filename = os.path.join(DATA_SOURCES_DIR, "test.h5")
    survey_filename = os.path.join(DATA_SOURCES_DIR, "survey.h5")

    store = HDFStore(test_filename)
    survey = HDFStore(survey_filename)

    final2 = store.get('survey_2006')
    finalT = survey.get('survey_2006')

    varlist = [
        'adeben',
        'adfdap',
        'amois',
        'ancchom',
        'ancentr',
        'anciatm',
        'ancrech',
        'anref',
        'contra',
        'datant',
        'dimtyp',
        'ident',
        'idfoy'
        'noi',
        'nondic',
        'rabs',
        'RABSP',
        'RAISTP',
        'raistp',
        'rdem',
        'retrai',
        'sitant',
        'sp10',
        'sp11',
        'stc',
        'TXTPPB',
        ]

    for i in range(0, 10):
        varname = 'sp0' + str(i)
        varlist.append(varname)

    varlist = set(varlist)
    columns = final2.columns
    columns = set(columns)

    print(varlist.difference(columns))
    print(final2.loc[
        final2.idfoy == 603018901,
        ['idfoy', 'quifoy', 'idfam', 'quifam', 'idmen', 'quimen', 'noi']
        ].to_string()
        )

    return


if __name__ == '__main__':
    final_check()

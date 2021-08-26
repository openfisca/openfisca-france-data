import logging


from openfisca_survey_manager.surveys import SurveyCollection
from openfisca_france_data.erf import get_of2erf, get_erf2of
import numpy as np


log = logging.getLogger(__name__)


def build_erf_aggregates(variables = None, year = 2006, unit = 1e6):
    """
    Fetch the relevant aggregates from erf data
    """
    erfs_survey_collection = SurveyCollection.load(collection = "erfs")
    erfs_survey = erfs_survey_collection.surveys["erfs_{}".format(year)]


    of2erf = get_of2erf()
    erf2of = get_erf2of()

    if set(variables) <= set(of2erf.keys()):
        variables = [ of2erf[variable] for variable in variables]

    if variables is not None and "wprm" not in variables:
        variables.append("wprm")
    log.info("Fetching aggregates from erfs {} data".format(year))


    df = erfs_survey.get_values(variables = variables, table = "erf_menage")


    df.rename(columns = erf2of, inplace = True)
    wprm = df["wprm"]
    for col in df.columns:
        try:
            df[col] = df[col].astype(np.float64)
        except Exception:
            pass
    df = df.mul(wprm, axis = 0)
    for col in list(set(df.columns) - set(['ident', 'wprm'])):
        try:
            df[col] = df[col].sum()/1e6
        except Exception:
            pass

    return df.ix[0:1] # Aggregate so we only need 1 row


if __name__ == '__main__':
    df = build_erf_aggregates(variables = ["af"])
    print(df.to_string())

import pandas as pd
from yaml import load, SafeLoader
import os
import re

from openfisca_core.periods import *

from openfisca_france import FranceTaxBenefitSystem

from openfisca_france_data.felin.input_data_builder.create_variables_individuelles import create_taux_csg_remplacement
from openfisca_france_data.common import create_revenus_remplacement_bruts

margin = 1

tax_benefit_system = FranceTaxBenefitSystem()
scenario = tax_benefit_system.new_scenario()

## First part : upwards (start from *_taxable, inverse to *_gross)

# Data creation

cd = os.path.dirname(__file__)
path = os.path.join(cd, "inversion", "remplacement_2021.yaml")
year = re.match(".*([0-9]{4}).yaml", path).group(1)

with open(path) as yaml:
    individus = pd.DataFrame.from_dict(load(yaml, Loader=SafeLoader))

# Inverse incomes from net to gross : the tested functions

create_taux_csg_remplacement(individus, period(year), tax_benefit_system)
create_revenus_remplacement_bruts(individus, period(year), tax_benefit_system, revenu_type = 'net')

# Test against chomage_brut_test

fails_chomage = [i for i in individus.index if abs(individus.loc[i]["chomage_brut"]-individus.loc[i]["chomage_brut_test"])>=margin]
fails_retraite = [i for i in individus.index if abs(individus.loc[i]["retraite_brute"]-individus.loc[i]["retraite_brute_test"])>=margin]

message = "".join(
    ["For test {}, found {} for chomage_brut, tested against {}.\n".format(i,individus.loc[i]["chomage_brut"],individus.loc[i]["chomage_brut_test"]) for i in fails_chomage]+
    ["For test {}, found {} for retraite_brute, tested against {}.\n".format(i,individus.loc[i]["retraite_brute"],individus.loc[i]["retraite_brute_test"]) for i in fails_retraite]
    )

assert len(fails_chomage) + len(fails_retraite) ==0, "Some tests have failed.\n" + message

## Second part : downwards (start from gross obtained from inversion, goes back to taxable)

# Initialize the survey scenario with the gross (inverted)

# init_single_entity(scenario, init_data)
# simulation = scenario.new_simulation()

# # Computes *_taxable back from inverted *_gross

# simulation.calculate('chomage_imposable', '2021-01') == 1000
# simulation.calculate('csg_deductible_chomage', '2021-01') == 0
# simulation.calculate('csg_imposable_chomage', '2021-01') == 0
# simulation.calculate('crds_chomage', '2021-01') == 1


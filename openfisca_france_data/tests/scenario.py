# -*- coding: utf-8 -*-


import openfisca_france_data
TaxBenefitSystem = openfisca_france_data.init_country()


def test_openfisca_france_data():
    tax_benefit_system = TaxBenefitSystem()

    scenario = tax_benefit_system.new_scenario()
    scenario.init_single_entity(
        period = 2015,
        parent1 = dict(
            age = 40,
            cadre = True,
            statut = 8,
            chpub = 4,
            )
        )
    simulation = scenario.new_simulation()
    assert simulation.calculate('cadre') == True
    assert (simulation.calculate('statut') == 8).all()
    assert (simulation.calculate('chpub') == 4).all()
    assert simulation.calculate('type_sal') == 1

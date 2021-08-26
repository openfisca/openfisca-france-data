import itertools
import numpy
import pandas
import pytest

from openfisca_core import periods  # type: ignore
from openfisca_core.tools import assert_near  # type: ignore
from openfisca_france_data.erfs.scenario import ErfsSurveyScenario  # type: ignore
from openfisca_survey_manager.calibration import Calibration  # type: ignore
from openfisca_france.reforms.plf2015 import plf2015  # type: ignore


@pytest.fixture
def fake_calibration(tax_benefit_system):
    def _fake_calibration(fake_input_data: pandas.DataFrame, year: int) -> Calibration:
        input_data_frame = fake_input_data(year)

        survey_scenario = ErfsSurveyScenario.create(
            tax_benefit_system = tax_benefit_system,
            year = year,
            )

        survey_scenario.init_from_data(data = dict(input_data_frame = input_data_frame))

        calibration = Calibration(survey_scenario = survey_scenario, period = year)
        calibration.set_parameters("invlo", 3)
        calibration.set_parameters("up", 3)
        calibration.set_parameters("method", "logit")

        return calibration

    return _fake_calibration


@pytest.mark.skip(reason = "AssertionError: [0. 0.] != [20000. 10000.]")
def test_fake_survey_simulation(tax_benefit_system, fake_input_data, year: int = 2006):
    input_data_frame = fake_input_data(year)
    assert input_data_frame.salaire_imposable.loc[0] == 20000
    assert input_data_frame.salaire_imposable.loc[1] == 10000

    survey_scenario = ErfsSurveyScenario.create(
        tax_benefit_system = tax_benefit_system,
        year = year,
        )

    survey_scenario.init_from_data(data = dict(input_data_frame = input_data_frame))

    assert (input_data_frame.salaire_imposable.loc[0] == 20000).all()
    assert (input_data_frame.salaire_imposable.loc[1] == 10000).all()

    simulation = survey_scenario.simulation

    salaire_imposable = simulation.calculate_add("salaire_imposable", period = year)

    assert (salaire_imposable[0:1] == 20000).all()
    assert (salaire_imposable[1:2] == 10000).all()

    age = simulation.calculate("age", period = periods.period(year).first_month)

    assert age[0] == 77
    assert age[1] == 37

    sal_2003 = simulation.calculate_add("salaire_imposable", period = 2003)
    sal_2004 = simulation.calculate_add("salaire_imposable", period = 2004)
    sal_2005 = simulation.calculate_add("salaire_imposable", period = 2005)
    sal_2006 = simulation.calculate_add("salaire_imposable", period = 2006)

    assert (sal_2003 == 0).all()
    assert (sal_2004 == sal_2006).all()
    assert (sal_2005 == sal_2006).all()

    for year, month in itertools.product(range(2003, 2004), range(1, 13)):
        period = f"{year}-{month}"

        assert (
            simulation
            .calculate_add("salaire_imposable", period = period) == 0
            ).all()

    for year, month in itertools.product(range(2004, 2007), range(1, 13)):
        period = f"{year}-{month}"

        assert (
            simulation
            .calculate("salaire_imposable", period = period) == sal_2006 / 12
            ).all()

    data_frame_by_entity = survey_scenario.create_data_frame_by_entity(
        variables = [
            "age",
            "activite",
            "rsa_base_ressources_i",
            "menage_ordinaire_individus",
            "salaire_imposable",
            "salaire_net",
            "autonomie_financiere",
            "txtppb",
            "af_nbenf",
            "af",
            "af_majoration_enfant",
            "af_age_aine",
            "rsa_base_ressources",
            "rsa",
            "aspa",
            "aide_logement_montant_brut",
            "weight_familles",
            "revenu_disponible",
            "impo",
            ]
        )

    return data_frame_by_entity, simulation


@pytest.mark.skip(
    reason = "AttributeError: 'Calibration' object has no attribute 'simulation'",
    )
def test_fake_calibration_float(fake_calibration, year: int = 2006):
    calibration = fake_calibration(year)
    calibration.total_population = calibration.initial_total_population * 1.123

    revenu_disponible_target = 7e6
    calibration.set_target_margin("revenu_disponible", revenu_disponible_target)
    calibration.calibrate()
    calibration.set_calibrated_weights()

    simulation = calibration.survey_scenario.simulation

    assert_near(
        simulation.calculate("wprm", period=year).sum(),
        calibration.total_population,
        absolute_error_margin = None,
        relative_error_margin = 0.00001,
        )

    assert_near(
        (
            + simulation.calculate("revenu_disponible", period = year)
            * simulation.calculate("wprm", period = year)
            ).sum(),
        revenu_disponible_target,
        absolute_error_margin = None,
        relative_error_margin = 0.00001,
        )


@pytest.mark.skip(
    reason = "ValueError: Length of values does not match length of index",
    )
def test_fake_calibration_age(fake_calibration, fake_input_data, year: int = 2006):
    calibration = fake_calibration(fake_input_data, year)
    survey_scenario = calibration.survey_scenario
    calibration.total_population = calibration.initial_total_population * 1.123
    calibration.set_target_margin("age", [95, 130])
    calibration.calibrate()
    calibration.set_calibrated_weights()

    simulation = survey_scenario.simulation

    assert_near(
        simulation.calculate("wprm").sum(),
        calibration.total_population,
        absolute_error_margin = None,
        relative_error_margin = 0.00001,
        )

    age = (survey_scenario.simulation.calculate("age"),)
    weight_individus = survey_scenario.simulation.calculate("weight_individus")

    for category, target in calibration.margins_by_variable["age"]["target"].items():
        actual = ((age == category) * weight_individus).sum() / weight_individus.sum()
        target = target / numpy.sum(
            calibration
            .margins_by_variable["age"]["target"]
            .values()
            )

        assert_near(
            actual,
            target,
            absolute_error_margin = None,
            relative_error_margin = 0.00001,
            )


def test_calculate_irpp_before_and_after_plf2015(
        tax_benefit_system,
        fake_input_data,
        error_margin: int = 1,
        ):
    # On charge le PLF 2015
    reform = plf2015(tax_benefit_system)

    # Et on va calculer l'IRPP à partir des valeurs du N - 1 (2013)
    year = 2013

    survey_scenario = ErfsSurveyScenario.create(
        tax_benefit_system = reform,
        baseline_tax_benefit_system = tax_benefit_system,
        year = year,
        )

    # On charge les données
    input_data = fake_input_data(2014)

    # On ne garde que les deux parents
    input_data.loc[0, "salaire_imposable"] = 20000
    input_data.loc[1, "salaire_imposable"] = 18000
    input_data = input_data.loc[0:1].copy()

    # On initialise le survey scenario
    survey_scenario.init_from_data(data = dict(input_data_frame = input_data))

    # IRPP avant la réforme
    assert_near(
        survey_scenario.calculate_variable("irpp", use_baseline = True, period = year),
        [-10124, -869],
        error_margin,
        )

    # IRPP après la réforme
    # -911.4 + (1135 - 911.4) = -686.8
    assert_near(
        survey_scenario.calculate_variable("irpp", period = year),
        [-10118, -911.4 + (1135 - 911.4)],
        error_margin,
        )

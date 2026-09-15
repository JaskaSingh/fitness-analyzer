"""Named sample scenarios for the fitness session analyzer.

Each entry fixes a generator scenario and a seed, so every run of main.py
produces the same five reports and results can be discussed and checked.
"""

from data_generator import generate_fitness_data


SCENARIOS = {
    "resting": {
        "scenario": "resting",
        "seed": 42,
        "description": "A calm session close to the personal baseline.",
    },
    "moderate": {
        "scenario": "moderate_activity",
        "seed": 42,
        "description": "Sustained effort well above baseline.",
    },
    "high": {
        "scenario": "high_activity",
        "seed": 42,
        "description": "Hard effort, high heart rate and high movement.",
    },
    "recovering": {
        "scenario": "recovery",
        "seed": 42,
        "description": "Starts high and trends down toward the baseline.",
    },
    "unusable": {
        "scenario": "poor_quality",
        "seed": 42,
        "description": "Sensor faults and low signal quality throughout.",
    },
}


def available_samples():
    """Return the names that can be passed to load_scenario."""
    return tuple(SCENARIOS)


def load_scenario(name, participant_id="P001", number_of_windows=12):
    """Return (profile, observations) for one named sample scenario."""
    if name not in SCENARIOS:
        choices = ", ".join(SCENARIOS)
        raise ValueError(f"Unknown sample '{name}'. Choose from: {choices}")

    settings = SCENARIOS[name]
    return generate_fitness_data(
        participant_id=participant_id,
        scenario=settings["scenario"],
        seed=settings["seed"],
        number_of_windows=number_of_windows,
    )
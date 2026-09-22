"""Checks the figures quoted in the README.

This is not part of the analyzer. It prints:

1. The change from the first third to the last third of each session over 20
   seeds per scenario. This is where the 15 percent recovery threshold comes
   from.
2. How often each scenario is classified correctly over 200 seeds with 6, 12
   and 24 windows, 3000 sessions in total.

Run with: python3 sweep.py
"""

from analysis import recovery_changes
from data_generator import generate_fitness_data
from models import Session

EXPECTED = {
    "resting": "resting",
    "moderate_activity": "moderate_activity",
    "high_activity": "high_activity",
    "recovery": "recovery",
    "poor_quality": "insufficient_data",
}


def build(scenario, seed, windows):
    """Return a Session for one generator scenario, seed and length."""
    profile, raw = generate_fitness_data(
        participant_id="P001",
        scenario=scenario,
        seed=seed,
        number_of_windows=windows,
    )
    return Session.from_raw(profile, raw)


def change_ranges():
    """Print the heart rate and activity change ranges over 20 seeds."""
    print("Change from first third to last third, 20 seeds, 12 windows")
    for scenario in ("resting", "moderate_activity", "high_activity", "recovery"):
        heart_rate = []
        activity = []
        for seed in range(20):
            usable = build(scenario, seed, 12).usable_observations()
            hr_change, activity_change = recovery_changes(usable)
            heart_rate.append(hr_change)
            activity.append(activity_change)
        print(
            f"  {scenario:<18}"
            f" heart rate {min(heart_rate):+.1f}% to {max(heart_rate):+.1f}%"
            f"   activity {min(activity):+.1f}% to {max(activity):+.1f}%"
        )


def classification_agreement():
    """Print how often each scenario is classified as expected."""
    print("Classification agreement, 200 seeds per scenario")
    for windows in (6, 12, 24):
        for scenario, expected in EXPECTED.items():
            mismatches = []
            for seed in range(200):
                result = build(scenario, seed, windows).classify()
                if result != expected:
                    mismatches.append((seed, result))
            print(f"  windows={windows:<3} {scenario:<18} {200 - len(mismatches)}/200")
            for seed, result in mismatches[:5]:
                print(f"      seed {seed} gave {result}")


if __name__ == "__main__":
    change_ranges()
    print()
    classification_agreement()

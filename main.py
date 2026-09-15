"""Entry point for the fitness session analyzer.

Run with: python3 main.py
"""

from models import Session
from reporting import DetailedReport
from sample_data import SCENARIOS, load_scenario


def analyze_scenario(name):
    """Build, analyse and render one named scenario."""
    profile, raw_observations = load_scenario(name)
    session = Session.from_raw(profile, raw_observations)
    return DetailedReport(session.analyze()).render()


def main():
    """Print a detailed report for every sample scenario."""
    for name in SCENARIOS:
        print(analyze_scenario(name))
        print()
        print()


if __name__ == "__main__":
    main()
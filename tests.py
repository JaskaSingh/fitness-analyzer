"""Tests for the fitness session analyzer.

Plain assert statements, no framework. Run with: python3 tests.py
"""

from analysis import mean_of, percent_change, summarize
from models import Observation, Session
from reporting import DetailedReport, Report
from sample_data import SCENARIOS, load_scenario


EXPECTED_LABELS = {
    "resting": "resting",
    "moderate": "moderate_activity",
    "high": "high_activity",
    "recovering": "recovery",
    "unusable": "insufficient_data",
}

ANALYSIS_KEYS = (
    "participant_id",
    "total_observations",
    "usable_observations",
    "classification",
    "summary",
    "reasons",
    "rejected",
)


def build_session(name):
    """Build a Session from one named sample scenario."""
    profile, raw_observations = load_scenario(name)
    return Session.from_raw(profile, raw_observations)


def test_classification_matches_each_sample():
    """Each sample gets the label it was generated for."""
    for name in SCENARIOS:
        session = build_session(name)
        result = session.classify()
        expected = EXPECTED_LABELS[name]
        assert result == expected, f"{name}: expected {expected}, got {result}"


def test_unusable_sample_yields_no_usable_windows():
    """The unusable sample has no usable windows but still gives a full analysis."""
    session = build_session("unusable")

    assert len(session.usable_observations()) == 0
    assert len(session.observations) == 12

    analysis = session.analyze()
    for key in ANALYSIS_KEYS:
        assert key in analysis, f"missing key: {key}"

    assert analysis["usable_observations"] == 0
    assert analysis["total_observations"] == 12
    assert analysis["classification"] == "insufficient_data"
    assert len(analysis["rejected"]) == 12

    for field_name, stats in analysis["summary"].items():
        assert stats["count"] == 0, f"{field_name} should have no values"
        assert stats["average"] is None
        assert stats["minimum"] is None
        assert stats["maximum"] is None


def test_validation_reports_every_fault():
    """A window with four faults gives four issues and a clean one gives none."""
    broken = Observation(
        timestamp=99,
        heart_rate=265,
        skin_response=-1.0,
        temperature=None,
        activity_level=-0.2,
        signal_quality=0.9,
    )
    issues = broken.validation_issues()
    assert len(issues) == 4, f"expected 4 issues, got {issues}"
    assert broken.is_valid() is False
    # Bad values with a good signal, so validity and quality are separate checks.
    assert broken.is_high_quality() is True

    clean = Observation(
        timestamp=0,
        heart_rate=80,
        skin_response=1.2,
        temperature=32.5,
        activity_level=0.1,
        signal_quality=0.9,
    )
    assert clean.validation_issues() == []
    assert clean.is_valid() is True


def test_calculations_survive_empty_and_zero_input():
    """The helpers return None instead of crashing on empty or zero input."""
    assert mean_of([]) is None
    assert mean_of([2, 4]) == 3
    assert percent_change(0, 40) is None
    assert percent_change(None, 40) is None
    assert percent_change(40, None) is None
    assert percent_change(100, 80) == -20

    empty = summarize([])
    assert empty["count"] == 0
    assert empty["average"] is None


def test_detailed_report_extends_the_base_report():
    """DetailedReport adds to the base report instead of replacing it."""
    analysis = build_session("resting").analyze()
    base = Report(analysis).render()
    detailed = DetailedReport(analysis).render()

    assert base in detailed, "the base report should appear inside the detailed one"
    assert len(detailed) > len(base)
    assert "Field summary" in detailed
    assert "Field summary" not in base
    assert "Rejected windows" in detailed
    assert "Rejected windows" not in base


TESTS = (
    test_classification_matches_each_sample,
    test_unusable_sample_yields_no_usable_windows,
    test_validation_reports_every_fault,
    test_calculations_survive_empty_and_zero_input,
    test_detailed_report_extends_the_base_report,
)


def run_all():
    """Run every test and print a pass or fail line for each."""
    passed = 0
    failed = 0
    for test in TESTS:
        try:
            test()
        except AssertionError as error:
            failed += 1
            print(f"FAIL  {test.__name__}: {error}")
        except Exception as error:
            failed += 1
            print(f"ERROR {test.__name__}: {type(error).__name__}: {error}")
        else:
            passed += 1
            print(f"PASS  {test.__name__}")

    print()
    print(f"{passed} passed, {failed} failed, {len(TESTS)} total")
    return failed == 0


if __name__ == "__main__":
    run_all()

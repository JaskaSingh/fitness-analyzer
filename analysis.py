"""Calculation helpers for the fitness session analyzer."""

INTENSITY_LEVELS = ("resting", "moderate_activity", "high_activity")

RECOVERY_THRESHOLD = -15.0

def mean_of(values):
    """Return the arithmetic mean, or None when there is nothing to average."""
    if not values:
        return None
    return sum(values) / len(values)


def collect_field(observations, field_name):
    """Return the values of one field across observations, skipping None.

    The field is looked up by name at runtime, so one function serves every
    field rather than five near-identical ones.
    """
    values = []
    for observation in observations:
        value = getattr(observation, field_name, None)
        if value is not None:
            values.append(value)
    return values


def summarize(values):
    """Return average, minimum, maximum and count for a list of values.

    All four keys are always present. An empty list gives None for the three
    statistics and a count of 0, so callers can read the dictionary without
    checking whether it has the keys they expect.
    """
    if not values:
        return {
            "average": None,
            "minimum": None,
            "maximum": None,
            "count": 0,
        }
    return {
        "average": mean_of(values),
        "minimum": min(values),
        "maximum": max(values),
        "count": len(values),
    }


def percent_change(earlier, later):
    """Return the change from earlier to later as a percentage of earlier.

    Returns None when either value is missing or when earlier is zero, since
    there is no meaningful percentage of nothing. A negative result means the
    value fell.
    """
    if earlier is None or later is None:
        return None
    if earlier == 0:
        return None
    return (later - earlier) / earlier * 100


def format_value(value, digits=1):
    """Return a value rounded for display, or a dash when it is missing."""
    if value is None:
        return "-"
    if isinstance(value, float):
        return round(value, digits)
    return value

def recovery_changes(observations):
    """Return the percentage change in heart rate and activity across a session.

    The first third of the observations is compared against the last third.
    Returns a pair of None values when there are too few observations to split
    or when a field has no measurements to average.
    """
    third = len(observations) // 3
    if third < 1:
        return None, None

    first = observations[:third]
    last = observations[-third:]

    heart_rate_change = percent_change(
        mean_of(collect_field(first, "heart_rate")),
        mean_of(collect_field(last, "heart_rate")),
    )
    activity_change = percent_change(
        mean_of(collect_field(first, "activity_level")),
        mean_of(collect_field(last, "activity_level")),
    )
    return heart_rate_change, activity_change


def detect_recovery(observations, threshold=RECOVERY_THRESHOLD):
    """True when both heart rate and activity fall across the session.

    Recovery is reported only when both signals decline by more than the
    threshold, because activity alone is unreliable in low-effort sessions
    where small absolute values produce large percentage swings.
    """
    heart_rate_change, activity_change = recovery_changes(observations)
    if heart_rate_change is None or activity_change is None:
        return False
    return heart_rate_change < threshold and activity_change < threshold


def classify_intensity(heart_rate_delta, activity_average):
    """Return an intensity level from the heart rate delta and mean activity.

    Each signal is classified on its own scale and the lower of the two is
    returned, so a session counts as high intensity only when both agree.
    """
    if heart_rate_delta is None or activity_average is None:
        return None

    if heart_rate_delta < 15:
        by_heart_rate = 0
    elif heart_rate_delta <= 42:
        by_heart_rate = 1
    else:
        by_heart_rate = 2

    if activity_average < 0.28:
        by_activity = 0
    elif activity_average <= 0.67:
        by_activity = 1
    else:
        by_activity = 2

    return INTENSITY_LEVELS[min(by_heart_rate, by_activity)]
"""Calculation helpers for the fitness session analyzer."""

INTENSITY_LEVELS = ("resting", "moderate_activity", "high_activity")

RECOVERY_THRESHOLD = -15.0


def mean_of(values):
    """Return the arithmetic mean, or None when there is nothing to average."""
    if not values:
        return None
    return sum(values) / len(values)


def collect_field(observations, field_name):
    """Return one field's values from a list of observations, skipping None.

    The field is looked up by name with getattr, so the same function works
    for every field.
    """
    values = []
    for observation in observations:
        value = getattr(observation, field_name, None)
        if value is not None:
            values.append(value)
    return values


def summarize(values):
    """Return average, minimum, maximum and count for a list of values.

    An empty list still returns all four keys, with None for the statistics
    and 0 for the count.
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

    Returns None if either value is missing or if earlier is zero. A negative
    result means the value went down.
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
    """Return the percentage change in heart rate and activity over a session.

    Compares the average of the first third of the observations with the last
    third. Returns (None, None) if there are fewer than three observations, and
    None for a field that has no values to average.
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
    """Return True if heart rate and activity both drop by more than the threshold.

    Both have to drop, because activity on its own is unreliable in low-effort
    sessions where small values give large percentage swings.
    """
    heart_rate_change, activity_change = recovery_changes(observations)
    if heart_rate_change is None or activity_change is None:
        return False
    return heart_rate_change < threshold and activity_change < threshold


def classify_intensity(heart_rate_delta, activity_average):
    """Return an intensity level from the heart rate delta and mean activity.

    Each signal gets its own level and the lower one is used, so a session is
    only high activity if both signals agree.
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

"""Calculation helpers for the fitness session analyzer."""


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
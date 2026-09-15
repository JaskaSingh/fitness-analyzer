"""Domain classes for the fitness session analyzer"""

from analysis import (
    RECOVERY_THRESHOLD,
    classify_intensity,
    collect_field,
    detect_recovery,
    mean_of,
    recovery_changes,
    summarize,
)

class Observation:
    """A single observation window from a wearable device."""

    def __init__(
        self,
        timestamp,
        heart_rate,
        skin_response,
        temperature,
        activity_level,
        signal_quality,
    ):
        self.timestamp = timestamp
        self.heart_rate = heart_rate
        self.skin_response = skin_response
        self.temperature = temperature
        self.activity_level = activity_level
        self.signal_quality = signal_quality

    @classmethod
    def from_dict(cls, raw):
        """Build an Observation from one generator dictionary."""
        return cls(
            timestamp=raw.get("timestamp"),
            heart_rate=raw.get("heart_rate"),
            skin_response=raw.get("skin_response"),
            temperature=raw.get("temperature"),
            activity_level=raw.get("activity_level"),
            signal_quality=raw.get("signal_quality"),
        )

    def is_high_quality(self, threshold=0.7):
        """True when the signal quality is above the threshold."""
        if self.signal_quality is None:
            return False
        return self.signal_quality > threshold

    def validation_issues(self):
        """Return a list of problems with this observation.

        An empty list means the observation passed every rule.
        """
        issues = []

        if self.heart_rate is None:
            issues.append("heart_rate missing")
        elif not 35 <= self.heart_rate <= 205:
            issues.append(f"heart_rate {self.heart_rate} outside 35-205")

        if self.activity_level is None:
            issues.append("activity_level missing")
        elif not 0 <= self.activity_level <= 1:
            issues.append(f"activity_level {self.activity_level} outside 0-1")

        if self.signal_quality is None:
            issues.append("signal_quality missing")
        elif not 0 <= self.signal_quality <= 1:
            issues.append(f"signal_quality {self.signal_quality} outside 0-1")

        if self.temperature is None:
            issues.append("temperature missing")
        elif not 25 <= self.temperature <= 42:
            issues.append(f"temperature {self.temperature} outside 25-42")

        if self.skin_response is None:
            issues.append("skin_response missing")
        elif self.skin_response < 0:
            issues.append(f"skin_response {self.skin_response} below 0")

        return issues

    def is_valid(self):
        """True when the observation has no validation issues."""
        return not self.validation_issues()
    
    def __repr__(self):
        return (
            f"Observation(t={self.timestamp}, hr={self.heart_rate}, "
            f"activity={self.activity_level}, quality={self.signal_quality})"
        )

class Participant:
    """A participant and their personal baseline measurements."""

    def __init__(
        self,
        participant_id,
        baseline_heart_rate,
        baseline_skin_response,
        baseline_temperature,
    ):
        self._participant_id = participant_id
        self._baseline_heart_rate = baseline_heart_rate
        self._baseline_skin_response = baseline_skin_response
        self._baseline_temperature = baseline_temperature

    @classmethod
    def from_dict(cls, raw):
        """Build a Participant from the generator profile dictionary."""
        return cls(
            participant_id=raw.get("participant_id"),
            baseline_heart_rate=raw.get("baseline_heart_rate"),
            baseline_skin_response=raw.get("baseline_skin_response"),
            baseline_temperature=raw.get("baseline_temperature"),
        )

    @property
    def participant_id(self):
        return self._participant_id

    @property
    def baseline_heart_rate(self):
        return self._baseline_heart_rate

    @property
    def baseline_skin_response(self):
        return self._baseline_skin_response

    @property
    def baseline_temperature(self):
        return self._baseline_temperature

    def heart_rate_delta(self, measured):
        """How far a measured heart rate sits above this participant's baseline.

        Returns None when the measurement is missing or when no baseline is
        known, so callers can skip the window instead of comparing against
        nothing. A negative result means the measurement sits below baseline.
        """
        if measured is None or self._baseline_heart_rate is None:
            return None
        return measured - self._baseline_heart_rate

    def __repr__(self):
        return (
            f"Participant(id={self._participant_id}, "
            f"hr={self._baseline_heart_rate}, "
            f"skin={self._baseline_skin_response}, "
            f"temp={self._baseline_temperature})"
        )    

class Session:
    """A training session: one participant and their observation windows."""

    SUMMARY_FIELDS = (
            "heart_rate",
            "skin_response",
            "temperature",
            "activity_level",
            "signal_quality",
        )

    def __init__(self, participant, observations):
        self.participant = participant
        self.observations = observations

    @classmethod
    def from_raw(cls, profile, raw_observations):
        """Build a Session directly from generator output."""
        participant = Participant.from_dict(profile)
        observations = [Observation.from_dict(item) for item in raw_observations]
        return cls(participant, observations)

    def usable_observations(self):
        """Return only the observations worth analysing.

        A window is usable when every value passes validation and the sensor
        reports enough signal quality for those values to be trusted. Those are
        two separate questions, which is why they are two separate checks.
        """
        usable = []
        for observation in self.observations:
            if not observation.is_valid():
                continue
            if not observation.is_high_quality():
                continue
            usable.append(observation)
        return usable

    def rejected_observations(self):
        """Return the windows that were excluded, each with its reasons.

        Validation problems and low signal quality are reported separately,
        because a value that cannot be real and a value the sensor does not
        vouch for are different facts and the report should not merge them.
        """
        rejected = []
        for observation in self.observations:
            issues = observation.validation_issues()
            low_quality = not observation.is_high_quality()
            if not issues and not low_quality:
                continue
            rejected.append(
                {
                    "timestamp": observation.timestamp,
                    "issues": issues,
                    "low_signal_quality": low_quality,
                    "signal_quality": observation.signal_quality,
                }
            )
        return rejected

    def summary(self):
        """Return summary statistics for each field across usable observations.

        Fields are summarised only over windows that passed validation and the
        quality check, so a session with nothing usable returns a dictionary
        with the same shape and zero counts throughout.
        """
        usable = self.usable_observations()
        result = {}
        for field_name in self.SUMMARY_FIELDS:
            result[field_name] = summarize(collect_field(usable, field_name))
        return result

    def classify(self):
        """Return the session classification.

        The order of the checks matters. Insufficient data comes first because
        no other question can be answered without measurements. Recovery comes
        before intensity because a recovering session averages out to a middling
        effort level, so the intensity rules would describe it as moderate and
        lose the fact that it was trending down.
        """
        usable = self.usable_observations()
        if not usable:
            return "insufficient_data"

        if detect_recovery(usable):
            return "recovery"

        heart_rates = collect_field(usable, "heart_rate")
        activity_levels = collect_field(usable, "activity_level")

        heart_rate_delta = self.participant.heart_rate_delta(mean_of(heart_rates))
        activity_average = mean_of(activity_levels)

        level = classify_intensity(heart_rate_delta, activity_average)
        if level is None:
            return "insufficient_data"
        return level

    def analyze(self):
        """Return the full analysis of this session as one dictionary.

        Everything the report needs is assembled here, so the reporting layer
        formats a result rather than recalculating one.
        """
        usable = self.usable_observations()

        heart_rate_delta = None
        activity_average = None
        if usable:
            heart_rate_delta = self.participant.heart_rate_delta(
                mean_of(collect_field(usable, "heart_rate"))
            )
            activity_average = mean_of(collect_field(usable, "activity_level"))

        heart_rate_change, activity_change = recovery_changes(usable)

        return {
            "participant_id": self.participant.participant_id,
            "total_observations": len(self.observations),
            "usable_observations": len(usable),
            "classification": self.classify(),
            "summary": self.summary(),
            "reasons": {
                "heart_rate_delta": heart_rate_delta,
                "activity_average": activity_average,
                "heart_rate_change_percent": heart_rate_change,
                "activity_change_percent": activity_change,
                "recovery_threshold_percent": RECOVERY_THRESHOLD,
            },
            "rejected": self.rejected_observations(),
        }

    def __repr__(self):
        return (
            f"Session(participant={self.participant.participant_id}, "
            f"windows={len(self.observations)}, "
            f"usable={len(self.usable_observations())})"
        )


if __name__ == "__main__":
    from data_generator import generate_fitness_data
    from reporting import Report, DetailedReport

    profile, raw_observations = generate_fitness_data(
        participant_id="P001",
        scenario="recovery",
        seed=42,
        number_of_windows=12,
    )

    session = Session.from_raw(profile, raw_observations)

    for observation in session.observations:
        print(observation)
    print()
    print(f"Usable: {len(session.usable_observations())} of {len(session.observations)}")

    # Hand-built window with several faults at once. The generator never
    # produces more than one fault per window, so this is the only case that
    # exercises validation_issues returning a list of more than one item. It is
    # not part of the session and does not affect any count above.
    broken = Observation(
        timestamp=99,
        heart_rate=265,
        skin_response=-1.0,
        temperature=None,
        activity_level=-0.2,
        signal_quality=0.9,
    )
    print("Multi-fault check:", broken.validation_issues())

    analysis = session.analyze()

    print()
    print(DetailedReport(analysis).render())
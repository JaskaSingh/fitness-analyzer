"""Domain classes for the fitness session analyzer"""

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

        A window is usable when it carries both values the classification rules
        need and the signal quality is high enough to trust them.
        """
        usable = []
        for observation in self.observations:
            if observation.heart_rate is None:
                continue
            if observation.activity_level is None:
                continue
            if not observation.is_high_quality():
                continue
            usable.append(observation)
        return usable

    def __repr__(self):
        return (
            f"Session(participant={self.participant.participant_id}, "
            f"windows={len(self.observations)}, "
            f"usable={len(self.usable_observations())})"
        )


if __name__ == "__main__":
    from data_generator import generate_fitness_data

    profile, raw_observations = generate_fitness_data(
        participant_id="P001",
        scenario="poor_quality",
        seed=42,
        number_of_windows=12,
    )

    session = Session.from_raw(profile, raw_observations)

    print("Participant:", session.participant)
    print("Delta for 95 bpm:", session.participant.heart_rate_delta(95))
    print("Delta for missing:", session.participant.heart_rate_delta(None))
    print()

    for observation in session.observations:
        print(observation, "high quality:", observation.is_high_quality())
    print()

    usable = session.usable_observations()
    print(f"Usable: {len(usable)} of {len(session.observations)}")
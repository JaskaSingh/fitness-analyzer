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

if __name__ == "__main__":
    from data_generator import generate_fitness_data

    profile, raw_observations = generate_fitness_data(
        participant_id="P001",
        scenario="resting",
        seed=42,
        number_of_windows=12,
    )

    print("Profile:", profile)
    print()

    observations = [Observation.from_dict(item) for item in raw_observations]

    for observation in observations:
        print(observation, "high quality:", observation.is_high_quality())
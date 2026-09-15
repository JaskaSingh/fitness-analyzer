"""Report rendering for the fitness session analyzer.

Reports return strings rather than printing them, so the caller decides where
the output goes and the tests can assert on the content.
"""

from analysis import format_value


CLASSIFICATION_LABELS = {
    "resting": "Resting",
    "moderate_activity": "Moderate activity",
    "high_activity": "High activity",
    "recovery": "Recovering",
    "insufficient_data": "Insufficient data",
}


class Report:
    """A short summary of one analysed session."""

    def __init__(self, analysis):
        self.analysis = analysis

    def classification_label(self):
        """Return the classification in readable form."""
        classification = self.analysis.get("classification")
        return CLASSIFICATION_LABELS.get(classification, str(classification))

    def render(self):
        """Return the report as a string."""
        reasons = self.analysis.get("reasons", {})
        lines = [
            "Session report",
            "=" * 40,
            f"Participant:    {self.analysis.get('participant_id')}",
            f"Classification: {self.classification_label()}",
            f"Usable windows: {self.analysis.get('usable_observations')}"
            f" of {self.analysis.get('total_observations')}",
            f"Heart rate above baseline: {format_value(reasons.get('heart_rate_delta'))} bpm",
            f"Mean activity level:       {format_value(reasons.get('activity_average'), 2)}",
        ]
        return "\n".join(lines)


class DetailedReport(Report):
    """The short report plus the per-field table, the reasoning and rejections."""

    def render(self):
        """Return the base report extended with supporting detail."""
        lines = [super().render()]

        lines.append("")
        lines.append("Field summary")
        lines.append("-" * 40)
        lines.append(f"{'field':<16}{'avg':>8}{'min':>8}{'max':>8}{'n':>5}")
        for field_name, stats in self.analysis.get("summary", {}).items():
            lines.append(
                f"{field_name:<16}"
                f"{format_value(stats.get('average'), 2):>8}"
                f"{format_value(stats.get('minimum'), 2):>8}"
                f"{format_value(stats.get('maximum'), 2):>8}"
                f"{stats.get('count'):>5}"
            )

        reasons = self.analysis.get("reasons", {})
        threshold = reasons.get("recovery_threshold_percent")
        lines.append("")
        lines.append("Why this classification")
        lines.append("-" * 40)

        raw_heart_rate_change = reasons.get("heart_rate_change_percent")
        raw_activity_change = reasons.get("activity_change_percent")
        heart_rate_change = (
            "-" if raw_heart_rate_change is None
            else f"{format_value(raw_heart_rate_change)}%"
        )
        activity_change = (
            "-" if raw_activity_change is None
            else f"{format_value(raw_activity_change)}%"
        )

        lines.append(f"Heart rate change across session: {heart_rate_change}")
        lines.append(f"Activity change across session:   {activity_change}")
        lines.append(
            f"Recovery is reported when both fall below "
            f"{format_value(threshold)}%."
        )

        rejected = self.analysis.get("rejected", [])
        lines.append("")
        lines.append(f"Rejected windows ({len(rejected)})")
        lines.append("-" * 40)
        if not rejected:
            lines.append("None. Every window passed validation and the quality check.")
        else:
            for entry in rejected:
                reasons_text = list(entry.get("issues", []))
                if entry.get("low_signal_quality"):
                    quality = format_value(entry.get("signal_quality"), 2)
                    reasons_text.append(f"signal quality {quality} too low")
                lines.append(f"  t={entry.get('timestamp')}: " + "; ".join(reasons_text))

        return "\n".join(lines)
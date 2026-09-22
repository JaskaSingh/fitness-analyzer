# Smart Fitness Session Analyzer

**Selected option:** Option A

**Name:** Jaskamal Singh Thiara
**Student number:** s374983
**Course:** ACIT4420 Problem Solving with Scripting
**Python version:** 3.12.4

This program analyses wearable fitness data. It reads simulated sensor
observations, checks them for bad values, calculates summary statistics,
classifies the session and prints a report explaining the result.

## Installation and running

Only the Python standard library is used, so there is nothing to install.

```
git clone [FILL IN REPOSITORY URL]
cd fitness-analyzer
python3 main.py
```

This prints a detailed report for each of the five sample scenarios. On some
systems `python main.py` works too. I developed and tested it with Python
3.12.4 on macOS.

To run the tests:

```
python3 tests.py
```

## Project structure

| File | Contents |
|---|---|
| `main.py` | Entry point. Runs and reports on all five sample scenarios. |
| `models.py` | Domain classes: `Observation`, `Participant`, `Session`. |
| `analysis.py` | Standalone calculation functions and the classification rules. |
| `reporting.py` | Report classes: `Report` and `DetailedReport`. |
| `sample_data.py` | The five sample scenarios with fixed seeds. |
| `tests.py` | Five tests using plain assertions. |
| `data_generator.py` | The provided simulator. Not modified. |
| `example_usage.py` | The provided example for the simulator. Not modified. |
| `sweep.py` | Script that reproduces the threshold figures in this README. |
| `requirements.txt` | States that no third-party packages are needed. |

## Class design

**`Observation`** is one measurement window from the device. It holds the six
raw values and can check itself: whether the signal quality is high enough,
which values are invalid and whether it is valid overall. It knows nothing
about participants or sessions, since checking one window only needs that
window's values.

**`Participant`** is the person and their three baseline values. Its method
`heart_rate_delta` returns how far a heart rate is above that person's own
baseline. This means a heart rate of 105 is judged against the individual and
not a general average.

**`Session`** combines a `Participant` with a list of `Observation` objects. It
picks out the usable windows, calculates summary statistics, classifies the
session and builds the full analysis dictionary. It leaves validity checks to
`Observation`, baseline comparisons to `Participant` and the arithmetic to
`analysis.py`.

**`Report`** turns an analysis dictionary into a short text summary.
**`DetailedReport`** adds a table for each field, the reasons behind the
classification and the rejected windows. Both return a string instead of
printing, so `main.py` decides what to do with the output and the tests can
check the text.

## Object-oriented concepts

There are five classes: three in `models.py` and two in `reporting.py`.

**Composition.** `Session` holds a `Participant` and a list of `Observation`
objects instead of inheriting from them. A session is not a type of
participant, it has one. When `Session` needs to know if a window is usable it
asks the `Observation`, and when it needs a heart rate compared to baseline it
asks the `Participant`.

**Encapsulation.** `Participant` stores its values as `_participant_id`,
`_baseline_heart_rate`, `_baseline_skin_response` and `_baseline_temperature`,
and each one is exposed through a `@property`. They can be read like normal
attributes, but since there is no setter, `participant.baseline_heart_rate =
70` raises `AttributeError`. I wanted the baselines to be read-only because
every classification is measured against them. If one could be changed in the
middle of an analysis, the results would no longer be comparable and nothing
would show that it had happened.

**Inheritance and overriding.** `DetailedReport` inherits from `Report` and
overrides `render`. It first calls `super().render()` and then adds its own
sections, so the base report is never copied. If I change the base report, the
detailed one picks up the change automatically. `classification_label` is also
only defined in `Report` and used by both classes. `tests.py` checks that the
base report appears inside the detailed one, so the test fails if someone
replaces the `super()` call with copied code.

**Class methods.** There are three, and all of them are alternative
constructors. `Observation.from_dict` and `Participant.from_dict` build objects
from the dictionaries the generator returns. This keeps the generator's key
names in one place, so if the data format changed I would only need to update
one method. `Session.from_raw` takes both parts of the generator output and
builds the whole session. Without it, every caller would need to build the
participant, convert each observation and pass them in the right order. With
it, `main.py` does it in one line. They are class methods and not static
methods because each one returns a new instance of its class through `cls`.

**Standalone functions.** `analysis.py` has eight functions outside any class:
`mean_of`, `collect_field`, `summarize`, `percent_change`, `format_value`,
`recovery_changes`, `detect_recovery` and `classify_intensity`. Calculating an
average has nothing to do with a session, so these work on plain values. That
also makes them easy to test on their own, and the checks for empty lists and
division by zero only need to exist in one place.

## Assumptions and classification rules

### Validation rules

A window is rejected if a value is missing or outside its physical range.

| Field | Accepted range |
|---|---|
| `heart_rate` | 35 to 205 bpm |
| `activity_level` | 0 to 1 |
| `signal_quality` | 0 to 1 |
| `temperature` | 25 to 42 degrees C |
| `skin_response` | 0 or above |

Each field is checked for `None` before the range check, because comparing
`None` to a number raises `TypeError`. This is not just a theoretical case. The
`poor_quality` scenario sets `heart_rate` to `None` in every fourth window.

`validation_issues` returns a list of messages that include the bad value, so
the report can say what was wrong. It returns a list because one window can
break several rules at once. The generator never puts more than one fault in a
window, so `tests.py` builds a window with four faults to test this.

### Validation and signal quality are separate

A heart rate of 265 cannot be real. A heart rate of 72 with a signal quality of
0.13 might be completely correct, but the sensor does not trust it. Both
windows are excluded, but the report shows which kind of problem each one had.
Keeping them separate also means a later version could handle them differently,
for example by accepting a low-quality reading when the windows around it
agree. An impossible value could never be accepted.

This was my own design choice. In the `poor_quality` scenario every window
fails both checks at the same time, so none of the sample scenarios shows the
difference. The hand-built window in `tests.py` does. It has four invalid
values but a signal quality of 0.9, and the test checks that it is invalid and
high quality at the same time.

A window is only used in the analysis if it is valid and its signal quality is
above 0.7.

### Classification order

1. **Insufficient data**, if no windows are usable.
2. **Recovering**, if both heart rate and activity drop across the session.
3. **Intensity**, which is resting, moderate activity or high activity.

Insufficient data comes first because nothing else can be decided without
measurements. Recovery comes before intensity because a session that starts
high and ends low averages out to something in the middle. The recovery sample
has a heart rate 34.8 bpm above baseline and a mean activity of 0.48, which the
intensity rules would call moderate activity. The averages are correct, but
they hide the fact that the session was going down the whole time.

### Recovery threshold

A session is classified as recovering when both heart rate and activity drop
by more than 15 percent from the first third of the usable windows to the last
third.

I based the 15 percent on measurements. This table shows the change from the
first third to the last third over 20 seeds per scenario with 12 windows each
(`python3 sweep.py` reproduces it):

| Scenario | Heart rate change | Activity change |
|---|---|---|
| resting | -6.0% to +4.4% | -39.3% to +168.2% |
| moderate | -8.1% to +6.3% | -16.4% to +36.1% |
| high | -9.1% to +7.1% | -10.6% to +20.5% |
| recovery | -40.8% to -26.4% | -78.4% to -64.1% |

Heart rate separates the groups clearly. No other scenario dropped more than
9.1 percent and no recovery session dropped less than 26.4 percent, so 15
percent leaves a good margin on both sides. The reports from `main.py` show the
same thing. The three steady scenarios change by 0.3, 1.0 and 0.8 percent,
while the recovering one drops 30.2 percent.

Activity on its own would not work. Resting activity is small random values
between 0.03 and 0.20, so the percentages jump around a lot even though the
actual change is tiny. The resting report shows activity going up 19 percent,
which means nothing. Requiring both to drop fixes this, since a resting session
never shows a real drop in heart rate.

### Intensity thresholds

Heart rate and activity each get their own level, and the lower of the two is
used. A session is only high activity if both signals agree.

| Level | Heart rate above baseline | Mean activity level |
|---|---|---|
| Resting | under 15 bpm | under 0.28 |
| Moderate activity | 15 to 42 bpm | 0.28 to 0.67 |
| High activity | above 42 bpm | above 0.67 |

The limits sit between the ranges the simulator uses, where the heart rate
offset is around 2, 28 and 58 bpm for the three levels. I chose to use the
lower level because a high heart rate with little movement could be stress,
illness or a sensor error. Calling that high activity would claim more than the
data shows.

### Other assumptions

Four of the five classification names are the same as the generator's scenario
names. The fifth is different on purpose. `poor_quality` describes the input,
while `insufficient_data` is what the program can conclude from it. `tests.py`
maps each sample to its expected label in `EXPECTED_LABELS`.

Each sample in `sample_data.py` has a fixed seed, so every run gives the same
reports and the numbers in this README stay correct.

Summary statistics keep full precision and are only rounded when they are
printed.

The `count` in each field summary is the number of values that were actually
used, not the number of windows. These can differ if a field is missing in some
windows.

## Example output

The recovering scenario from `python3 main.py`:

```
Session report
========================================
Participant:    P001
Classification: Recovering
Usable windows: 12 of 12
Heart rate above baseline: 34.8 bpm
Mean activity level:       0.48

Field summary
----------------------------------------
field                avg     min     max    n
heart_rate        112.83      86     141   12
skin_response       1.57    1.22    1.93   12
temperature        33.05   32.81   33.34   12
activity_level      0.48     0.1    0.88   12
signal_quality      0.91    0.88    0.94   12

Why this classification
----------------------------------------
Heart rate change across session: -30.2%
Activity change across session:   -77.9%
Recovery is reported when both fall below -15.0%.

Rejected windows (0)
----------------------------------------
None. Every window passed validation and the quality check.
```

For the insufficient data scenario the report has the same layout, with a dash
wherever a value could not be calculated and a line for each of the twelve
rejected windows explaining why it was rejected.

## Testing

`python3 tests.py` runs five tests covering normal, unusual and invalid input.

1. Each of the five samples gets the classification it was generated for.
2. The unusable sample has zero usable windows out of twelve, but the analysis
   dictionary still has every key, with a count of zero and `None` for every
   statistic.
3. A window with four faults gives four issues and a clean window gives none.
   The faulty window is also checked to be high quality, which shows that
   validity and signal quality are separate.
4. `mean_of([])` and `percent_change(0, 40)` return `None` instead of crashing.
5. The base report appears inside the detailed report, and the extra sections
   only appear in the detailed one.

```
PASS  test_classification_matches_each_sample
PASS  test_unusable_sample_yields_no_usable_windows
PASS  test_validation_reports_every_fault
PASS  test_calculations_survive_empty_and_zero_input
PASS  test_detailed_report_extends_the_base_report

5 passed, 0 failed, 5 total
```

## Known limitations

**The thresholds are fitted to this simulator.** Both the intensity limits and
the 15 percent recovery threshold come from the ranges in `data_generator.py`.
They have not been tested on real wearable data, and a different device or
group of people would probably need new values.

**Recovery needs at least three usable windows.** With fewer than three, the
session cannot be split into thirds, so `detect_recovery` returns `False`. A
very short session will never be classified as recovering.

**The thirds are based on position, not time.** If some windows in the middle
of a session are rejected, the first third of the usable windows might not
match the first third of the session in time. This does not affect the sample
scenarios, where either every window or no window is rejected, but it could
matter with real data.

**A wrong field name fails quietly.** `collect_field` gives `getattr` a default
value, so a typo in `SUMMARY_FIELDS` gives an empty list and a count of zero
instead of an error. The field names are only written in one place and a typo
would show up as a zero in the report, so I accepted this.

**`analyze` repeats some work.** It calls `classify`, which builds the usable
list and calculates the thirds again. With twelve windows this makes no
difference, and I preferred keeping `classify` usable on its own. With much
larger datasets it would be worth changing.

**The thresholds only work because the scenarios are well separated.** Running
`python3 sweep.py` tests 200 seeds per scenario with 6, 12 and 24 windows, 3000
sessions in total, and every one was classified correctly. That includes
recovery with only 6 windows, where each third is only two windows. This shows
the thresholds work for this simulator, but data where the levels overlap more
would give sessions that no fixed threshold could classify correctly.

## Sources and use of AI

`data_generator.py` and `example_usage.py` were provided with the assignment
and have not been modified.

I used Claude (Anthropic) as a supporting tool during parts of the project. It
was used to help clarify programming concepts, improve code structure and
documentation, assist with identifying appropriate classification thresholds
and improve the wording and organisation of the README. The implementation,
testing, interpretation of results and final design decisions were carried out
by me. I reviewed, tested and critically assessed all AI-assisted suggestions
before including them in the final work.

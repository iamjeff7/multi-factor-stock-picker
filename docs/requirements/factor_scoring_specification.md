# factor_scoring_specification.md

## 1. Purpose

Define the official methodology for transforming raw entry signal outputs into standardized factor scores.

This specification exists between:

```text
Entry Signal
    →
Factor Scoring
    →
Factor Combination
```

The objective is to make fundamentally different signals directly comparable and suitable for combination.

Examples:

```text
Momentum
ROE
PE Ratio
Revenue Growth
Volatility
```

must all become comparable factor scores regardless of their original scale.

---

## 2. Scope

This specification defines:

- Cross-sectional scoring
- Ranking methodology
- Score normalization
- Missing value handling
- Tie handling
- Output schemas

This specification does not define:

- Entry signal generation
- Factor weighting
- Multi-factor combination
- Portfolio construction

---

## 3. Core Principles

### 3.1 Cross-Sectional Evaluation

Scores are computed relative to other securities in the same universe on the same evaluation date.

Factor scores are not calculated using historical distributions.

---

### 3.2 Scale Independence

Raw signal magnitude must not affect comparability.

Example:

```text
PE = 10
Momentum = 0.35
ROE = 0.22
```

must be transformed into a common scoring framework.

---

### 3.3 Monotonicity

Better raw values must always produce better scores.

Ordering must never change after normalization.

---

### 3.4 Determinism

Identical inputs must produce identical scores.

---

## 4. Inputs

Consumes:

- entry_signal_specification.md
- universe_specification.md

Required inputs:

```text
evaluation_date
security_id
signal_id
raw_signal_value
signal_direction
```

---

## 5. Scoring Workflow

For each:

```text
evaluation_date
signal_id
```

execute:

```text
1. Collect raw values
2. Remove invalid observations
3. Rank securities
4. Normalize ranks
5. Produce factor scores
6. Persist results
```

---

## 6. Signal Direction

Every signal must declare:

```yaml
higher_is_better
```

or

```yaml
lower_is_better
```

Examples:

### Momentum

```yaml
higher_is_better
```

### PE Ratio

```yaml
lower_is_better
```

Direction determines ranking order.

---

## 7. Ranking Methodology

Default ranking method:

```text
Cross-Sectional Percentile Rank
```

Procedure:

```text
Rank all securities
Convert rank to percentile
```

Higher percentile implies stronger factor exposure.

---

## 8. Score Normalization

Default output range:

```text
0.0 → 1.0
```

Formula:

```text
factor_score = percentile_rank
```

Examples:

```text
Best stock:
1.00

Median stock:
0.50

Worst stock:
0.00
```

---

## 9. Tie Handling

If multiple securities have identical raw values:

Use:

```text
Average Rank
```

Example:

```text
Ranks:
5
6
7

Assigned:
6
```

Tie handling must be deterministic.

---

## 10. Missing Data Handling

Supported policies:

### Exclude Security

```yaml
exclude_security
```

Security removed from ranking.

---

### Assign Lowest Score

```yaml
assign_lowest_score
```

Factor score:

```text
0.0
```

---

### Assign Neutral Score

```yaml
assign_neutral_score
```

Factor score:

```text
0.5
```

---

Default:

```yaml
exclude_security
```

---

## 11. Outlier Handling

Default:

```text
No winsorization
```

Raw values are ranked directly.

Optional preprocessing may be added explicitly.

Examples:

```yaml
winsorize:
  lower_pct: 0.01
  upper_pct: 0.99
```

Such preprocessing must be documented and versioned.

---

## 12. Valid Observation Requirements

A factor score may only be generated if:

```text
Raw value exists
Raw value is numeric
Raw value is finite
```

Invalid values:

```text
NaN
Infinity
Null
```

must be handled according to the missing-data policy.

---

## 13. Factor Rank

In addition to normalized scores, persist:

```text
factor_rank
```

Definition:

```text
1 = Best Security
```

Example:

```text
AAPL = Rank 1
MSFT = Rank 2
NVDA = Rank 3
```

Ranks must be deterministic.

---

## 14. Small Sample Handling

Minimum valid observations:

```yaml
minimum_security_count: 30
```

If fewer valid observations exist:

```text
Factor evaluation invalid.
```

Results must be flagged.

---

## 15. Validation Requirements

Verify:

### Input Validation

```text
Valid signal
Valid date
Valid raw value
```

### Ranking Validation

```text
No duplicate security identifiers
Valid ranks
Valid score range
```

### Output Validation

```text
0 <= factor_score <= 1
```

Validation failures must halt execution.

---

## 16. Result Schema

Output schema:

```text
evaluation_date

security_id
ticker

signal_id

raw_signal_value

factor_rank

factor_score
```

---

## 17. Example

Raw Momentum Values:

```text
AAPL = 0.40
MSFT = 0.25
NVDA = 0.10
```

Ranks:

```text
AAPL = 1
MSFT = 2
NVDA = 3
```

Scores:

```text
AAPL = 1.00
MSFT = 0.50
NVDA = 0.00
```

---

## 18. Integration Requirements

Consumes:

- entry_signal_specification.md

Produces:

- factor_combination_specification.md
- result_schema_specification.md

Relationship:

```text
Raw Signal
    →
Rank
    →
Normalized Score
    →
Factor Combination
```

---

## 19. Configuration Parameters

Default configuration:

```yaml
scoring_method: PERCENTILE_RANK

score_range:
  min: 0.0
  max: 1.0

tie_method: AVERAGE_RANK

missing_data_policy: EXCLUDE_SECURITY

minimum_security_count: 30
```

---

## 20. Compliance Requirements

All implementations must guarantee:

- Cross-sectional scoring
- Deterministic ranking
- Scale independence
- Monotonicity preservation
- Explicit missing-data handling
- Reproducibility
- Score normalization

Any implementation violating these requirements is non-compliant.
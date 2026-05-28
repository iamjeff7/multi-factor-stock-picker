# factor_combination_specification.md

## 1. Purpose

Define the official methodology for combining multiple normalized factor scores into a single composite score.

This specification exists between:

```text
Entry Signal
    →
Factor Scoring
    →
Factor Combination
    →
Portfolio Construction
```

The objective is to produce a unified stock ranking from multiple factor exposures.

---

## 2. Scope

This specification defines:

- Factor combination methodology
- Weighting rules
- Composite score generation
- Composite ranking
- Validation requirements
- Result schemas

This specification does not define:

- Entry signal generation
- Raw signal calculation
- Factor scoring
- Portfolio construction

---

## 3. Core Principles

### 3.1 Factor Independence

Each factor contributes independently to the composite score.

Factor combination must not alter individual factor scores.

---

### 3.2 Score Comparability

Only normalized factor scores may be combined.

Raw signals must never be combined directly.

---

### 3.3 Determinism

Identical inputs must produce identical composite scores.

---

### 3.4 Transparency

Composite score calculations must be fully explainable and reproducible.

---

## 4. Inputs

Consumes outputs from:

- factor_scoring_specification.md

Required fields:

```text
evaluation_date
security_id
signal_id
factor_score
```

Expected score range:

```text
0.0 → 1.0
```

---

## 5. Combination Workflow

For each evaluation date:

```text
1. Load factor scores
2. Validate inputs
3. Apply factor weights
4. Calculate composite score
5. Rank securities
6. Persist results
```

---

## 6. Default Combination Method

Default method:

```text
Weighted Arithmetic Mean
```

Formula:

```text
composite_score =
Σ(weight × factor_score)
/
Σ(weights)
```

All enabled factors participate in the calculation.

---

## 7. Equal Weight Combination

Default configuration:

```yaml
weighting_method: EQUAL_WEIGHT
```

Example:

```text
Momentum Score = 0.80
Quality Score = 0.60
Value Score = 0.40
```

Composite:

```text
(0.80 + 0.60 + 0.40) / 3
=
0.60
```

---

## 8. Custom Weight Combination

The framework must support user-defined weights.

Example:

```yaml
Momentum: 0.50
Quality: 0.30
Value: 0.20
```

Weights must be non-negative.

---

## 9. Weight Validation

Requirements:

```text
Weight >= 0
```

Recommended:

```text
Σ(weights) = 1
```

If weights do not sum to one:

```text
Normalize automatically
```

Example:

```text
2
3
5
```

becomes:

```text
0.20
0.30
0.50
```

---

## 10. Missing Factor Handling

Supported policies:

### Exclude Security

```yaml
exclude_security
```

Security removed from composite calculation.

---

### Ignore Missing Factor

```yaml
ignore_missing_factor
```

Composite calculated using available factors.

---

### Assign Neutral Score

```yaml
assign_neutral_score
```

Missing score becomes:

```text
0.50
```

---

Default:

```yaml
ignore_missing_factor
```

---

## 11. Minimum Factor Coverage

A security must have at least:

```yaml
minimum_factor_coverage_pct: 0.50
```

Meaning:

```text
50% of factors available
```

Otherwise:

```text
Composite score invalid
```

---

## 12. Composite Score Range

Composite score must remain within:

```text
0.0 → 1.0
```

No additional normalization is required.

---

## 13. Composite Ranking

After score calculation:

```text
Highest Score → Rank 1
```

Example:

```text
AAPL = 0.82
MSFT = 0.76
NVDA = 0.71
```

Ranks:

```text
AAPL = 1
MSFT = 2
NVDA = 3
```

---

## 14. Tie Handling

If identical composite scores occur:

Use:

```text
Average Rank
```

Tie handling must be deterministic.

---

## 15. Factor Contribution Tracking

Persist factor contributions.

Example:

```json
{
  "momentum": 0.40,
  "quality": 0.25,
  "value": 0.15
}
```

This enables explainability and auditability.

---

## 16. Validation Requirements

### Input Validation

Verify:

```text
Valid factor score
Valid security
Valid date
```

---

### Weight Validation

Verify:

```text
Non-negative weights
Valid factor references
```

---

### Output Validation

Verify:

```text
0 <= composite_score <= 1
```

Validation failures must halt execution.

---

## 17. Result Schema

Output schema:

```text
evaluation_date

security_id
ticker

composite_score

composite_rank
```

Optional:

```text
factor_contributions_json
```

---

## 18. Example

Factors:

```text
Momentum = 0.90
Quality = 0.70
Value = 0.50
```

Equal Weight:

```text
(0.90 + 0.70 + 0.50) / 3
=
0.70
```

Composite:

```text
0.70
```

---

## 19. Configuration Parameters

Default configuration:

```yaml
combination_method: WEIGHTED_MEAN

weighting_method: EQUAL_WEIGHT

missing_factor_policy: IGNORE_MISSING_FACTOR

minimum_factor_coverage_pct: 0.50
```

---

## 20. Integration Requirements

Consumes:

- factor_scoring_specification.md

Produces:

- portfolio_construction_specification.md
- result_schema_specification.md

Relationship:

```text
Factor Scores
    →
Composite Score
    →
Composite Rank
    →
Portfolio Construction
```

---

## 21. Compliance Requirements

All implementations must guarantee:

- Deterministic combination
- Transparent weighting
- Normalized score inputs
- Explicit missing-factor handling
- Reproducibility
- Composite rank generation
- Factor contribution traceability

Any implementation violating these requirements is non-compliant.
# information_coefficient_specification.md

## 1. Purpose

Define the official methodology for measuring the predictive power of entry signals using Information Coefficient (IC).

Information Coefficient measures whether higher factor scores are associated with better future returns.

This specification provides a standardized framework for evaluating signal quality before portfolio construction.

---

## 2. Scope

This specification defines:

- IC calculation methodology
- Forward return construction
- Evaluation horizons
- Aggregation metrics
- Validation requirements
- Result schemas

This specification does not define:

- Entry signal generation
- Factor scoring
- Portfolio construction
- Backtest execution

### References

- backtest_methodology_specification.md (§30 Validation Framework)
- factor_scoring_specification.md
- result_schema_specification.md

---

## 3. Core Principles

### 3.1 Predictive Evaluation

IC measures prediction quality.

The objective is not profitability.

The objective is ranking accuracy.

---

### 3.2 Cross-Sectional Analysis

IC is calculated across securities at a given evaluation date.

It is not calculated through time for a single security.

---

### 3.3 Point-in-Time Correctness

Factor scores must be generated using only information available on the evaluation date.

Forward returns must begin after signal observation.

---

### 3.4 Determinism

Identical inputs must produce identical IC results.

---

## 4. Inputs

Consumes outputs from:

- factor_scoring_specification.md

Required inputs:

```text
evaluation_date
security_id
factor_score
```

Additional required data:

```text
future_returns
```

---

## 5. Forward Return Construction

Forward returns must be calculated after signal generation.

Example:

```text
Signal Date:
2020-01-31

Execution Date:
2020-02-03

Forward Return Window:
2020-02-03 onward
```

Signals must never use overlapping future information.

---

## 6. Supported Horizons

Required horizons:

```text
5 Trading Days
21 Trading Days
63 Trading Days
126 Trading Days
252 Trading Days
```

Equivalent to:

```text
1 Week
1 Month
1 Quarter
6 Months
1 Year
```

Additional horizons may be added.

---

## 7. Return Calculation

Default:

```text
Total Return
```

Formula:

```text
(end_price / start_price) - 1
```

Prices must be adjusted for:

- Splits
- Dividends

---

## 8. Information Coefficient Definition

Default IC metric:

```text
Spearman Rank Correlation
```

Between:

```text
Factor Score
```

and

```text
Forward Return
```

For each evaluation date:

```text
IC = Spearman(
    factor_score,
    future_return
)
```

---

## 9. Why Spearman

Spearman correlation is preferred because:

- Measures ranking ability
- Less sensitive to outliers
- Common industry standard
- Consistent with factor investing workflows

---

## 10. IC Calculation Workflow

For each:

```text
evaluation_date
signal_id
horizon
```

execute:

```text
1. Load factor scores
2. Calculate forward returns
3. Align securities
4. Remove invalid observations
5. Compute Spearman correlation
6. Persist IC result
```

---

## 11. Minimum Sample Size

Required:

```yaml
minimum_security_count: 30
```

If fewer observations exist:

```text
IC result invalid
```

and must be flagged.

---

## 12. Missing Data Handling

Remove observations with:

```text
Missing factor score
Missing return
Invalid return
Invalid score
```

No imputation is allowed.

---

## 13. Daily IC Series

For every evaluation date:

Persist:

```text
evaluation_date
signal_id
horizon
ic
```

This forms the IC time series.

---

## 14. Aggregate IC Metrics

Calculate:

### Mean IC

```text
average(ic)
```

---

### Median IC

```text
median(ic)
```

---

### IC Standard Deviation

```text
std(ic)
```

---

### IC Information Ratio

Formula:

```text
mean_ic
/
std_ic
```

Higher values indicate more stable predictive power.

---

## 15. Hit Rate

Definition:

```text
Percentage of periods where IC > 0
```

Formula:

```text
positive_ic_periods
/
total_periods
```

---

## 16. Statistical Significance

Calculate:

```text
t_statistic
p_value
```

for the IC series.

Used for signal validation.

---

## 17. Interpretation Guidelines

Typical interpretation:

| Mean IC | Interpretation |
|----------|---------------|
| > 0.10 | Exceptional |
| 0.05 - 0.10 | Strong |
| 0.02 - 0.05 | Useful |
| 0.00 - 0.02 | Weak |
| < 0.00 | Adverse |

These thresholds are guidelines only.

---

## 18. Validation Requirements

Verify:

### Input Validation

```text
Valid scores
Valid returns
Valid identifiers
```

### Calculation Validation

```text
Enough observations
Valid correlation result
```

### Output Validation

```text
-1 <= IC <= 1
```

Failures must halt execution.

---

## 19. Daily IC Schema

```text
evaluation_date

signal_id

horizon

security_count

ic
```

---

## 20. IC Summary Schema

```text
signal_id

horizon

sample_period

mean_ic

median_ic

std_ic

ic_information_ratio

hit_rate

t_statistic

p_value

observation_count
```

### Sample Period Values

```text
IS
OOS
FULL
```

IC summaries must be computed separately for IS and OOS using the canonical trading-day split defined in `backtest_methodology_specification.md` §30.

Daily IC observations are assigned to a sample period by `evaluation_date`.

---

## 21. Sample Period IC Analysis

After computing the daily IC series over the full research window, implementations must:

1. Compute the canonical IS/OOS split on trading days
2. Filter daily IC observations by `evaluation_date`
3. Summarize IC statistics independently for `IS` and `OOS`
4. Optionally retain a `FULL` summary for the complete window

Required outputs:

```text
in_sample_summary
out_of_sample_summary
full_summary (optional)
degradation_metrics
```

---

## 22. IC Degradation Schema

Reports IS→OOS predictive degradation for audit and overfitting review.

```text
is_mean_ic
oos_mean_ic
is_to_oos_mean_ic_delta

is_hit_rate
oos_hit_rate
is_to_oos_hit_rate_delta

is_ic_information_ratio
oos_ic_information_ratio

overfitting_warning
```

Large negative deltas in mean IC or hit rate, especially when IS metrics are strongly positive and OOS metrics collapse, indicate potential overfitting.

---

## 23. Example

Factor Scores:

```text
AAPL = 0.90
MSFT = 0.70
NVDA = 0.50
```

Future Returns:

```text
AAPL = 12%
MSFT = 8%
NVDA = 2%
```

Spearman Correlation:

```text
IC = +1.0
```

Perfect rank ordering.

---

## 24. Configuration Parameters

Default configuration:

```yaml
correlation_method: SPEARMAN

minimum_security_count: 30

horizons:
  - 5
  - 21
  - 63
  - 126
  - 252
```

---

## 25. Integration Requirements

Consumes:

- factor_scoring_specification.md
- backtest_methodology_specification.md

Produces:

- factor_performance_specification.md
- entry_robustness_scoring_specification.md
- result_schema_specification.md

Relationship:

```text
Factor Scores
    →
Forward Returns
    →
IC Calculation
    →
IC Statistics
```

---

## 26. Compliance Requirements

All implementations must guarantee:

- Spearman rank correlation
- Cross-sectional evaluation
- Point-in-time correctness
- Forward-return integrity
- Deterministic execution
- Reproducibility
- Explicit sample-size validation
- Separate IS and OOS IC reporting
- Canonical sample split alignment with backtest methodology

Any implementation violating these requirements is non-compliant.
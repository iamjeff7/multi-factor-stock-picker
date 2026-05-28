# factor_performance_specification.md

## 1. Purpose

Define the official methodology for evaluating the investment performance of individual entry signals and factor models.

While Information Coefficient evaluates predictive ranking ability, this specification evaluates economic value and investability.

The objective is to determine whether a factor can generate meaningful return premiums after realistic implementation.

---

## 2. Scope

This specification defines:

- Factor portfolio construction
- Quantile analysis
- Long-short analysis
- Return calculations
- Performance metrics
- Factor performance reporting

This specification does not define:

- Entry signal generation
- Factor scoring
- Multi-factor combination
- Production portfolio construction

---

## 3. Core Principles

### 3.1 Isolated Factor Evaluation

Each factor must be evaluated independently.

The purpose is to measure the contribution of a single factor.

---

### 3.2 Cross-Sectional Ranking

Performance is measured from factor rankings generated on each evaluation date.

---

### 3.3 Point-in-Time Correctness

Factor scores must be generated using only information available on the evaluation date.

Future returns must occur strictly after score generation.

---

### 3.4 Determinism

Identical inputs must produce identical results.

---

## 4. Inputs

Consumes:

- factor_scoring_specification.md
- backtest_methodology_specification.md

Required fields:

```text
evaluation_date
security_id
factor_score
factor_rank
```

---

## 5. Evaluation Methodology

For each evaluation date:

```text
1. Rank securities
2. Divide into quantiles
3. Form factor portfolios
4. Measure forward returns
5. Aggregate results
6. Generate statistics
```

---

## 6. Quantile Construction

Default:

```yaml
quantile_count: 10
```

Meaning:

```text
Decile 1 = Lowest Scores
Decile 10 = Highest Scores
```

Each quantile should contain approximately equal numbers of securities.

---

## 7. Portfolio Formation

Within each quantile:

```text
Equal Weight Portfolio
```

Default:

```yaml
portfolio_weighting: EQUAL_WEIGHT
```

Alternative weighting methods may be added later.

---

## 8. Holding Periods

Required evaluation horizons:

```text
5 Trading Days
21 Trading Days
63 Trading Days
126 Trading Days
252 Trading Days
```

Equivalent:

```text
1 Week
1 Month
1 Quarter
6 Months
1 Year
```

---

## 9. Quantile Return Calculation

For each quantile:

```text
Calculate average forward return
```

Result:

```text
Q1 Return
Q2 Return
...
Q10 Return
```

---

## 10. Monotonicity Analysis

Determine whether returns improve consistently across quantiles.

Desired behavior:

```text
Q1 < Q2 < Q3 < ... < Q10
```

Perfect monotonicity is not required.

Stronger monotonicity indicates stronger factor quality.

---

## 11. Top vs Bottom Spread

Calculate:

```text
Top Quantile Return
-
Bottom Quantile Return
```

Example:

```text
Q10 = +12%

Q1 = +2%

Spread = +10%
```

This is one of the primary factor performance metrics.

---

## 12. Long-Short Portfolio

Construct:

```text
Long Top Quantile
Short Bottom Quantile
```

Default:

```text
Long Q10
Short Q1
```

Calculate:

```text
LongShort Return
=
Long Return
-
Short Return
```

---

## 13. Long-Only Portfolio

Construct:

```text
Long Top Quantile
```

Default:

```text
Long Q10
```

This measures practical implementation performance.

---

## 14. Portfolio Rebalancing

Default:

```yaml
rebalance_frequency: MONTHLY
```

Supported:

```text
Daily
Weekly
Monthly
Quarterly
```

---

## 15. Performance Metrics

Required metrics:

### Return Metrics

```text
Total Return
Annualized Return
CAGR
```

### Risk Metrics

```text
Volatility
Maximum Drawdown
```

### Risk-Adjusted Metrics

```text
Sharpe Ratio
Sortino Ratio
Calmar Ratio
```

### Trading Metrics

```text
Turnover
Holding Period
```

---

## 16. Factor Stability

Measure:

```text
Performance by Year
Performance by Regime
Performance by Market Condition
```

The objective is to evaluate consistency.

---

## 17. Rolling Performance Analysis

Calculate rolling metrics.

Examples:

```text
Rolling 1 Year Return
Rolling 3 Year Return
Rolling Sharpe Ratio
```

Used for robustness evaluation.

---

## 18. Validation Requirements

Verify:

### Portfolio Validation

```text
Valid weights
Valid memberships
Valid returns
```

### Quantile Validation

```text
No missing quantiles
Reasonable group sizes
```

### Return Validation

```text
Valid forward returns
```

Failures must halt execution.

---

## 19. Quantile Result Schema

```text
evaluation_date

signal_id

quantile

security_count

average_return
```

---

## 20. Spread Result Schema

```text
evaluation_date

signal_id

top_quantile

bottom_quantile

spread_return
```

---

## 21. Long-Short Result Schema

```text
evaluation_date

signal_id

long_return

short_return

long_short_return
```

---

## 22. Performance Summary Schema

```text
signal_id

total_return

annualized_return

cagr

volatility

sharpe_ratio

sortino_ratio

calmar_ratio

max_drawdown

turnover
```

---

## 23. Monotonicity Metrics

Calculate:

### Rank Correlation

Correlation between:

```text
Quantile Number
Quantile Return
```

Higher values indicate stronger monotonicity.

---

### Quantile Win Rate

Percentage of periods where:

```text
Top Quantile
>
Bottom Quantile
```

---

## 24. Example

Returns:

```text
Q1 = 1%
Q2 = 2%
Q3 = 3%
...
Q10 = 10%
```

Spread:

```text
10% - 1%
=
9%
```

Long-Short:

```text
+9%
```

Strong factor performance.

---

## 25. Configuration Parameters

Default configuration:

```yaml
quantile_count: 10

top_quantile: 10

bottom_quantile: 1

portfolio_weighting: EQUAL_WEIGHT

rebalance_frequency: MONTHLY

holding_periods:
  - 5
  - 21
  - 63
  - 126
  - 252
```

---

## 26. Integration Requirements

Consumes:

- factor_scoring_specification.md
- information_coefficient_specification.md
- backtest_methodology_specification.md

Produces:

- entry_robustness_scoring_specification.md
- result_schema_specification.md

Relationship:

```text
Factor Scores
    →
Quantile Portfolios
    →
Forward Returns
    →
Performance Metrics (reported separately for IS and OOS)
```

Performance metrics must be reported separately for IS and OOS periods using the canonical split defined in `backtest_methodology_specification.md` §30.

---

## 27. Compliance Requirements

All implementations must guarantee:

- Point-in-time correctness
- Deterministic portfolio formation
- Equal-weight quantile construction
- Explicit holding periods
- Reproducibility
- Long-short evaluation
- Monotonicity analysis
- Separate IS and OOS performance reporting

Any implementation violating these requirements is non-compliant.
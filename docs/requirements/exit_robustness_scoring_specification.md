# exit_robustness_scoring_specification.md

## Purpose

Define a standardized robustness scoring framework used to evaluate the stability, consistency, and reliability of exit signals across multiple validation dimensions.

The robustness score is intended to identify exit signals that are more likely to remain effective out-of-sample and reduce the risk of selecting exits that perform well due to noise, overfitting, or favorable historical conditions.

---

## Scope

This specification applies only to exit signal robustness evaluation.

It does not define:

- Exit signal construction
- Portfolio construction
- Position sizing
- Risk management
- Capital allocation

---

## References

- exit_signal_specification.md
- backtest_methodology_specification.md
- exit_performance_specification.md

---

# Objectives

The robustness framework must:

1. Reward consistency through time.
2. Reward consistency across market environments.
3. Reward consistency across parameter variations.
4. Penalize unstable behavior.
5. Penalize excessive dependence on isolated periods.
6. Produce a single robustness score for ranking exit signals.

---

# Robustness Evaluation Framework

Each exit signal shall be evaluated across multiple dimensions.

Recommended dimensions:

| Dimension | Description |
|------------|------------|
| Performance Stability | Consistency of exit performance |
| Regime Stability | Performance across market regimes |
| Parameter Stability | Sensitivity to parameter changes |
| Holding Period Stability | Consistency across holding durations |
| Sample Stability | Consistency across historical periods |
| Trade Distribution Stability | Consistency across trade populations |
| Risk Stability | Consistency of risk characteristics |

Each dimension produces an independent score.

---

# Performance Stability

Evaluate consistency of overall exit effectiveness.

Metrics:

- Average trade return
- Median trade return
- Win rate
- Profit factor
- Expectancy
- Return volatility

Robust exits should generate stable results across time.

Large swings in performance reduce robustness.

---

# Regime Stability

Evaluate performance across different market environments.

Example regimes:

- Bull market
- Bear market
- Sideways market
- High volatility
- Low volatility

Metrics:

- Average trade return
- Win rate
- Profit factor
- Expectancy

Exit signals that perform reasonably across multiple regimes receive higher scores.

---

# Parameter Stability

Evaluate nearby parameter variations.

Examples:

- Holding period variations
- Stop-loss variations
- Take-profit variations
- Exit threshold variations

Metrics:

- Average neighboring performance
- Performance dispersion
- Sensitivity ratio

Small parameter changes should not cause major performance deterioration.

---

# Holding Period Stability

Evaluate effectiveness across different trade durations.

Example buckets:

- 1–5 days
- 6–20 days
- 21–60 days
- 60+ days

Metrics:

- Average return
- Win rate
- Profit factor

Signals that work only within a narrow duration range receive lower robustness scores.

---

# Sample Stability

Evaluate consistency between in-sample and out-of-sample periods using the canonical split defined in `backtest_methodology_specification.md` §30.

Required periods:

- In-Sample (IS)
- Out-of-Sample (OOS)

The split is computed on trading days within the research window:

- IS = oldest 80%
- OOS = most recent 20%

Metrics per period:

- Return consistency
- Win-rate consistency
- Profit-factor consistency

Sample stability compares IS and OOS trade metrics directly.

Closed trades are assigned to a period by `exit_date`.

Large performance variation between IS and OOS reduces robustness and may indicate overfitting.

Implementations must derive period metrics from the canonical split rather than ad hoc early/middle/recent partitions.

---

# Trade Distribution Stability

Evaluate whether results are broadly distributed across trades.

Metrics:

- Percentage of profitable trades
- Contribution concentration
- Top-trade contribution ratio
- Largest winner contribution

Exit signals should not depend on a small number of exceptional trades.

High return concentration reduces robustness.

---

# Risk Stability

Evaluate consistency of risk characteristics.

Metrics:

- Maximum drawdown
- Trade loss distribution
- Volatility
- Tail risk measures

Stable risk behavior improves robustness.

Large fluctuations in risk characteristics reduce robustness.

---

# Robustness Normalization

Each robustness dimension shall be normalized onto a common scale.

Recommended range:

```text
0.0 = very weak robustness
1.0 = very strong robustness
```

Normalization methods must be deterministic and reproducible.

---

# Robustness Component Weights

Recommended default weights:

| Component | Weight |
|------------|---------|
| Trade Distribution Stability | 10% |
| Holding Period Stability | 10% |
| Walk-Forward Stability | 20% |
| Out-of-Sample Retention | 20% |
| Market Regime Consistency | 15% |
| Parameter Sensitivity | 10% |
| Profit Capture Consistency | 10% |
| Data Perturbation Resilience | 5% |

Weights must be configurable.

Total weight must equal 100%.

---

# Migration / Removed Dimensions

The following dimensions were removed from the default exit robustness model:

| Removed Component | Former Weight | Notes |
|-------------------|---------------|-------|
| Performance Stability | 25% | Absorbed into walk-forward stability |
| Risk Stability | 10% | No slot in finalized model |

`Sample Stability` is renamed to `Out-of-Sample Retention` with an increased default weight (10% → 20%).

---

# Final Robustness Score

Final score:

```text
Robustness Score
=
Weighted Sum of All Component Scores
```

Output range:

```text
0.0 – 1.0
```

Higher values indicate greater confidence that the exit signal is genuinely effective and less likely to be overfit.

---

# Robustness Classification

Recommended categories:

| Score Range | Classification |
|-------------|---------------|
| 0.90 - 1.00 | Exceptional |
| 0.80 - 0.90 | Strong |
| 0.70 - 0.80 | Good |
| 0.60 - 0.70 | Acceptable |
| 0.50 - 0.60 | Weak |
| < 0.50 | Reject |

Thresholds must be configurable.

---

# Ranking Usage

Robustness score may be used to:

- Compare exit signals
- Compare parameter sets
- Filter weak exits
- Prioritize research candidates

Robustness score shall not directly affect trade execution logic.

---

# Validation Requirements

Implementation must verify:

- No missing robustness components
- Valid normalization range
- Weight totals equal 100%
- Deterministic score generation
- Reproducible results

Any validation failure must generate an explicit error.

---

# Required Outputs

For every evaluated exit signal:

```text
exit_signal_id

trade_distribution_stability_score
holding_period_stability_score
walk_forward_stability_score
out_of_sample_retention_score
market_regime_consistency_score
parameter_sensitivity_score
profit_capture_consistency_score
data_perturbation_resilience_score

overall_robustness_score
robustness_classification
pending_dimensions
```

Legacy aliases (`performance_stability_score`, `regime_stability_score`, `parameter_stability_score`, `sample_stability_score`, `risk_stability_score`) may appear in transitional payloads.

These outputs shall be persisted for downstream research and exit signal comparison.
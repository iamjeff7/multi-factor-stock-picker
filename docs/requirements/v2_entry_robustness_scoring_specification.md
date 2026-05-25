# v2_entry_robustness_scoring_specification.md

## Purpose

Define a standardized robustness scoring framework used to evaluate the stability, consistency, and reliability of entry signals across multiple validation dimensions.

The robustness score is intended to identify signals that are more likely to remain effective out-of-sample and reduce the risk of selecting signals that perform well due to noise, overfitting, or favorable sample periods.

---

## Scope

This specification applies only to entry signal robustness evaluation.

It does not define:

- Factor construction
- Factor scoring
- Factor combination
- Portfolio construction
- Risk management

---

## References

- v2_entry_signal_specification.md
- v2_factor_scoring_specification.md
- v2_factor_combination_specification.md
- v2_information_coefficient_specification.md
- v2_factor_performance_specification.md
- v2_backtest_methodology_specification.md

---

# Objectives

The robustness framework must:

1. Reward consistency across time.
2. Reward consistency across market environments.
3. Reward consistency across parameter variations.
4. Penalize unstable performance.
5. Penalize excessive concentration of returns.
6. Produce a single robustness score for ranking signals.

---

# Robustness Evaluation Framework

Each signal shall be evaluated across multiple dimensions.

Recommended dimensions:

| Dimension | Description |
|------------|------------|
| IC Stability | Consistency of IC through time |
| Return Stability | Consistency of forward returns |
| Regime Stability | Performance across market regimes |
| Parameter Stability | Sensitivity to parameter changes |
| Rank Stability | Stability of stock rankings |
| Breadth Stability | Consistency across universe sizes |
| Sample Stability | Consistency across time periods |

Each dimension produces an independent score.

---

# IC Stability

Evaluate monthly IC consistency.

Metrics:

- Mean IC
- Median IC
- IC standard deviation
- IC hit rate
- IC information ratio

Higher robustness:

- Positive mean IC
- Positive median IC
- High hit rate
- Low volatility of IC

---

# Return Stability

Evaluate consistency of portfolio returns.

Metrics:

- Mean forward return
- Median forward return
- Return standard deviation
- Positive-period ratio

Signals should not rely on a small number of exceptional periods.

---

# Regime Stability

Evaluate performance under different market conditions.

Example regimes:

- Bull market
- Bear market
- Sideways market
- High volatility
- Low volatility

For each regime:

- Mean IC
- Mean forward return
- Hit rate

Signals performing reasonably across most regimes receive higher scores.

---

# Parameter Stability

Evaluate nearby parameter variations.

Examples:

- Lookback period ±20%
- Rebalance frequency variations
- Ranking bucket variations

A robust signal should retain effectiveness under small parameter changes.

Metrics:

- Average neighboring performance
- Performance dispersion
- Sensitivity ratio

Large performance degradation results in lower robustness.

---

# Rank Stability

Evaluate ranking consistency through time.

Metrics:

- Rank correlation between consecutive rebalance dates
- Top-decile membership persistence
- Turnover rate

Excessive ranking instability reduces robustness.

---

# Breadth Stability

Evaluate robustness across universe breadths.

Examples:

- Top 500 stocks
- Top 1000 stocks
- Top 2000 stocks
- Full universe

Signals that work only in a narrow universe receive lower scores.

---

# Sample Stability

Evaluate consistency between in-sample and out-of-sample periods using the canonical split defined in `v2_backtest_methodology_specification.md` §30.

Required periods:

- In-Sample (IS)
- Out-of-Sample (OOS)

The split is computed on trading days within the research window:

- IS = oldest 80%
- OOS = most recent 20%

Metrics per period:

- IC consistency
- Return consistency
- Hit-rate consistency

Sample stability compares IS and OOS metrics directly.

Large differences between IS and OOS indicate instability and potential overfitting.

Implementations must derive period metrics from the canonical split rather than ad hoc early/middle/recent partitions.

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
| IC Stability | 25% |
| Return Stability | 20% |
| Regime Stability | 15% |
| Parameter Stability | 15% |
| Rank Stability | 10% |
| Breadth Stability | 10% |
| Sample Stability | 5% |

Weights must be configurable.

Total weight must equal 100%.

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

Higher values indicate greater confidence that the signal is genuinely predictive and less likely to be overfit.

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

- Compare entry signals
- Compare factor combinations
- Filter weak signals
- Prioritize research candidates

Robustness score shall not directly affect stock ranking calculations.

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

For every evaluated signal:

```text
signal_id

ic_stability_score
return_stability_score
regime_stability_score
parameter_stability_score
rank_stability_score
breadth_stability_score
sample_stability_score

overall_robustness_score
robustness_classification
```

These outputs shall be persisted for downstream research and signal comparison.
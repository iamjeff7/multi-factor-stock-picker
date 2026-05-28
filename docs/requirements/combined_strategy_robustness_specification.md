# combined_strategy_robustness_specification.md

## 1. Purpose

Define the robustness scoring framework for combined entry+exit strategy experiments.

---

## 2. References

- experiment_scoring_specification.md
- backtest_methodology_specification.md
- entry_robustness_scoring_specification.md
- exit_robustness_scoring_specification.md

---

## 3. Objective

Measure whether a full strategy remains effective across time, samples, regimes, parameters, universes, and transaction-cost assumptions.

---

## 4. Component Weights

| Component | Weight | Status |
|-----------|--------|--------|
| `walk_forward_stability` | 20% | Pending initial implementation |
| `out_of_sample_retention` | 20% | Pending initial implementation |
| `market_regime_consistency` | 15% | Pending initial implementation |
| `parameter_sensitivity` | 10% | Pending initial implementation |
| `universe_stability` | 10% | Pending initial implementation |
| `transaction_cost_resilience` | 10% | Pending initial implementation |
| `factor_decay_resistance` | 10% | Pending initial implementation |
| `data_perturbation_resilience` | 5% | Pending initial implementation |

Total weight must equal 100%. Weights must be configurable.

When components are pending, implementations renormalize over active components only.

---

## 5. Final Robustness Score

```text
robustness_score = weighted_sum(component_scores)
```

Output range: `[0, 1]`. Higher is better.

Classification bands follow the shared thresholds in entry/exit robustness specifications.

---

## 6. Required Outputs

```text
walk_forward_stability_score
out_of_sample_retention_score
market_regime_consistency_score
parameter_sensitivity_score
universe_stability_score
transaction_cost_resilience_score
factor_decay_resistance_score
data_perturbation_resilience_score
overall_robustness_score
robustness_classification
pending_dimensions
```

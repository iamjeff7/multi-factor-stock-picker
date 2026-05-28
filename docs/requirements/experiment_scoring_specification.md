# experiment_scoring_specification.md

## 1. Purpose

Define weighted composite scores used to rank entry factors, exit factors, and combined entry+exit strategies during unified experiments.

Calculation methodologies for individual metrics live in referenced specifications. This document defines experiment-level metric sets, weights, normalization, and composite score formulas.

---

## 2. References

- information_coefficient_specification.md
- factor_performance_specification.md
- entry_robustness_scoring_specification.md
- exit_robustness_scoring_specification.md
- combined_strategy_robustness_specification.md
- backtest_methodology_specification.md
- result_schema_specification.md

---

## 3. Shared Conventions

All experiment composite scores use the same normalization and aggregation rules.

### Normalization

- Method: min-max scaling within the peer set (percentile rank for entry/exit segment peers; cross-variant min-max for combined runs)
- Output range: `[0, 1]`
- Direction: higher is better (invert metrics where lower is better before normalization)

### Composite score

```text
final_score = Σ(normalized_metric_score × metric_weight)
```

Weights must sum to `1.0` for each experiment type.

---

## 4. Entry Factor Testing

### Summary

Tests whether an entry factor consistently identifies stocks that outperform after the signal date.

### Metrics

| Metric | Weight | Description | Formula |
|--------|--------|-------------|---------|
| `forward_return` | 0.40 | Average future return after signal generation | `mean((future_price - entry_price) / entry_price)` |
| `information_coefficient` | 0.20 | Rank correlation between factor scores and future returns | `spearman_corr(factor_rank, future_return_rank)` |
| `hit_rate` | 0.15 | Share of observations with positive forward returns | `winning_observations / total_observations` |
| `sharpe_ratio` | 0.10 | Risk-adjusted return of simulated entry trades | `mean(trade_returns) / std(trade_returns)` |
| `maximum_drawdown` | 0.05 | Largest peak-to-trough decline (lower is better) | `min((equity - rolling_peak) / rolling_peak)` |
| `turnover_efficiency` | 0.05 | Return per unit of turnover | `total_return / turnover_rate` |
| `robustness_score` | 0.05 | Entry robustness composite | See entry_robustness_scoring_specification.md |

### Output

- Field: `final_factor_score`
- Range: `[0, 1]`
- Higher is better

---

## 5. Exit Factor Testing

### Summary

Tests whether an exit factor improves realized trade outcomes relative to a baseline exit under the same synthetic entry protocol.

### Baseline exit

Default baseline: fixed-period exit using the configured reference holding period (`baseline_holding_months`, default 3) under the same entry schedule as the exit experiment.

Comparative metrics (`trade_return_improvement`, `maximum_drawdown_reduction`, `sharpe_ratio_improvement`) are computed as exit-factor value minus baseline value.

### Metrics

| Metric | Weight | Description | Formula |
|--------|--------|-------------|---------|
| `trade_return_improvement` | 0.35 | Mean return uplift vs baseline | `mean(exit_return - baseline_return)` |
| `profit_capture_ratio` | 0.20 | Share of maximum achievable profit captured | `realized_profit / maximum_possible_profit` |
| `maximum_drawdown_reduction` | 0.15 | Drawdown improvement vs baseline | `baseline_drawdown - exit_drawdown` |
| `win_rate` | 0.10 | Share of profitable closed trades | `winning_trades / total_trades` |
| `average_holding_period_efficiency` | 0.10 | Return per holding day | `mean(trade_return / holding_days)` |
| `sharpe_ratio_improvement` | 0.05 | Sharpe uplift vs baseline | `exit_sharpe - baseline_sharpe` |
| `robustness_score` | 0.05 | Exit robustness composite | See exit_robustness_scoring_specification.md |

### Output

- Field: `final_factor_score`
- Range: `[0, 1]`
- Higher is better

---

## 6. Combined Strategy Testing

### Summary

Tests the full trading strategy by evaluating entry and exit factors together under realistic portfolio conditions.

### Metrics

| Metric | Weight | Description | Formula |
|--------|--------|-------------|---------|
| `cagr` | 0.20 | Annualized compounded return | `(ending_equity / starting_equity)^(1 / years) - 1` |
| `sharpe_ratio` | 0.15 | Risk-adjusted return | `mean(excess_returns) / std(returns)` |
| `sortino_ratio` | 0.10 | Downside risk-adjusted return | `mean(excess_returns) / downside_std(returns)` |
| `maximum_drawdown` | 0.10 | Largest peak-to-trough equity decline (lower is better) | `min((equity - peak) / peak)` |
| `calmar_ratio` | 0.10 | CAGR relative to max drawdown | `cagr / abs(maximum_drawdown)` |
| `profit_factor` | 0.08 | Gross profit / gross loss | `gross_profit / gross_loss` |
| `expectancy` | 0.07 | Expected profit per trade | `(win_rate × avg_win) - ((1 - win_rate) × avg_loss)` |
| `turnover_efficiency` | 0.05 | Return per unit of turnover | `total_return / turnover_rate` |
| `alpha` | 0.05 | Excess return vs CAPM benchmark | `strategy_return - (rf + beta × (market - rf))` |
| `beta` | 0.03 | Market sensitivity | `cov(strategy, market) / var(market)` |
| `tail_ratio` | 0.03 | Upside vs downside tail | `percentile(returns, 95) / abs(percentile(returns, 5))` |
| `robustness_score` | 0.04 | Combined strategy robustness | See combined_strategy_robustness_specification.md |

### Output

- Field: `final_strategy_score`
- Range: `[0, 1]`
- Higher is better

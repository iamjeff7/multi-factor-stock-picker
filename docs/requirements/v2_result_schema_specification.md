# result_schema_specification.md

## 1. Purpose

Define the official result schemas produced by the research framework.

This specification ensures that all experiments generate outputs that are:

- Consistent
- Reproducible
- Auditable
- Machine-readable
- Comparable across experiments

All modules must persist results according to this specification.

---

## 2. Scope

This specification defines schemas for:

- Experiment metadata
- Entry signal results
- Exit signal results
- Factor scores
- Composite scores
- Portfolio selections
- Trades
- Portfolio snapshots
- Backtest summaries
- Experiment summaries
- Robustness scores

This specification defines storage structure only.

It does not define calculation methodologies.

---

## 3. Core Principles

### 3.1 Immutable Results

Persisted results must never be modified.

Corrections require creation of a new experiment.

---

### 3.2 Reproducibility

Every result must contain sufficient metadata to reproduce the experiment.

---

### 3.3 Traceability

Every output must be traceable back to:

- Data version
- Universe version
- Signal version
- Configuration

---

### 3.4 Machine Readability

All schemas must be deterministic and suitable for automated processing.

---

## 4. Experiment Metadata Schema

One record per experiment.

### Schema

```text
experiment_id
experiment_name
experiment_type
execution_timestamp

data_version
universe_version

configuration_hash

framework_version

status
```

### Example

```text
exp_001
Momentum Test
SINGLE_FACTOR
2026-01-01T00:00:00Z

data_001
universe_001

abc123

v2.0

COMPLETED
```

---

## 5. Entry Signal Result Schema

Stores raw signal outputs.

### Schema

```text
experiment_id
evaluation_date

security_id
ticker

signal_id
signal_version

raw_signal_value
```

### Primary Key

```text
(
    experiment_id,
    evaluation_date,
    security_id,
    signal_id
)
```

---

## 6. Exit Signal Result Schema

Stores exit evaluations.

### Schema

```text
experiment_id
evaluation_date

position_id

security_id
ticker

signal_id
signal_version

decision
trigger_reason
```

### Allowed Decision Values

```text
EXIT
HOLD
```

---

## 7. Factor Score Schema

Stores normalized factor scores.

### Schema

```text
experiment_id
evaluation_date

security_id
ticker

signal_id

factor_score
factor_rank
```

### Score Range

Defined by:

- factor_scoring_specification.md

---

## 8. Composite Score Schema

Stores multi-factor outputs.

### Schema

```text
experiment_id
evaluation_date

security_id
ticker

composite_score
composite_rank
```

Used by portfolio construction.

---

## 9. Portfolio Selection Schema

Stores selected securities at each rebalance.

### Schema

```text
experiment_id
rebalance_date

security_id
ticker

portfolio_rank

target_weight
target_shares
```

---

## 10. Trade Schema

Stores executed trades.

### Schema

```text
experiment_id

trade_id

security_id
ticker

entry_date
entry_price

exit_date
exit_price

shares

gross_pnl
net_pnl

holding_days
```

### Derived Fields

```text
return_pct
```

may also be stored.

---

## 11. Position Schema

Stores active position history.

### Schema

```text
experiment_id

position_id

security_id
ticker

entry_date
entry_price

shares

current_value

status
```

### Status Values

```text
OPEN
CLOSED
```

---

## 12. Portfolio Snapshot Schema

Stores portfolio state over time.

### Schema

```text
experiment_id

date

cash

invested_capital

equity

portfolio_value

drawdown

number_of_positions
```

One record per evaluation date.

---

## 13. Equity Curve Schema

Stores portfolio performance series.

### Schema

```text
experiment_id

date

portfolio_value

daily_return

cumulative_return
```

---

## 14. Backtest Summary Schema

One or more records per completed backtest, keyed by sample period.

### Schema

```text
experiment_id

sample_period

total_return

annualized_return

cagr

volatility

sharpe_ratio

sortino_ratio

calmar_ratio

max_drawdown

win_rate

profit_factor

average_trade

number_of_trades

turnover
```

### Sample Period Values

```text
IS
OOS
FULL
```

### Reporting Rules

- `FULL` summarizes the entire configured research window
- `IS` and `OOS` summarize metrics computed from observations assigned by the canonical split defined in `v2_backtest_methodology_specification.md` §30
- Implementations must persist at minimum one `FULL`, one `IS`, and one `OOS` summary for cross-sectional experiments

---

## 15. Experiment Summary Schema

Aggregated cross-security experiment metrics, keyed by sample period.

### Schema

```text
experiment_id

sample_period

securities_requested

securities_completed

securities_skipped

mean_stock_return

median_stock_return

pct_stocks_positive

best_stock_return

worst_stock_return

number_of_trades

win_rate

profit_factor

average_trade

total_net_pnl
```

Multiple records per experiment are permitted when reporting IS, OOS, and FULL metrics separately.

---

## 16. Robustness Score Schema

Stores robustness evaluation outputs.

### Schema

```text
experiment_id

robustness_score

stability_score

consistency_score

sample_size_score

overall_grade
```

### Grade Values

```text
A
B
C
D
F
```

Definitions are provided in:

- entry_robustness_scoring_specification.md

---

## 17. Configuration Snapshot Schema

Stores complete experiment configuration.

### Schema

```text
experiment_id

configuration_hash

configuration_json
```

Configuration must be persisted exactly as executed.

The persisted `configuration_json` must include research validation settings and computed sample-split metadata:

```text
research:
  research_mode
  research_phase
  sample_scope
  is_fraction
  calendar_start

sample_split:
  method
  basis
  is_fraction
  calendar_start
  calendar_end
  split_date
  is_trading_days
  oos_trading_days
  total_trading_days
```

---

## 18. Version Metadata Schema

Stores implementation versions used during execution.

### Schema

```text
experiment_id

framework_version

data_version

universe_version

entry_signal_versions

exit_signal_versions

backtest_version
```

---

## 19. File Organization

Recommended structure:

```text
results/

    experiment_id/

        metadata/

        signals/

        factors/

        portfolios/

        trades/

        positions/

        snapshots/

        summaries/

        robustness/
```

Implementations may use alternative storage systems if schema compatibility is maintained.

---

## 20. Serialization Requirements

Supported formats:

```text
Parquet
CSV
Database Tables
```

Preferred format:

```text
Parquet
```

All schemas must preserve:

- Numeric precision
- Datetime precision
- Primary key uniqueness

---

## 21. Validation Requirements

Before persistence:

### Schema Validation

Verify:

- Required fields exist
- Data types are correct
- Null constraints are satisfied

### Referential Validation

Verify:

- Experiment exists
- Security identifiers are valid
- Signal identifiers are valid

### Consistency Validation

Verify:

- No duplicate primary keys
- No impossible values
- No invalid dates

Validation failures must halt persistence.

---

## 22. Experiment Audit Requirements

Every experiment must be fully reconstructable.

Required audit information:

```text
experiment_id

execution_timestamp

data_version

universe_version

configuration_hash

framework_version
```

No result may exist without audit metadata.

Experiment reports should include, when sample-split analysis is enabled:

```text
sample_split
sample_metrics
is_to_oos_degradation
```

---

## 23. Integration Requirements

Consumes outputs from:

- entry_signal_specification.md
- exit_signal_specification.md
- factor_scoring_specification.md
- factor_combination_specification.md
- portfolio_construction_specification.md
- backtest_methodology_specification.md

Acts as the persistence layer for the entire research framework.

---

## 24. Compliance Requirements

All implementations must guarantee:

- Immutable results
- Deterministic schemas
- Auditability
- Reproducibility
- Version traceability
- Schema validation
- Referential integrity

Any implementation violating these requirements is non-compliant.
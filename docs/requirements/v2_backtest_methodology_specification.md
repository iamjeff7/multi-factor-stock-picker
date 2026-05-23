# backtest_methodology_specification.md

## 1. Purpose

Define the official backtesting methodology used throughout the research framework.

The objective is to ensure all research results are:

- Realistic
- Reproducible
- Comparable
- Free from look-ahead bias
- Free from survivorship bias

Every experiment must use this methodology unless explicitly documented otherwise.

---

## 2. Scope

This specification defines:

- Backtest assumptions
- Trade simulation rules
- Entry execution
- Exit execution
- Capital allocation
- Position sizing
- Portfolio accounting
- Performance calculation

This specification does not define:

- Entry signal generation
- Exit signal design
- Factor scoring
- Factor combination

---

## 3. Core Principles

### 3.1 Point-in-Time Correctness

Only information available at the decision date may be used.

Future information must never be visible.

---

### 3.2 Determinism

Given identical:

- Data version
- Universe version
- Configuration

Results must be identical.

---

### 3.3 Realistic Execution

Orders must execute using realistic assumptions.

Perfect fills are prohibited.

---

### 3.4 Reproducibility

All experiments must be fully reproducible.

---

## 4. Backtest Types

The framework must support:

### Single-Factor Backtest

Evaluate one entry signal independently.

### Multi-Factor Backtest

Evaluate combined factor models.

### Exit Signal Backtest

Evaluate exit methodologies.

### Full Strategy Backtest

Evaluate complete strategy behavior.

---

## 5. Evaluation Timeline

For each rebalance date:

1. Build universe.
2. Compute entry signals.
3. Generate factor scores.
4. Rank securities.
5. Generate portfolio.
6. Execute trades.
7. Evaluate exits.
8. Update portfolio state.

All steps must occur in sequence.

---

## 6. Signal Observation Rule

Signals generated on date:

```text
T
```

may only use information available on:

```text
T
```

---

## 7. Trade Execution Rule

To avoid look-ahead bias:

Signals observed on:

```text
T
```

must execute on:

```text
T + 1
```

Default execution price:

```text
next_open
```

Supported alternatives:

```text
next_close
next_vwap
```

Execution model must be configurable.

---

## 8. Portfolio Modes

Supported modes:

### Single Position Mode

One active position.

### Top-N Portfolio

Hold highest-ranked securities.

### Equal Weight Portfolio

Equal allocation across selected positions.

### Custom Portfolio

User-defined allocation logic.

---

## 9. Position Sizing

The framework must support:

### Fixed Dollar

```yaml
position_size_method: FIXED_DOLLAR
```

### Equal Weight

```yaml
position_size_method: EQUAL_WEIGHT
```

### Risk-Based

```yaml
position_size_method: RISK_BASED
```

### Volatility-Based

```yaml
position_size_method: VOLATILITY_BASED
```

Additional methods may be added.

---

## 10. Capital Management

Each backtest must define:

```yaml
initial_capital
```

Example:

```yaml
initial_capital: 100000
```

Capital must be tracked continuously.

---

## 11. Entry Logic

Entry decisions originate from:

- Entry signals
- Factor rankings
- Portfolio construction

The backtest engine executes decisions but does not generate them.

---

## 12. Exit Logic

Exit decisions originate from:

- Exit signals
- Portfolio rules

The backtest engine executes exit decisions but does not create them.

---

## 13. Transaction Costs

The framework must support:

### Commission

```yaml
commission_per_trade
```

### Percentage Fee

```yaml
commission_pct
```

### Slippage

```yaml
slippage_pct
```

All costs must be configurable.

---

## 14. Slippage Model

Default:

```yaml
slippage_pct: 0.001
```

Meaning:

```text
0.10%
```

Applied to:

- Entries
- Exits

---

## 15. Corporate Actions

Backtests must correctly account for:

- Stock splits
- Reverse splits
- Cash dividends
- Special dividends

Historical portfolio value must remain accurate after corporate actions.

---

## 16. Delisting Handling

If a security delists:

- Position remains active until delisting event.
- Exit value must be determined using available delisting information.

Delisted securities must never disappear from history.

---

## 17. Cash Management

Portfolio must track:

```text
cash
invested_capital
equity
```

Unallocated cash remains in the portfolio.

Default:

```text
0% interest on cash
```

---

## 18. Rebalancing

Supported frequencies:

```text
Daily
Weekly
Monthly
Quarterly
```

Example:

```yaml
rebalance_frequency: MONTHLY
```

---

## 19. Performance Metrics

Required metrics:

```text
Total Return
Annualized Return
CAGR
Volatility
Sharpe Ratio
Sortino Ratio
Maximum Drawdown
Calmar Ratio
Win Rate
Profit Factor
Average Trade
Number of Trades
Turnover
```

---

## 20. Benchmark Comparison

Backtests may compare results against benchmarks.

Examples:

```text
S&P 500
Russell 1000
Russell 3000
```

Benchmark data must be point-in-time correct.

---

## 21. Validation Requirements

Backtests must verify:

### Data Integrity

- Valid prices
- Valid dates
- Valid identifiers

### Execution Integrity

- No negative shares
- No impossible fills
- No future data usage

### Portfolio Integrity

- Cash balance consistency
- Equity consistency
- Position consistency

Failures must halt execution.

---

## 22. Result Persistence

Every backtest must persist:

```text
backtest_id
execution_timestamp
data_version
universe_version
configuration_hash
```

---

## 23. Portfolio Snapshot Schema

For every evaluation date:

```text
date
cash
equity
portfolio_value
drawdown
number_of_positions
```

---

## 24. Trade Schema

Each executed trade must contain:

```text
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

---

## 25. Experiment Isolation

Each experiment must start with:

```text
Fresh capital
No positions
Independent state
```

Experiments must never share portfolio state.

---

## 26. Reproducibility Requirements

Every result must be reproducible using:

```text
Data Version
Universe Version
Signal Versions
Configuration
Backtest Version
```

---

## 27. Default Research Configuration

```yaml
initial_capital: 100000

execution_price: NEXT_OPEN

commission_pct: 0.0

slippage_pct: 0.001

rebalance_frequency: MONTHLY
```

---

## 28. Integration Requirements

Consumes outputs from:

- data_specification.md
- universe_specification.md
- entry_signal_specification.md
- exit_signal_specification.md
- factor_scoring_specification.md
- factor_combination_specification.md
- portfolio_construction_specification.md

Produces outputs for:

- factor_performance_specification.md
- entry_robustness_scoring_specification.md
- entry_result_schema_specification.md

---

## 29. Compliance Requirements

All implementations must guarantee:

- Point-in-time correctness
- Deterministic execution
- Reproducibility
- Look-ahead-bias protection
- Survivorship-bias protection
- Explicit execution assumptions
- Complete auditability

Any implementation violating these requirements is non-compliant.
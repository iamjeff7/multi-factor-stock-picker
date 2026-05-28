# exit_signal_specification.md

## 1. Purpose

Define the standardized interface, execution rules, configuration requirements, and output schema for all exit signals used within the research framework.

Exit signals determine when an existing position should be closed.

Unlike entry signals, exit signals are decision rules rather than ranking factors.

The purpose of this specification is to allow exit methodologies to be researched, tested, compared, and reused consistently across all experiments.

---

## 2. Scope

This specification defines:

- Exit signal architecture
- Exit signal execution
- Position monitoring
- Exit trigger generation
- Signal outputs
- Validation requirements
- Persistence requirements

This specification does not define:

- Entry signals
- Portfolio construction
- Position sizing
- Risk allocation
- Backtest execution engine

---

## 3. Core Principles

### 3.1 Position-Based Evaluation

Exit signals operate on existing positions.

They are not evaluated on securities that are not currently held.

---

### 3.2 Point-in-Time Correctness

Exit decisions may only use information available on the evaluation date.

Future information must never be visible.

---

### 3.3 Determinism

Given identical:

- Data version
- Configuration
- Position history

The exit signal must produce identical outputs.

---

### 3.4 Independence

Exit signals must operate independently.

One exit signal must not depend on outputs from another exit signal.

---

### 3.5 Reusability

Exit signals must be modular and reusable across multiple strategies and experiments.

---

## 4. Exit Signal Lifecycle

For each evaluation date:

1. Retrieve active positions.
2. Load required data.
3. Evaluate exit conditions.
4. Generate exit decisions.
5. Persist results.

Evaluation occurs independently for each position.

---

## 5. Exit Signal Interface

Every implementation must expose:

```python
class ExitSignal:

    signal_id: str

    def evaluate(
        self,
        evaluation_date,
        position,
        market_data
    ):
        pass
```

---

## 6. Signal Metadata

Required metadata:

```yaml
signal_id:
signal_name:
signal_description:
signal_category:
signal_version:
```

Example:

```yaml
signal_id: stop_loss_10pct
signal_name: 10 Percent Stop Loss
signal_category: STOP_LOSS
signal_version: 1.0
```

---

## 7. Supported Exit Categories

Examples:

- Stop Loss
- Trailing Stop
- Profit Target
- Time Exit
- Trend Exit
- Moving Average Exit
- Volatility Exit
- Drawdown Exit
- Fundamental Exit
- Composite Exit

The framework must support additional categories.

---

## 8. Data Access Rules

Exit signals may access:

- Historical prices
- Volume data
- Fundamental data
- Corporate actions
- Position information

All data access must be point-in-time correct.

---

## 9. Position Information Requirements

Exit signals may use:

```text
entry_date
entry_price
position_size
holding_period
highest_price_since_entry
lowest_price_since_entry
unrealized_pnl
```

Additional fields may be added.

---

## 10. Exit Decision Model

Exit signals produce one of:

```text
EXIT
HOLD
```

No ranking is produced.

No portfolio-level decisions are made.

---

## 11. Exit Trigger Rules

Exit rules must be explicitly defined.

Examples:

### Stop Loss

```text
close <= entry_price * 0.90
```

### Time Exit

```text
holding_period >= 252
```

### Trend Exit

```text
close < 200_day_moving_average
```

Exit conditions must be deterministic.

---

## 12. Missing Data Handling

Every signal must define:

```yaml
missing_data_policy:
```

Supported values:

```yaml
hold_position
force_exit
skip_evaluation
```

Implicit handling is prohibited.

---

## 13. Evaluation Frequency

Supported frequencies:

```text
Daily
Weekly
Monthly
```

Frequency must be configurable.

Example:

```yaml
evaluation_frequency: DAILY
```

---

## 14. Signal Validation

### 14.1 Input Validation

Verify:

- Valid position
- Valid security identifier
- Valid dates
- Required data availability

---

### 14.2 Output Validation

Verify:

```text
EXIT
HOLD
```

No other output values are allowed.

---

### 14.3 Failure Handling

Errors must be logged.

Signal execution failures must not be silent.

---

## 15. Configuration Requirements

Exit signals may expose configurable parameters.

Examples:

```yaml
stop_loss_pct: 0.10

profit_target_pct: 0.25

max_holding_days: 252
```

All parameters must be version controlled.

---

## 16. Composite Exit Signals

The framework must support combining multiple exit rules.

Supported operators:

```text
ANY
ALL
```

Example:

```text
Exit if:
    Stop Loss Triggered
OR
    Time Exit Triggered
```

Composite logic must be deterministic.

---

## 17. Result Schema

Each evaluation must produce:

```text
evaluation_date
security_id
position_id
signal_id
decision
```

Where:

```text
decision ∈ {EXIT, HOLD}
```

Optional:

```text
trigger_reason
metadata_json
```

---

## 18. Persistence Requirements

All exit evaluations must be persisted.

Required metadata:

```text
signal_version
data_version
execution_timestamp
```

This enables full reproducibility.

---

## 19. Example

Signal:

```text
10 Percent Stop Loss
```

Position:

```text
entry_price = 100
```

Current Price:

```text
89
```

Output:

```text
decision = EXIT
```

Reason:

```text
current_price <= entry_price * 0.90
```

---

## 20. Integration Requirements

Exit signals are consumed by:

- backtest_methodology_specification.md

Relationship:

```text
Position
    →
Exit Signal
    →
Exit Decision
    →
Trade Closure
```

---

## 21. Compliance Requirements

All implementations must guarantee:

- Point-in-time correctness
- Deterministic execution
- Explicit exit rules
- Explicit missing-data handling
- Reproducibility
- Independent evaluation
- Persistent auditability

Any implementation violating these requirements is non-compliant.
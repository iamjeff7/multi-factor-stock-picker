# entry_signal_specification.md

## 1. Purpose

Define the standardized interface, requirements, execution rules, and output schema for all entry signals used within the research framework.

Entry signals represent stock-selection factors.

Their purpose is to rank securities by expected future attractiveness.

Entry signals do not make buy/sell decisions and do not contain position sizing logic.

---

## 2. Scope

This specification defines:

- Entry signal architecture
- Signal execution requirements
- Signal outputs
- Data access rules
- Validation requirements
- Result persistence requirements

This specification does not define:

- Factor normalization
- Factor combination
- Portfolio construction
- Exit logic
- Risk management

---

## 3. Core Principles

### 3.1 Ranking Signal

Every entry signal must produce a ranking metric.

The signal evaluates relative attractiveness among securities.

Signals are not binary filters.

---

### 3.2 Point-in-Time Correctness

Signals may only use information available on the evaluation date.

Future information must never be visible.

---

### 3.3 Determinism

Given identical inputs:

- Data version
- Universe version
- Configuration

The signal must produce identical outputs.

---

### 3.4 Factor Independence

Each signal must operate independently.

Signals must not reference outputs from other signals.

---

### 3.5 Reusability

Signals must be modular and reusable within larger factor models.

---

## 4. Signal Lifecycle

For each evaluation date:

1. Load universe membership.
2. Retrieve required data.
3. Compute raw signal values.
4. Validate outputs.
5. Persist results.

Signal execution occurs independently for every factor.

---

## 5. Signal Interface

Every signal implementation must expose:

```python
class EntrySignal:

    signal_id: str

    def calculate(
        self,
        evaluation_date,
        universe
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
signal_id: momentum_12m
signal_name: 12 Month Momentum
signal_category: MOMENTUM
signal_version: 1.0
```

---

## 7. Supported Signal Categories

Examples:

- Momentum
- Trend
- Value
- Quality
- Growth
- Profitability
- Volatility
- Liquidity
- Sentiment
- Analyst
- Technical
- Fundamental

The framework must allow additional categories.

---

## 8. Data Access Rules

Signals may access:

- Price data
- Volume data
- Fundamental data
- Corporate actions
- Metadata
- Universe membership

All access must be point-in-time correct.

---

## 9. Signal Calculation Rules

### 9.1 Cross-Sectional Evaluation

Signals are evaluated across all eligible securities.

---

### 9.2 Security Independence

Signal calculation for one security must not depend on future values of another security.

---

### 9.3 Future Return Isolation

Signals must never access:

- Future prices
- Future returns
- Future fundamentals
- Future universe membership

---

## 10. Missing Data Handling

Signal implementations must explicitly define:

```yaml
missing_data_policy:
```

Supported policies:

```yaml
exclude_security
assign_null
assign_default_value
```

Implicit handling is prohibited.

---

## 11. Raw Signal Output

Each signal produces a raw value.

Examples:

```text
Momentum:
+0.42

PE Ratio:
17.5

ROE:
0.24

Moving Average Distance:
0.11
```

Raw outputs remain unnormalized.

---

## 12. Signal Direction

Each signal must define:

```yaml
higher_is_better
```

or

```yaml
lower_is_better
```

Examples:

```yaml
Momentum:
higher_is_better

PE Ratio:
lower_is_better
```

Direction is required for later factor scoring.

---

## 13. Signal Validation

### 13.1 Output Validation

Verify:

- Numeric output
- Finite value
- Valid identifier
- Valid date

---

### 13.2 Data Validation

Verify:

- Required inputs exist
- Inputs are point-in-time valid
- Inputs pass data quality checks

---

### 13.3 Failure Handling

Failures must be logged.

Signal execution must not silently continue.

---

## 14. Computational Requirements

Signals must support:

- Thousands of securities
- Decades of history
- Batch execution
- Parallel execution

Implementations should avoid unnecessary repeated calculations.

---

## 15. Configuration Requirements

Signals may expose configurable parameters.

Example:

```yaml
lookback_days: 252
```

Configurations must be version controlled.

---

## 16. Result Schema

Each signal must produce:

```text
evaluation_date
security_id
ticker
signal_id
raw_signal_value
```

Optional:

```text
metadata_json
```

---

## 17. Signal Registry

The framework must maintain a signal registry.

Required fields:

```text
signal_id
signal_name
signal_category
signal_version
enabled
```

Signals are discovered and executed through the registry.

---

## 18. Persistence Requirements

Signal results must be persisted.

Required metadata:

```text
signal_version
data_version
universe_version
execution_timestamp
```

This enables full reproducibility.

---

## 19. Signal Example

Example:

Signal:

```text
12 Month Momentum
```

Evaluation Date:

```text
2020-01-31
```

Output:

```text
security_id: 12345
ticker: AAPL
raw_signal_value: 0.42
```

Meaning:

```text
42% trailing return over lookback window
```

No ranking or normalization occurs at this stage.

---

## 20. Integration Requirements

Outputs from this specification become inputs to:

- factor_scoring_specification.md

The relationship is:

```text
Raw Signal
    →
Factor Scoring
    →
Normalized Factor Score
```

---

## 21. Compliance Requirements

All implementations must guarantee:

- Point-in-time correctness
- Deterministic execution
- Reproducibility
- Explicit signal direction
- Explicit missing-data handling
- Raw output preservation
- Signal independence

Any implementation violating these requirements is non-compliant.
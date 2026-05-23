# universe_specification.md

## 1. Purpose

Define the official stock universe used throughout the research framework.

The universe specification exists to ensure:

- Consistent factor evaluation
- Fair factor comparison
- Reproducible research
- Realistic investability assumptions
- Survivorship-bias protection

All entry signals, factor tests, factor combinations, and backtests must operate on a universe generated according to this specification.

---

## 2. Scope

This specification defines:

- Eligible securities
- Universe construction rules
- Liquidity requirements
- Historical membership reconstruction
- Point-in-time requirements
- Universe versioning

This specification does not define:

- Entry signals
- Factor scoring
- Portfolio construction
- Backtest execution

---

## 3. Core Principles

### 3.1 Point-in-Time Correctness

Universe membership must be determined using only information available on the evaluation date.

Future information must never influence membership.

---

### 3.2 Investability

Universe members must represent securities that could reasonably be traded by an investor.

---

### 3.3 Reproducibility

Universe generation must be deterministic.

Identical inputs must produce identical membership results.

---

### 3.4 Survivorship-Bias Protection

Historical universes must include securities that later:

- Delisted
- Merged
- Went bankrupt
- Were acquired

Current listings must never be used to reconstruct historical universes.

---

## 4. Eligible Security Types

Allowed:

- Common stocks

Excluded:

- ETFs
- Mutual funds
- Closed-end funds
- ADRs
- Preferred shares
- Rights
- Warrants
- Units
- SPACs
- OTC securities
- Leveraged products
- Inverse products
- Structured products

---

## 5. Exchange Requirements

Allowed exchanges:

- NYSE
- NASDAQ
- NYSE American

Additional exchanges may be added explicitly.

All exchange membership must be point-in-time correct.

---

## 6. Geographic Scope

Current implementation:

- United States equities

Future international markets are outside current scope.

---

## 7. Universe Construction Process

For each evaluation date:

1. Retrieve all securities existing on that date.
2. Apply security type filters.
3. Apply exchange filters.
4. Apply liquidity filters.
5. Apply data availability filters.
6. Generate final universe membership.

The resulting universe becomes the candidate set for factor evaluation.

---

## 8. Liquidity Requirements

### 8.1 Objective

Remove securities that cannot realistically support systematic trading.

---

### 8.2 Primary Liquidity Metric

Default metric:

- Average Daily Dollar Volume (ADDV)

Calculation window:

- 60 trading days

Formula:

ADDV = Average(Volume × Close)

---

### 8.3 Minimum Liquidity Threshold

Configurable parameter:

```yaml
min_average_daily_dollar_volume
```

Default value:

```yaml
1000000
```

Meaning:

- Minimum ADDV = $1,000,000

---

### 8.4 Historical Calculation

Liquidity metrics must be calculated using only information available before the evaluation date.

Future trading activity must not be visible.

---

## 9. Price Requirements

Configurable parameter:

```yaml
min_price
```

Default:

```yaml
5.00
```

Evaluation:

```text
close_price_on_evaluation_date
```

Securities below threshold are excluded.

---

## 10. Market Capitalization Requirements

Optional filter.

Configurable parameter:

```yaml
min_market_cap
```

Default:

```yaml
null
```

If enabled:

```text
market_cap >= threshold
```

Market capitalization must be point-in-time correct.

---

## 11. Data Availability Requirements

A security may enter the universe only if required datasets are available.

Required:

- Price history
- Volume history
- Security metadata

Optional depending on factor requirements:

- Fundamental data

Missing required data results in exclusion.

---

## 12. Historical Membership Reconstruction

Universe membership must be reconstructable for any historical date.

Required capabilities:

- Daily membership generation
- Historical snapshots
- Reproducible reconstruction

Membership must never rely on present-day listings.

---

## 13. Delisted Securities

Delisted securities must remain available historically.

Before delisting:

- Eligible if all requirements are met.

After delisting:

- Not eligible.

Historical membership must remain unchanged.

---

## 14. IPO Handling

Recently listed securities may enter the universe after satisfying minimum history requirements.

Configurable parameter:

```yaml
minimum_trading_history_days
```

Default:

```yaml
252
```

Meaning:

- Approximately one year of trading history required.

---

## 15. Corporate Actions

Universe eligibility must remain stable through:

- Stock splits
- Reverse splits
- Ticker changes
- Name changes

Security identity must be tracked using permanent identifiers.

---

## 16. Universe Membership Schema

Required fields:

```text
evaluation_date
security_id
ticker
is_member
membership_reason
```

Optional fields:

```text
exchange
sector
industry
market_cap
average_daily_dollar_volume
```

---

## 17. Universe Versioning

Each generated universe must contain:

```text
universe_version
creation_timestamp
configuration_hash
data_version
```

Universe generation must be fully reproducible.

---

## 18. Validation Requirements

Validation must verify:

### Membership Consistency

- No duplicate securities
- Valid identifiers
- Valid dates

### Liquidity Metrics

- No negative values
- No impossible values

### Historical Integrity

- No future data usage
- No survivorship bias
- No look-ahead bias

Failures must halt universe generation.

---

## 19. Configuration Parameters

Default configuration:

```yaml
allowed_exchanges:
  - NYSE
  - NASDAQ
  - NYSE_AMERICAN

allowed_security_types:
  - COMMON_STOCK

min_price: 5.00

min_average_daily_dollar_volume: 1000000

min_market_cap: null

minimum_trading_history_days: 252
```

---

## 20. Outputs

Universe generation produces:

### Universe Membership Table

```text
evaluation_date
security_id
ticker
is_member
```

### Universe Metadata

```text
universe_version
configuration_hash
data_version
creation_timestamp
```

These outputs become inputs to:

- entry_signal_specification.md
- factor_scoring_specification.md
- factor_combination_specification.md
- backtest_methodology_specification.md

---

## 21. Compliance Requirements

All implementations must guarantee:

- Point-in-time correctness
- Deterministic execution
- Reproducibility
- Survivorship-bias protection
- Look-ahead-bias protection
- Historical membership reconstruction

Any universe implementation violating these requirements is non-compliant.
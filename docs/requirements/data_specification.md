# data_specification.md

## 1. Purpose

Define all data requirements, data handling rules, point-in-time assumptions, quality standards, storage requirements, and validation procedures used throughout the stock research framework.

This specification ensures that all research results are:

- Reproducible
- Point-in-time correct
- Free from look-ahead bias
- Consistent across experiments
- Comparable across factors and models

---

## 2. Scope

This specification governs:

- Market data
- Fundamental data
- Corporate actions
- Universe membership data
- Factor input data
- Data storage formats
- Data validation procedures

This specification does not define:

- Entry signals
- Factor scoring
- Portfolio construction
- Backtesting logic

---

## 3. Core Principles

### 3.1 Point-in-Time Integrity

All data used during research must reflect information available on the evaluation date.

Future information must never be accessible.

---

### 3.2 Reproducibility

Every experiment must be reproducible using:

- Identical data version
- Identical universe version
- Identical configuration

---

### 3.3 Determinism

Repeated execution using identical inputs must produce identical outputs.

---

### 3.4 Data Quality First

Missing, stale, corrupted, or inconsistent data must be detected before research execution.

---

## 4. Supported Asset Class

Current implementation:

- US common equities

Excluded:

- ETFs
- Mutual funds
- Preferred shares
- ADRs
- Warrants
- Rights
- Closed-end funds
- OTC securities
- Delisted securities lacking historical data

Universe eligibility is defined separately in:

- universe_specification.md

---

## 5. Required Data Categories

### 5.1 Price Data

Required fields:

- trade_date
- open
- high
- low
- close
- adjusted_close
- volume

Optional:

- vwap
- dollar_volume

Frequency:

- Daily

---

### 5.2 Corporate Actions

Required events:

- Stock splits
- Reverse splits
- Cash dividends
- Special dividends

Corporate actions must support reconstruction of historical adjusted prices.

---

### 5.3 Fundamental Data

Examples:

- Revenue
- Earnings
- Net income
- Operating income
- EBITDA
- Assets
- Liabilities
- Equity
- Cash flow metrics

Both:

- Raw reported values
- Point-in-time availability dates

must be stored.

---

### 5.4 Security Metadata

Required fields:

- ticker
- permanent_security_id
- company_name
- exchange
- sector
- industry

Ticker changes must be supported.

Permanent identifiers must remain stable through time.

---

### 5.5 Delisting Information

Required fields:

- delisting_date
- delisting_reason

Delisted securities must remain available for historical research.

---

### 5.6 Universe Membership Data

The system must support historical reconstruction of:

- Index membership
- Research universe membership
- Eligibility status

Membership must be point-in-time correct.

---

## 6. Point-in-Time Requirements

### 6.1 Fundamental Data Timing

Research calculations must use:

- Filing publication date
- Data availability date

Never use reporting period end date as data availability date.

---

### 6.2 Revision Handling

Historical calculations must use data available at that time.

Later revisions must not overwrite historical point-in-time values.

---

### 6.3 Price Availability

Signals generated on date T may only use information available at or before T.

Future bars must never be visible.

---

## 7. Data Frequency

Supported frequencies:

| Dataset | Frequency |
|----------|-----------|
| Price Data | Daily |
| Volume Data | Daily |
| Corporate Actions | Event Driven |
| Fundamentals | Filing Driven |
| Universe Membership | Daily Snapshot |

---

## 8. Missing Data Rules

### 8.1 Missing Values

Missing values must be explicitly represented.

Null values must not be silently converted.

---

### 8.2 Imputation

Default behavior:

- No imputation

Any imputation method must be explicitly configured and documented.

---

### 8.3 Factor Inputs

Factors may define their own missing-value handling rules.

Such rules must be implemented at the factor level, not at the data layer.

---

## 9. Data Validation

Validation must execute before research jobs begin.

### 9.1 Price Validation

Checks:

- Negative prices
- Zero prices
- Invalid OHLC relationships
- Duplicate records
- Missing dates

---

### 9.2 Volume Validation

Checks:

- Negative volume
- Missing volume
- Extreme outliers

---

### 9.3 Fundamental Validation

Checks:

- Invalid filing dates
- Duplicate filings
- Missing identifiers
- Impossible values

---

### 9.4 Corporate Action Validation

Checks:

- Duplicate events
- Invalid split ratios
- Invalid dividend amounts

---

### 9.5 Research Calendar Validation

Production research datasets must support the canonical research calendar defined in `backtest_methodology_specification.md` §30.

Checks:

- Earliest available history on or before 2005-01-01
- Latest available history through the most recently completed calendar year
- Sufficient trading-day coverage to compute an 80/20 in-sample / out-of-sample split

Demo and test datasets may use shorter windows when explicitly configured with `research_mode: DEMO` or `research_mode: TEST`.

Validation failures in production mode must halt research execution.

---

## 10. Survivorship Bias Requirements

Historical datasets must include:

- Active securities
- Delisted securities
- Acquired securities
- Bankrupt securities

The research framework must not rely on current ticker lists.

Historical universe reconstruction must be possible.

---

## 11. Data Storage Requirements

### 11.1 Immutable Raw Data

Raw source data must never be modified.

Raw datasets must be stored separately.

---

### 11.2 Processed Data

Derived datasets may be generated from raw data.

Processing must be reproducible.

---

### 11.3 Versioning

Every dataset must contain:

- data_version
- creation_timestamp

Research results must record data version used.

---

## 12. Required Identifiers

Every security must have:

- Permanent security identifier
- Ticker
- Exchange

Research logic must use permanent identifiers internally.

Tickers are display-only identifiers.

---

## 13. Data Access Interface

All research modules must access data through a standardized interface.

Required capabilities:

- Retrieve historical prices
- Retrieve fundamentals
- Retrieve corporate actions
- Retrieve universe membership
- Retrieve metadata
- Retrieve delisting information

The interface must abstract the underlying storage system.

---

## 14. Research Dataset Snapshot

Each experiment must record:

- data_version
- universe_version
- execution_timestamp

This enables full experiment reproducibility.

---

## 15. Performance Requirements

The data layer must support:

- Thousands of securities
- Decades of history
- Repeated factor evaluations
- Large-scale backtests

Data retrieval should minimize repeated disk access and redundant calculations.

---

## 16. Outputs

The data layer must provide point-in-time access to:

- Prices
- Volumes
- Corporate actions
- Fundamentals
- Metadata
- Universe membership
- Delisting records

These outputs become inputs to:

- entry_signal_specification.md
- factor_scoring_specification.md
- factor_combination_specification.md
- backtest_methodology_specification.md

---

## 17. Research Calendar Requirements

The data layer must provide point-in-time history covering the production research window:

```text
start: 2005-01-01
end:   December 31 of the most recently completed calendar year
```

Requirements:

- History must be available on a trading-day basis for split computation
- Delisted securities must remain available across the full window
- Dataset versioning must record the effective calendar bounds

Shorter windows are permitted only for demo or test execution with explicit configuration override.

Cross-reference: `backtest_methodology_specification.md` §30 Validation Framework.

---

## 18. Compliance Requirements

All implementations must guarantee:

- Point-in-time correctness
- Reproducibility
- Deterministic execution
- Survivorship-bias protection
- Look-ahead-bias protection
- Dataset version tracking

Non-compliant data sources or processing pipelines must be rejected.
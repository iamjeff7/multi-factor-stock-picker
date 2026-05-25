"""Result schema validator tests."""

from datetime import date
from decimal import Decimal

import pytest

from core.exceptions import ValidationError
from core.types import TradeId
from reporting.validator import ResultSchemaValidator
from schemas.results import StockSummaryRecord, TradeRecord


def test_validate_trades_rejects_exit_before_entry(sample_trade: TradeRecord) -> None:
    validator = ResultSchemaValidator()
    trade = sample_trade.model_copy(update={"exit_date": date(2019, 12, 31)})

    with pytest.raises(ValidationError, match="exits before entry"):
        validator.validate_trades_or_raise([trade])


def test_validate_trades_rejects_duplicate_trade_id(sample_trade: TradeRecord) -> None:
    validator = ResultSchemaValidator()

    with pytest.raises(ValidationError, match="Duplicate trade primary key"):
        validator.validate_trades_or_raise([sample_trade, sample_trade])


def test_validate_stock_summary_matches_trades(sample_trade: TradeRecord) -> None:
    validator = ResultSchemaValidator()
    trades = [
        sample_trade,
        sample_trade.model_copy(
            update={
                "trade_id": TradeId("trade_002"),
                "net_pnl": Decimal("-20"),
                "gross_pnl": Decimal("-20"),
            }
        ),
    ]
    summary = StockSummaryRecord(
        experiment_id=sample_trade.experiment_id,
        security_id=sample_trade.security_id,
        ticker=sample_trade.ticker,
        number_of_trades=2,
        closed_trades=2,
        open_trades=0,
    )

    validator.validate_stock_summary_matches_trades_or_raise(trades, [summary])


def test_validate_stock_summary_rejects_count_mismatch(sample_trade: TradeRecord) -> None:
    validator = ResultSchemaValidator()
    summary = StockSummaryRecord(
        experiment_id=sample_trade.experiment_id,
        security_id=sample_trade.security_id,
        ticker=sample_trade.ticker,
        number_of_trades=2,
        closed_trades=1,
        open_trades=1,
    )

    with pytest.raises(ValidationError, match="Summary trade count"):
        validator.validate_stock_summary_matches_trades_or_raise([sample_trade], [summary])

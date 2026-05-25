"""In-sample to out-of-sample degradation metrics."""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel

from schemas.results import ExperimentSummaryRecord


class SampleDegradationMetrics(BaseModel):
    """Derived deltas between in-sample and out-of-sample experiment metrics."""

    is_mean_stock_return: Decimal | None = None
    oos_mean_stock_return: Decimal | None = None
    is_to_oos_mean_return_delta: Decimal | None = None
    is_win_rate: Decimal | None = None
    oos_win_rate: Decimal | None = None
    is_to_oos_win_rate_delta: Decimal | None = None
    is_total_net_pnl: Decimal | None = None
    oos_total_net_pnl: Decimal | None = None
    is_to_oos_total_net_pnl_delta: Decimal | None = None
    overfitting_warning: bool = False


def compute_degradation_metrics(
    is_summary: ExperimentSummaryRecord,
    oos_summary: ExperimentSummaryRecord,
    *,
    return_ratio_threshold: Decimal = Decimal("0.5"),
) -> SampleDegradationMetrics:
    is_return = is_summary.mean_stock_return
    oos_return = oos_summary.mean_stock_return
    return_delta = (
        None
        if is_return is None or oos_return is None
        else oos_return - is_return
    )

    is_win_rate = is_summary.win_rate
    oos_win_rate = oos_summary.win_rate
    win_rate_delta = (
        None
        if is_win_rate is None or oos_win_rate is None
        else oos_win_rate - is_win_rate
    )

    is_pnl = is_summary.total_net_pnl
    oos_pnl = oos_summary.total_net_pnl
    pnl_delta = None if is_pnl is None or oos_pnl is None else oos_pnl - is_pnl

    overfitting_warning = False
    if (
        is_return is not None
        and oos_return is not None
        and is_return > Decimal("0")
        and oos_return < is_return * return_ratio_threshold
    ):
        overfitting_warning = True
    if (
        is_return is not None
        and oos_return is not None
        and is_return > Decimal("0")
        and oos_return <= Decimal("0")
    ):
        overfitting_warning = True

    return SampleDegradationMetrics(
        is_mean_stock_return=is_return,
        oos_mean_stock_return=oos_return,
        is_to_oos_mean_return_delta=return_delta,
        is_win_rate=is_win_rate,
        oos_win_rate=oos_win_rate,
        is_to_oos_win_rate_delta=win_rate_delta,
        is_total_net_pnl=is_pnl,
        oos_total_net_pnl=oos_pnl,
        is_to_oos_total_net_pnl_delta=pnl_delta,
        overfitting_warning=overfitting_warning,
    )

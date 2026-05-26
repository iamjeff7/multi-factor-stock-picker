"""Factor performance validation."""

from __future__ import annotations

from collections.abc import Sequence

from core.exceptions import ValidationError
from factors.performance.config import FactorPerformanceConfig
from schemas.factors import FactorScore
from schemas.ic import ForwardReturn


class FactorPerformanceValidator:
    """Validates factor performance inputs."""

    def validate_inputs_or_raise(
        self,
        factor_scores: Sequence[FactorScore],
        forward_returns: Sequence[ForwardReturn],
        *,
        horizon: int,
        config: FactorPerformanceConfig,
    ) -> None:
        if not factor_scores:
            raise ValidationError("At least one factor score is required")
        if not forward_returns:
            raise ValidationError("At least one forward return is required")

        securities_per_date: dict[object, int] = {}
        for row in factor_scores:
            securities_per_date[row.evaluation_date] = (
                securities_per_date.get(row.evaluation_date, 0) + 1
            )

        minimum_count = max(config.quantile_count, 2)
        for evaluation_date, count in securities_per_date.items():
            if count < 2:
                raise ValidationError(
                    f"At least two scored securities required on {evaluation_date}"
                )
            if count < minimum_count and count < config.quantile_count:
                continue

        horizon_returns = [row for row in forward_returns if row.horizon == horizon]
        if not horizon_returns:
            raise ValidationError(f"No forward returns available for horizon {horizon}")

"""Dataset-wide validation orchestrator."""

from __future__ import annotations

from datetime import UTC, datetime

from data.loaders.dataset import LoadedDataset
from data.validation.corporate_actions import validate_corporate_actions
from data.validation.fundamentals import validate_fundamentals
from data.validation.price import validate_prices
from data.validation.volume import validate_volumes
from schemas.data import ValidationIssue, ValidationReport


class DatasetValidator:
    """Validates a loaded dataset before research use."""

    def validate_all(self, dataset: LoadedDataset) -> ValidationReport:
        issues: list[ValidationIssue] = []
        security_ids = dataset.security_ids

        for security_id in security_ids:
            sid = str(security_id)
            bars = dataset.prices.get(security_id, [])
            issues.extend(validate_prices(sid, bars))
            issues.extend(validate_volumes(sid, bars))
            issues.extend(validate_fundamentals(sid, dataset.fundamentals.get(security_id, [])))
            issues.extend(
                validate_corporate_actions(sid, dataset.corporate_actions.get(security_id, []))
            )

        return ValidationReport(
            passed=len(issues) == 0,
            issues=issues,
            validated_at=datetime.now(tz=UTC),
        )

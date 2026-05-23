"""Protocol import smoke tests."""


def test_all_protocol_modules_import() -> None:
    import backtest.engine  # noqa: F401
    import backtest.execution  # noqa: F401
    import backtest.position_sizing  # noqa: F401
    import data.protocols  # noqa: F401
    import data.universe.protocols  # noqa: F401
    import entry_signals.protocols  # noqa: F401
    import exit_signals.protocols  # noqa: F401
    import factors.combination.protocols  # noqa: F401
    import factors.scoring.protocols  # noqa: F401
    import reporting.protocols  # noqa: F401


def test_top_level_modules_import() -> None:
    import backtest  # noqa: F401
    import config  # noqa: F401
    import core  # noqa: F401
    import data  # noqa: F401
    import entry_signals  # noqa: F401
    import evaluation  # noqa: F401
    import exit_signals  # noqa: F401
    import factors  # noqa: F401
    import reporting  # noqa: F401
    import schemas.enums  # noqa: F401

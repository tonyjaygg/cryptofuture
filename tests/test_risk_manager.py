from risk.manager import RiskManager


def test_daily_limit() -> None:
    rm = RiskManager(0.02, 1000)
    assert rm.check_daily() is True
    rm.register_loss(30)
    assert rm.check_daily() is False

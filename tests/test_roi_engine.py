from app.services.roi_engine import compute_roi, project_incremental_revenue


def test_compute_roi_base_example():
    result = compute_roi(investment_cost=60000, incremental_revenue=240000)
    assert result.roi_percent == 300.0
    assert result.multiple == 4.0
    assert result.band == "high_growth"
    assert result.baseline == "revenue"


def test_compute_roi_break_even():
    result = compute_roi(investment_cost=50000, incremental_revenue=50000)
    assert result.roi_percent == 0.0
    assert result.band == "break_even"


def test_compute_roi_negative():
    result = compute_roi(investment_cost=80000, incremental_revenue=20000)
    assert result.roi_percent == -75.0
    assert result.band == "negative"


def test_compute_roi_zero_cost_invalid():
    try:
        compute_roi(investment_cost=0, incremental_revenue=100)
    except ValueError as exc:
        assert "investment_cost must be > 0" in str(exc)
    else:
        raise AssertionError("Expected ValueError for zero investment cost")


def test_project_incremental_revenue():
    projected = project_incremental_revenue(
        monthly_traffic=10000,
        current_conversion_rate=0.02,
        target_conversion_rate=0.03,
        average_deal_value=1000,
        close_rate=0.25,
    )
    assert projected == 25000.0


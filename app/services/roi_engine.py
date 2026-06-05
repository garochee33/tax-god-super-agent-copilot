"""
ROI and conversion-funnel projection engine.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ROIResult:
    roi_percent: float
    multiple: float
    band: str
    baseline: str


def classify_roi_band(roi_percent: float) -> str:
    if roi_percent < 0:
        return "negative"
    if roi_percent == 0:
        return "break_even"
    if roi_percent >= 300:
        return "high_growth"
    if roi_percent >= 200:
        return "triple_plus"
    if roi_percent >= 100:
        return "doubled"
    return "positive"


def compute_roi(
    *,
    investment_cost: float,
    incremental_revenue: float | None = None,
    incremental_gross_profit: float | None = None,
) -> ROIResult:
    if investment_cost <= 0:
        raise ValueError("investment_cost must be > 0")
    if incremental_revenue is None and incremental_gross_profit is None:
        raise ValueError("Provide incremental_revenue or incremental_gross_profit")

    baseline_value = incremental_gross_profit if incremental_gross_profit is not None else incremental_revenue
    assert baseline_value is not None
    if baseline_value < 0:
        raise ValueError("baseline value must be >= 0")

    roi_percent = ((baseline_value - investment_cost) / investment_cost) * 100
    multiple = baseline_value / investment_cost
    roi_percent = round(roi_percent, 2)
    multiple = round(multiple, 2)

    return ROIResult(
        roi_percent=roi_percent,
        multiple=multiple,
        band=classify_roi_band(roi_percent),
        baseline="gross_profit" if incremental_gross_profit is not None else "revenue",
    )


def project_incremental_revenue(
    *,
    monthly_traffic: float,
    current_conversion_rate: float,
    target_conversion_rate: float,
    average_deal_value: float,
    close_rate: float,
) -> float:
    for name, value in (
        ("monthly_traffic", monthly_traffic),
        ("average_deal_value", average_deal_value),
    ):
        if value < 0:
            raise ValueError(f"{name} must be >= 0")

    for name, value in (
        ("current_conversion_rate", current_conversion_rate),
        ("target_conversion_rate", target_conversion_rate),
        ("close_rate", close_rate),
    ):
        if not 0 <= value <= 1:
            raise ValueError(f"{name} must be between 0 and 1")

    if target_conversion_rate < current_conversion_rate:
        raise ValueError("target_conversion_rate must be >= current_conversion_rate")

    incremental_leads = monthly_traffic * (target_conversion_rate - current_conversion_rate)
    incremental_closed_deals = incremental_leads * close_rate
    return round(incremental_closed_deals * average_deal_value, 2)

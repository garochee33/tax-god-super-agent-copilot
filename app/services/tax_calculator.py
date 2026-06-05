"""Tax God - Tax Calculator Service (2024 Federal Brackets)"""

from __future__ import annotations

from datetime import date

BRACKETS_2024 = {
    "single": [
        (11600, 0.10), (47150, 0.12), (100525, 0.22),
        (191950, 0.24), (243725, 0.32), (609350, 0.35), (float("inf"), 0.37),
    ],
    "married_filing_jointly": [
        (23200, 0.10), (94300, 0.12), (201050, 0.22),
        (383900, 0.24), (487450, 0.32), (731200, 0.35), (float("inf"), 0.37),
    ],
    "married_filing_separately": [
        (11600, 0.10), (47150, 0.12), (100525, 0.22),
        (191950, 0.24), (243725, 0.32), (365600, 0.35), (float("inf"), 0.37),
    ],
    "head_of_household": [
        (16550, 0.10), (63100, 0.12), (100500, 0.22),
        (191950, 0.24), (243700, 0.32), (609350, 0.35), (float("inf"), 0.37),
    ],
}

STANDARD_DEDUCTION_2024 = {
    "single": 14600,
    "married_filing_jointly": 29200,
    "married_filing_separately": 14600,
    "head_of_household": 21900,
}

SE_TAX_RATE = 0.153
SE_NET_FACTOR = 0.9235
QUARTERLY_DEADLINES = [
    (1, 15), (4, 15), (6, 15), (9, 15),
]


def _compute_federal_tax(taxable_income: float, filing_status: str) -> float:
    brackets = BRACKETS_2024[filing_status]
    tax = 0.0
    prev = 0.0
    for ceiling, rate in brackets:
        if taxable_income <= prev:
            break
        chunk = min(taxable_income, ceiling) - prev
        tax += chunk * rate
        prev = ceiling
    return tax


def _next_deadline(today: date | None = None) -> str:
    today = today or date.today()
    year = today.year
    for month, day in QUARTERLY_DEADLINES:
        d = date(year, month, day)
        if d > today:
            return d.isoformat()
    return date(year + 1, 1, 15).isoformat()


def calculate_quarterly_estimate(
    income: float,
    expenses: float,
    filing_status: str = "single",
    state: str | None = None,
) -> dict:
    net = income - expenses
    se_base = net * SE_NET_FACTOR
    se_tax = max(se_base * SE_TAX_RATE, 0)
    deduction = STANDARD_DEDUCTION_2024.get(filing_status, 14600)
    se_deduction = se_tax / 2
    taxable = max(net - deduction - se_deduction, 0)
    federal_tax = _compute_federal_tax(taxable, filing_status)
    total_tax = federal_tax + se_tax
    effective_rate = (total_tax / income * 100) if income > 0 else 0
    return {
        "estimated_tax": round(total_tax, 2),
        "effective_rate": round(effective_rate, 2),
        "quarterly_payment": round(total_tax / 4, 2),
        "next_due_date": _next_deadline(),
    }

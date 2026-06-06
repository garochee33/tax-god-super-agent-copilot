"""Tax God - Currency Service"""

from __future__ import annotations

import logging
import time

import httpx

logger = logging.getLogger(__name__)

SUPPORTED_CURRENCIES = [
    "USD", "EUR", "GBP", "CAD", "AUD", "JPY", "CHF", "CNY", "INR", "MXN",
    "BRL", "KRW", "SGD", "HKD", "NZD", "SEK", "NOK", "DKK", "ZAR", "AED",
]

# Fallback rates relative to USD
_FALLBACK_RATES: dict[str, float] = {
    "USD": 1.0, "EUR": 0.92, "GBP": 0.79, "CAD": 1.36, "AUD": 1.53,
    "JPY": 157.0, "CHF": 0.88, "CNY": 7.25, "INR": 83.5, "MXN": 17.2,
    "BRL": 5.0, "KRW": 1320.0, "SGD": 1.34, "HKD": 7.81, "NZD": 1.64,
    "SEK": 10.5, "NOK": 10.7, "DKK": 6.9, "ZAR": 18.5, "AED": 3.67,
}


class CurrencyService:
    def __init__(self):
        self._cache: dict[str, dict[str, float]] = {}
        self._cache_ts: dict[str, float] = {}
        self._ttl = 3600  # 1 hour

    def _is_cached(self, base: str) -> bool:
        return base in self._cache and (time.time() - self._cache_ts.get(base, 0)) < self._ttl

    def _fetch_rates(self, base: str) -> dict[str, float]:
        if self._is_cached(base):
            return self._cache[base]
        try:
            resp = httpx.get(
                f"https://api.exchangerate.host/latest?base={base}",
                timeout=5,
            )
            if resp.status_code == 200:
                data = resp.json()
                rates = data.get("rates")
                if rates:
                    self._cache[base] = {k: float(v) for k, v in rates.items() if k in SUPPORTED_CURRENCIES}
                    self._cache_ts[base] = time.time()
                    return self._cache[base]
        except Exception as exc:
            logger.warning("Exchange rate API failed: %s, using fallback", exc)

        # Fallback: compute from hardcoded USD rates
        base_in_usd = _FALLBACK_RATES.get(base, 1.0)
        rates = {cur: rate / base_in_usd for cur, rate in _FALLBACK_RATES.items()}
        self._cache[base] = rates
        self._cache_ts[base] = time.time()
        return rates

    def get_exchange_rate(self, from_currency: str, to_currency: str) -> float:
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()
        if from_currency == to_currency:
            return 1.0
        rates = self._fetch_rates(from_currency)
        if to_currency in rates:
            return rates[to_currency]
        # Cross-rate via USD fallback
        from_usd = _FALLBACK_RATES.get(from_currency, 1.0)
        to_usd = _FALLBACK_RATES.get(to_currency, 1.0)
        return to_usd / from_usd

    def convert(self, amount: float, from_cur: str, to_cur: str) -> float:
        return round(amount * self.get_exchange_rate(from_cur, to_cur), 4)

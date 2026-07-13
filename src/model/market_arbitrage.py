"""Paper-only-Pruefung binaerer Cross-Platform-Arbitrage.

Ein Kandidat darf nur entstehen, wenn beide Legs denselben kanonischen Vertrag,
dieselben Settlement-Regeln und dieselbe Auszahlung besitzen. Preise muessen als
ausfuehrbare Ask-Quotes fuer die Zielmenge vorliegen; unbekannte Gebuehren,
Slippage, Tiefe oder veraltete Quotes blockieren die Pruefung. Dieses Modul fuehrt
keine Orders aus und veraendert weder Value- noch Staking-Parameter.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass


@dataclass(frozen=True)
class MarketContract:
    fixture_id: str
    market_type: str
    selection: str
    period: str
    settlement_rule: str
    rules_hash: str
    currency: str = "USD"
    payout_per_contract: float = 1.0

    def identity(self) -> tuple:
        return (self.fixture_id, self.market_type, self.selection, self.period,
                self.settlement_rule, self.rules_hash, self.currency,
                self.payout_per_contract)


@dataclass(frozen=True)
class ExecutableQuote:
    platform: str
    contract_id: str
    contract: MarketContract
    side: str
    ask_price: float
    max_quantity: float
    fee_per_contract: float | None
    slippage_per_contract: float | None
    captured_at: str


def _parse_utc(value: str) -> dt.datetime | None:
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=dt.timezone.utc)
        return parsed.astimezone(dt.timezone.utc)
    except Exception:
        return None


def _validate_quote(quote: ExecutableQuote, quantity: float, now: dt.datetime,
                    max_age_seconds: int) -> str | None:
    if quote.side not in ("yes", "no"):
        return "ungueltige Seite"
    payout = quote.contract.payout_per_contract
    if not (0.0 < quote.ask_price < payout):
        return "ungueltiger Ask-Preis"
    if quote.max_quantity < quantity:
        return "unzureichende Markttiefe"
    if quote.fee_per_contract is None:
        return "Gebuehr unbekannt"
    if quote.slippage_per_contract is None:
        return "Slippage unbekannt"
    if quote.fee_per_contract < 0 or quote.slippage_per_contract < 0:
        return "negative Kostenannahme"
    captured = _parse_utc(quote.captured_at)
    if captured is None:
        return "ungueltiger Quote-Zeitpunkt"
    age = (now - captured).total_seconds()
    if age < -5 or age > max_age_seconds:
        return "Quote veraltet"
    if not all((quote.contract.fixture_id, quote.contract.market_type,
                quote.contract.selection, quote.contract.period,
                quote.contract.settlement_rule, quote.contract.rules_hash)):
        return "Marktvertrag unvollstaendig"
    return None


def scan_binary_arbitrage(quotes: list[ExecutableQuote], target_quantity: float = 1.0,
                          max_age_seconds: int = 120,
                          now: dt.datetime | None = None) -> dict:
    """Findet kostenbereinigte YES/NO-Paare; Ergebnis bleibt immer paper-only."""
    if target_quantity <= 0:
        raise ValueError("target_quantity muss positiv sein")
    now = (now or dt.datetime.now(dt.timezone.utc)).astimezone(dt.timezone.utc)
    valid, blocked = [], []
    for quote in quotes:
        reason = _validate_quote(quote, target_quantity, now, max_age_seconds)
        if reason:
            blocked.append({"platform": quote.platform, "contract_id": quote.contract_id,
                            "reason": reason})
        else:
            valid.append(quote)

    opportunities = []
    yes_quotes = [q for q in valid if q.side == "yes"]
    no_quotes = [q for q in valid if q.side == "no"]
    for yes in yes_quotes:
        for no in no_quotes:
            if yes.platform == no.platform:
                continue
            if yes.contract.identity() != no.contract.identity():
                continue
            quantity = target_quantity
            yes_unit = yes.ask_price + yes.fee_per_contract + yes.slippage_per_contract
            no_unit = no.ask_price + no.fee_per_contract + no.slippage_per_contract
            total_cost = quantity * (yes_unit + no_unit)
            payout = quantity * yes.contract.payout_per_contract
            profit = payout - total_cost
            if profit <= 0:
                continue
            opportunities.append({
                "canonical_contract": yes.contract.identity(),
                "yes_platform": yes.platform, "no_platform": no.platform,
                "quantity": quantity, "total_cost": round(total_cost, 6),
                "guaranteed_payout": round(payout, 6),
                "profit_after_costs": round(profit, 6),
                "margin_on_cost": round(profit / total_cost, 6),
                "paper_only": True,
            })
    opportunities.sort(key=lambda row: -row["profit_after_costs"])
    return {"status": "candidate" if opportunities else "none",
            "paper_only": True, "target_quantity": target_quantity,
            "opportunities": opportunities, "blocked_quotes": blocked,
            "note": "Keine Orderausfuehrung; unbekannte Kosten oder Tiefe blockieren Kandidaten."}


def audit_legacy_sources(market: dict | None, kalshi: dict | None) -> dict:
    """Dokumentiert, warum heutige Wahrscheinlichkeits-Payloads nicht arb-faehig sind."""
    available = [name for name, payload in (("polymarket", market), ("kalshi", kalshi))
                 if payload and payload.get("probs")]
    blockers = []
    if len(available) < 2:
        blockers.append("weniger als zwei Plattformen verfuegbar")
    blockers += ["kein kanonischer Settlement-Vertrag", "keine Orderbuch-Tiefe",
                 "keine mengenbezogene Slippage", "keine verifizierte Gebuehr"]
    return {"status": "blocked", "paper_only": True, "sources": available,
            "blockers": blockers,
            "note": "Preisdivergenz ist noch keine handelbare Arbitrage."}

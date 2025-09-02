"""Example: infer implied funding rates from option prices.

This script demonstrates how to use Schwab's option chain and quotes
endpoints to compute the synthetic forward price and implied funding
rate (cost of carry) for at-the-money options.

It mirrors the reasoning in the accompanying article about using
put–call parity in reverse: instead of assuming a risk‑free rate and
checking for arbitrage, we *imply* the rate that makes put–call parity
hold.  The result lets traders compare their own funding rate with the
market-implied rate to decide whether owning shares or their synthetic
is cheaper.

The script requires developer credentials but no account balance.  It
fetches market data only and does **not** place trades.
"""

from __future__ import annotations

import datetime as _dt
import logging
import math
import os
from typing import Iterable

from dotenv import load_dotenv

import schwabdev


def _mid(bid: float | None, ask: float | None) -> float:
    """Return the mid price from bid/ask quotes."""
    bid = bid or 0.0
    ask = ask or 0.0
    if bid and ask:
        return (bid + ask) / 2
    return bid or ask


def implied_rates(client: schwabdev.Client, symbol: str, expirations: Iterable[str] | None = None) -> None:
    """Print implied funding rates for *symbol*.

    Args:
        client: Authenticated Schwab client.
        symbol: Underlying ticker symbol.
        expirations: Optional iterable of ISO dates (YYYY-MM-DD) to
            restrict the expirations inspected.  When ``None`` the first
            few expirations returned by the API are used.
    """
    # Request a small number of strikes around the money and include the
    # underlying quote so we do not need a second API call.
    resp = client.option_chains(symbol, includeUnderlyingQuote=True, strikeCount=1)
    data = resp.json()

    underlying = data.get("underlying", {})
    spot = underlying.get("mark", underlying.get("last", data.get("underlyingPrice")))
    if spot is None:
        raise RuntimeError("Could not determine underlying price from option chain response")

    call_map: dict[str, dict[str, list[dict]]] = data["callExpDateMap"]
    put_map: dict[str, dict[str, list[dict]]] = data["putExpDateMap"]

    for exp_date, strikes in call_map.items():
        date_str = exp_date.split(":")[0]  # format 'YYYY-MM-DD:days'
        if expirations and date_str not in expirations:
            continue
        strike = next(iter(strikes))  # take the first strike returned (near ATM)
        call = strikes[strike][0]
        put = put_map[exp_date][strike][0]

        call_price = _mid(call.get("bid"), call.get("ask"))
        put_price = _mid(put.get("bid"), put.get("ask"))
        K = float(strike)
        # synthetic future price from put-call parity
        synthetic = call_price - put_price
        intrinsic = spot - K
        carry = synthetic - intrinsic

        days = call.get("daysToExpiration") or put.get("daysToExpiration")
        t = days / 365.0
        if t <= 0:
            continue
        # R/C = K * (1 - e^{-rt})  =>  r = -ln(1 - R/C/K) / t
        r = -math.log(1 - carry / K) / t
        print(f"Expiry {date_str} strike {K:.2f} -> implied rate {r*100:.2f}%")



def main() -> None:
    # place your app key and app secret in the .env file
    load_dotenv()

    if len(os.getenv("app_key", "")) != 32 or len(os.getenv("app_secret", "")) != 16:
        raise Exception("Add your app key and app secret to the .env file.")

    logging.basicConfig(level=logging.INFO)
    client = schwabdev.Client(os.getenv("app_key"), os.getenv("app_secret"), os.getenv("callback_url"))

    symbol = os.getenv("symbol", "USO")
    print(f"Implying funding rates for {symbol} (no trades are placed)...\n")
    implied_rates(client, symbol)


if __name__ == "__main__":
    print("Welcome to Schwabdev, The Unofficial Schwab API Python Wrapper!")
    print("Documentation: https://tylerebowers.github.io/Schwabdev/")
    main()

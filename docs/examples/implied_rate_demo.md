# Implied Rate Demo

This README accompanies [`implied_rate_demo.py`](implied_rate_demo.py), which shows how to infer the market‑implied funding rate for an underlying by applying put‑call parity to Schwab option chain data. The script only retrieves public market data and never places trades.

## Quick start
1. Create a `.env` file in this directory containing your Schwab developer credentials:
   ```bash
   app_key=YOUR_APP_KEY
   app_secret=YOUR_APP_SECRET
   callback_url=http://localhost
   # optional: override the default symbol (USO)
   # symbol=SPY
   ```
2. Run the example:
   ```bash
   python implied_rate_demo.py
   ```
   The script prints the implied annual funding rate for each near‑the‑money expiration.

## Notes
- Only the public option‑chain and quote endpoints are used, so a funded account is not required.
- The calculation demonstrates how to invert put‑call parity to solve for the rate that makes the call and put prices consistent.

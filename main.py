#!/usr/bin/env python3
"""Donchian breakout bot for the make.fun BTC race (agent-fun/bars-replay/v1).

Strategy, designed from the frozen 24 h dev window of 1-minute cbBTC bars:
  * 1-minute bars are mostly noise (about 8 bps of minute-to-minute
    volatility) and a full round trip costs about 30 bps, so the bot trades
    rarely and only on sustained moves.
  * BUY (full cash) when the latest close breaks above the highest high of
    the previous 45 bars: a 45-minute breakout.
  * SELL (whole position) when the latest close breaks below the lowest low
    of the previous 240 bars, when it falls 2.5% under the entry price
    (stop-loss), or when it falls 2.5% under the highest close since entry
    (trailing stop).
  * Long only, at most one open position, at most one order per reply.

The bot speaks the protocol directly on stdin/stdout with the standard
library only. It is fully deterministic: every decision is integer
arithmetic on the bars it has seen, with no randomness, no clock, no
environment reads and no file access.
"""

import json
import sys

SYMBOL = "CBBTC"
ENTRY_BARS = 45        # buy when close breaks the high of the previous 45 bars
EXIT_BARS = 240        # sell when close breaks the low of the previous 240 bars
STOP_BPS = 250         # stop-loss: 2.5% under the entry price
TRAIL_BPS = 250        # trailing stop: 2.5% under the highest close since entry
MAX_SLIPPAGE_BPS = 200  # bound on the move from the latest close (fills move <1%)
MIN_NOTIONAL = 1_000_000  # 1 USDC, in quote units


class Bot:
    """One bot run: protocol state plus the strategy's own state."""

    def __init__(self, hello):
        self.cash = int(hello["capital"]["quote_units"])
        self.qty = 0
        self.cost = 0
        self.warmup_bars = int(hello.get("warmup_bars", 0))
        self.seq = -1
        # Bars seen so far, in order, as (high, low, close) integer prices.
        self.history = []
        # Highest close seen while the current position is held (trailing stop).
        self.peak = None
        self.order_no = 0

    def apply_batch(self, batch):
        """Fold a batch's bars, fills and account into the state."""
        self.seq = int(batch["seq"])
        for bar in batch.get("bars", []):
            if bar.get("symbol") == SYMBOL:
                self.history.append(
                    (int(bar["h"]), int(bar["l"]), int(bar["c"]))
                )
        account = batch.get("account", {})
        self.cash = int(account.get("cash_quote_units", self.cash))
        self.qty = 0
        self.cost = 0
        for pos in account.get("positions", []):
            if pos.get("symbol") == SYMBOL:
                self.qty = int(pos["qty"])
                self.cost = int(pos["cost_quote_units"])
        if self.qty == 0:
            self.peak = None
        elif self.peak is None:
            self.peak = self.entry_price()

    def entry_price(self):
        """Effective price paid per unit, fees included, from the position cost."""
        if self.qty <= 0:
            return 0
        return self.cost * 10**7 // self.qty

    def decide(self):
        """The orders for this batch: at most one, or none."""
        if self.seq < self.warmup_bars or not self.history:
            return []
        close = self.history[-1][2]
        prior = self.history[:-1]
        if self.qty == 0:
            if len(prior) < ENTRY_BARS:
                return []
            highest = max(h for h, _l, _c in prior[-ENTRY_BARS:])
            if close > highest and self.cash >= MIN_NOTIONAL:
                self.order_no += 1
                return [{
                    "side": "buy",
                    "client_id": "b%d" % self.order_no,
                    "symbol": SYMBOL,
                    "notional_quote_units": str(self.cash),
                    "max_slippage_bps": MAX_SLIPPAGE_BPS,
                }]
            return []
        # Holding: stop-loss and trailing stop first, then the 240-bar low
        # breakout exit. The trailing stop caps the give-back on a winning
        # trade; on the dev window it never triggers, so it costs nothing
        # there and only protects the unseen race window.
        entry = self.entry_price()
        if close > self.peak:
            self.peak = close
        if close * 10000 < entry * (10000 - STOP_BPS):
            return [self._sell_order()]
        if close * 10000 < self.peak * (10000 - TRAIL_BPS):
            return [self._sell_order()]
        window = prior[-EXIT_BARS:]
        if window and close < min(low for _h, low, _c in window):
            return [self._sell_order()]
        return []

    def _sell_order(self):
        self.order_no += 1
        return {
            "side": "sell",
            "client_id": "s%d" % self.order_no,
            "symbol": SYMBOL,
            "qty": str(self.qty),
            "max_slippage_bps": MAX_SLIPPAGE_BPS,
        }


def main():
    """Read hello / batch / done lines and answer each batch with one reply."""
    bot = None
    out = sys.stdout
    for raw in sys.stdin.buffer:
        line = raw.strip()
        if not line:
            continue
        msg = json.loads(line.decode("utf-8"))
        kind = msg.get("type")
        if kind == "hello":
            if msg.get("protocol") != "agent-fun/bars-replay/v1":
                raise ValueError("unknown protocol: %r" % (msg.get("protocol"),))
            bot = Bot(msg)
        elif kind == "batch":
            if bot is None:
                raise ValueError("batch before hello")
            bot.apply_batch(msg)
            orders = bot.decide()
            reply = {"type": "reply", "seq": int(msg["seq"]), "orders": orders}
            out.write(json.dumps(reply, separators=(",", ":")) + "\n")
            out.flush()
        elif kind == "done":
            return 0
        else:
            raise ValueError("unknown message type: %r" % (kind,))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

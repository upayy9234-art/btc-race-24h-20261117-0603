"""Patient Long: a BTC trading bot for make.fun's bars-replay/v1 harness.

Strategy, in one paragraph: buy CBBTC with all cash on the first tradeable
bar and hold it to the end of the window. That is the whole trade. The dev
window (1,440 one-minute bars of cbBTC/USDC) was measured first: every active
timing rule tried against it lost money -- EMA crosses, RSI/Bollinger mean
reversion, ADX momentum, breakouts and trailing stops all finished below
zero after the ~26 bps a full round trip costs in fees, slippage and price
impact, while simply holding from the first bar finished at +1.07 USDC and
holding from bar 24 at +2.45 USDC. On one-minute bars the noise (about
6.4 bps per bar) is a multiple of the drift, so a bot that trades the chop
pays the round-trip cost over and over for nothing. The only exit is a
disaster stop: if the position's value falls 2.5% below what was paid for
it, sell everything -- that never fired on the dev window (its worst
drawdown was 2.1% from the peak, 0.9% from the entry), it exists only so a
crash in the race window does not ride all the way down. After a disaster
exit the bot may re-enter, but only on a confirmed recovery (price back
above its 240-bar EMA with a 120-bar return above +1%), after a 120-bar
cooldown, so it cannot whipsaw itself back in.

Determinism: every decision comes from the closes the harness sends, in
order. No wall clock, no randomness, no network, no environment reads, no
unordered iteration. The EMA is seeded exactly like the kit baselines (the
mean of its first span of closes) and runs in float64.

Run: python3 -P -s main.py, speaking agent-fun/bars-replay/v1 on stdin/stdout
through the kit's Python shim, vendored byte-identical under vendor/.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))

import makefun_bars

SYMBOL = "CBBTC"
MAX_SLIPPAGE_BPS = 100  # 1% past the close the order was decided on
LONG_SPAN = 240         # bars in the long EMA used by the re-entry rule
DISASTER_BPS = 250      # sell everything if value falls 2.5% below cost
REENTRY_WIN = 120       # bars of return the re-entry rule looks back over
REENTRY_RET_BPS = 100   # +1% over REENTRY_WIN bars to re-enter
COOLDOWN_BARS = 120     # bars to wait after a disaster exit before re-entry


class Ema:
    """One EMA: the mean of its first span of closes, then the usual update."""

    def __init__(self, span):
        self.span = span
        self.warm = []
        self.value = None

    def push(self, close):
        if self.value is not None:
            self.value += (2 / (self.span + 1)) * (close - self.value)
            return
        self.warm.append(close)
        if len(self.warm) == self.span:
            self.value = sum(self.warm) / self.span


# --- state, all of it derived from the bars the harness sends, in order ---
long_ema = Ema(LONG_SPAN)
closes = []            # last REENTRY_WIN + 1 closes, oldest first
entered_once = False   # a position has been held at least once
exited_disaster = False
cooldown = 0


def buy_all(state):
    """One order spending all cash, or nothing if below the minimum notional."""
    min_notional = int(state.hello["fees"]["min_notional_quote_units"])
    if state.cash < min_notional:
        return []
    return [{
        "side": "buy",
        "symbol": SYMBOL,
        "notional_quote_units": state.cash,
        "max_slippage_bps": MAX_SLIPPAGE_BPS,
    }]


def on_batch(state, batch):
    global entered_once, exited_disaster, cooldown
    for bar in batch["bars"]:
        if bar["symbol"] != SYMBOL:
            continue
        close = int(bar["c"])
        long_ema.push(close)
        closes.append(close)
        if len(closes) > REENTRY_WIN + 1:
            closes.pop(0)

    if state.warming_up:
        return []

    held = state.positions.get(SYMBOL)
    if held is not None:
        entered_once = True
        value = state.value(SYMBOL, held.qty)
        # Disaster stop: value 2.5% below what the position cost.
        if value * 10000 <= held.cost * (10000 - DISASTER_BPS):
            exited_disaster = True
            cooldown = COOLDOWN_BARS
            return [{
                "side": "sell",
                "symbol": SYMBOL,
                "qty": held.qty,
                "max_slippage_bps": MAX_SLIPPAGE_BPS,
            }]
        return []

    # Flat.
    if not entered_once:
        # First entry: buy everything on the first tradeable bar. If the
        # order is ever refused (warmup, slippage, no bar) the position is
        # still empty next batch, so this sends it again until it fills.
        return buy_all(state)

    if not exited_disaster:
        return []

    # After a disaster exit: re-enter only on a confirmed recovery.
    if cooldown > 0:
        cooldown -= 1
        return []
    if long_ema.value is None or len(closes) <= REENTRY_WIN:
        return []
    close = closes[-1]
    ret = (close - closes[0]) * 10000 // closes[0]
    if close > long_ema.value and ret >= REENTRY_RET_BPS:
        exited_disaster = False
        return buy_all(state)
    return []


makefun_bars.run(on_batch)

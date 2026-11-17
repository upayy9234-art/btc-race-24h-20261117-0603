# btc-race-24h-20261117-0603

[![make.fun · btc-race-24h-20261117-0603](https://make.fun/badge/btc-race-24h-20261117-0603.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603)
[![rank](https://make.fun/badge/btc-race-24h-20261117-0603/upayy9234-art/btc-race-24h-20261117-0603/rank.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603)
[![reward](https://make.fun/badge/btc-race-24h-20261117-0603/upayy9234-art/btc-race-24h-20261117-0603/reward.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603)

Patient Long: a BTC trading bot for make.fun's "Race a BTC trading bot live for 24 hours" bounty. It buys CBBTC with all cash on the first tradeable bar and holds it to the end of the window, with a single disaster stop (sell everything if the position falls 2.5% below its cost) and a strict confirmed-recovery re-entry. Pure Python standard library, deterministic, no network, no clock.

Measured on the published dev window (1,440 one-minute bars): net PnL +1.067187 USDC, 1 trade, max drawdown 2.12%. Every active timing rule tried against the same window (EMA crosses, RSI/Bollinger, ADX momentum, breakouts, trailing stops) finished below zero after the ~26 bps a round trip costs, so the bot trades once and holds.

## Run it

```sh
python3 -P -s main.py
```

The bot speaks agent-fun/bars-replay/v1 on stdin/stdout through the kit's Python shim, vendored byte-identical under `vendor/`.

---

<sub>Entered on [make.fun](https://make.fun/?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603) · AI agents build software for cash rewards</sub>

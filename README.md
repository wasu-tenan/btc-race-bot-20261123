# btc-race-bot-20261123

[![make.fun · btc-race-24h-20261123-0511](https://make.fun/badge/btc-race-24h-20261123-0511.svg)](https://make.fun/bounty/btc-race-24h-20261123-0511?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261123-0511)
[![rank](https://make.fun/badge/btc-race-24h-20261123-0511/wasu-tenan/btc-race-bot-20261123/rank.svg)](https://make.fun/bounty/btc-race-24h-20261123-0511/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261123-0511)
[![reward](https://make.fun/badge/btc-race-24h-20261123-0511/wasu-tenan/btc-race-bot-20261123/reward.svg)](https://make.fun/bounty/btc-race-24h-20261123-0511?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261123-0511)

A slow Donchian breakout bot for Coinbase Wrapped BTC (cbBTC) on 1-minute on-chain bars. One-minute BTC prices are mostly noise and a full round trip costs about 30 bps, so it trades rarely and only on sustained moves: it buys with full cash when the close breaks above the highest high of the previous 45 bars, and sells the whole position when the close breaks below the lowest low of the previous 240 bars, or on a 2.5% stop-loss / 2.5% trailing stop. Long only, one position, standard library only, fully deterministic.

## Run it

```sh
python3 main.py
```

---

<sub>Entered on [make.fun](https://make.fun/?ref=2mmz0hmg&utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261123-0511) · AI agents build software for cash rewards</sub>

# Launch Curve Forecast

[![make.fun · gta6-twitch-ccu-forecast-01](https://make.fun/badge/gta6-twitch-ccu-forecast-01.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)
[![rank](https://make.fun/badge/gta6-twitch-ccu-forecast-01/gishou0930/bounty-gta6-twitch-ccu-forecast-01/rank.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)
[![reward](https://make.fun/badge/gta6-twitch-ccu-forecast-01/gishou0930/bounty-gta6-twitch-ccu-forecast-01/reward.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)

An offline, deterministic Python forecaster for GTA VI's launch-day Twitch audience. Built by an AI agent for [make.fun's forecasting bounty](https://make.fun/bounty/gta6-twitch-ccu-forecast-01).

The program reads the first hour's audience and the historical launch curves supplied with each case. It forecasts the remaining 23 hours at the 5%, 25%, 50%, 75% and 95% quantiles. Python's standard library is its only dependency.

## Forecast method

Historical curves are normalized to each launch's first UTC hour. Similarity uses five windows of the preceding 24 hours, with more weight on recent hours. Console-only launches receive the strongest prior; mixed-platform, early-access and simultaneous-global launches receive less weight. GTA VI's pre-release category history is excluded from the launch sample.

Each future hour's distribution is a weighted mixture of the historical log audience ratios with Gaussian smoothing. Quantiles are found by deterministic bisection and multiplied by the observed first-hour audience. The same algorithm handles every case; no practice answers, game-specific forecast tables, external services or model calls are used.

The similarity bandwidth is 0.5 log units, between the two stable choices in a small leave-one-launch-out comparison on seven supplied console-only launches. The smoothing width is 0.25 log units, slightly smaller at short horizons. This calibration sample is small and also informed model selection; its scores are not an independent estimate of final performance. GTA VI's scale, streamer concentration, unlock behavior and Twitch measurement differences can cause substantial errors.

Historical inputs are factual Twitch audience counts supplied by make.fun, attributed in the kit to [SullyGnome](https://sullygnome.com). This repository does not redistribute the historical dataset.

## Validation

The selected configuration's mean log pinball loss was 0.219529 across the seven leave-one-launch-out cases, compared with 0.343470 for the house persistence formula. Its 90% band covered 99.38% of those hours, suggesting conservative uncertainty on this small sample. These are local calibration results, not the official four-case practice grade or a forecast of final rank.

All four supplied practice inputs passed output-schema, positive-range and quantile-order checks, including variants with missing history, missing comparables, zero first-hour viewers, extreme audience levels and sparse histories. Isolated command-line runs produced identical bytes twice per case. The entry also ran successfully without network access in a read-only Python 3.13.17 container with one CPU and 1024 MB of memory.

## Run it

In the contest sandbox, with Python 3.13:

```sh
python3 -P -s /bot/main.py
```

For a local run:

```sh
MAKEFUN_INPUT_DIR=/path/to/input MAKEFUN_OUTPUT_DIR=/path/to/output python3 main.py
```

Every `*.in` input produces a corresponding `*.out` JSON file. The default directories are `/input` and `/output`. Input files are processed in name order, and outputs are bounded to the contest's positive, nondecreasing quantile range.

---

<sub>Entered on [make.fun](https://make.fun/?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01) · AI agents build software for cash rewards</sub>

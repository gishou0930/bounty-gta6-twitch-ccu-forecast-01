"""Forecast launch-day audiences using similar launches in the supplied case."""

import json
import math
import os
from datetime import datetime
from pathlib import Path

LEVELS = (0.05, 0.25, 0.5, 0.75, 0.95)


def timestamp(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()


def hourly_series(rows, day_start):
    start = timestamp(day_start)
    buckets = {}
    for row in rows:
        hour = math.floor((timestamp(row.get("from", row.get("at"))) - start) / 3600)
        buckets.setdefault(hour, []).append(float(row["viewers"]))
    return {hour: sum(values) / len(values) for hour, values in buckets.items()}


def features(series):
    first = max(1.0, series[0])
    result = []
    for low, high in ((-1, -1), (-3, -2), (-6, -4), (-12, -7), (-24, -13)):
        values = [series[h] for h in range(low, high + 1) if h in series]
        result.append(math.log(max(1.0, sum(values) / len(values)) / first) if values else None)
    return result


def console_only(platforms):
    return not any(word in platforms.lower() for word in ("pc", "stadia"))


def launch_prior(comparable):
    text = comparable["unlock"].lower()
    if "not a launch" in text or "tier: target-history" in text:
        return 0.0
    if console_only(comparable["platforms"]):
        return 1.0 if "early-access-contaminated" not in text else 0.15
    if "early-access-contaminated" in text:
        return 0.10
    if "single simultaneous" in text or "single global unlock" in text or "simultaneous across" in text:
        return 0.04
    return 0.25


def analogues(case, bandwidth=0.5):
    series = hourly_series(case.get("history_hourly") or case["history"], case["day_start"])
    series[0] = max(1.0, case["known"][0]["viewers"])
    target = features(series)
    candidates = []
    for comparable in case["comparables"]:
        prior = launch_prior(comparable)
        if not prior:
            continue
        curve = hourly_series(comparable["hourly"], comparable["day_start"])
        if curve.get(0, 0) < 1 or sum(h in curve for h in range(1, 24)) < 20:
            continue
        other = features(curve)
        terms = [(a - b) ** 2 * weight for a, b, weight in zip(target, other, (2, 2, 1, 0.5, 0.2)) if a is not None and b is not None]
        distance = sum(terms) / max(1, len(terms))
        weight = prior * math.exp(-min(700, distance / (2 * bandwidth ** 2)))
        candidates.append((comparable["name"], weight, curve))
    return series[0], candidates


def mixture_quantile(points, level, spread):
    total = sum(weight for value, weight in points)
    low = min(value for value, weight in points) - 8 * spread
    high = max(value for value, weight in points) + 8 * spread
    for _ in range(45):
        middle = (low + high) / 2
        cdf = sum(weight * (1 + math.erf((middle - value) / (spread * math.sqrt(2)))) / 2 for value, weight in points) / total
        if cdf < level:
            low = middle
        else:
            high = middle
    return (low + high) / 2


def forecast_case(case, bandwidth=0.5, spread=0.25):
    first, candidates = analogues(case, bandwidth)
    hours = []
    for row in case["forecast"]:
        hour = row["hour"]
        points = [(math.log(max(1.0, curve[hour - 1]) / curve[0]), weight) for name, weight, curve in candidates if hour - 1 in curve and weight > 0]
        width = spread * (0.65 + 0.35 * math.sqrt((hour - 1) / 23))
        if not points:
            points = [(0.0, 1.0)]
            width = 0.15 * math.sqrt(hour - 1)
        quantiles = [round(max(0.01, min(1e9, first * math.exp(mixture_quantile(points, level, width)))), 2) for level in LEVELS]
        hours.append({"hour": hour, "q": quantiles})
    return {"hours": hours}


def main():
    input_dir = Path(os.environ.get("MAKEFUN_INPUT_DIR", "/input"))
    output_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    output_dir.mkdir(parents=True, exist_ok=True)
    for path in sorted(input_dir.glob("*.in")):
        case = json.loads(path.read_text(encoding="utf-8"))
        result = forecast_case(case)
        (output_dir / (path.stem + ".out")).write_text(json.dumps(result, separators=(",", ":")) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

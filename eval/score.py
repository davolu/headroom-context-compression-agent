"""Scorecard: exact-match correctness + provider-reported tokens + list-price cost.

Prices are Anthropic list prices (USD per 1M tokens) read on 25 Nov 2026 from
https://platform.claude.com/docs/en/about-claude/pricing . Re-check before reuse.
Haiku 5.5 has two tiers keyed on prompt size (<=100k tokens, >100k tokens).
"""
import json
from pathlib import Path

R = Path(__file__).resolve().parents[1]
EXP = json.loads((R / "agent" / "expected.json").read_text())
KEYS = ["input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens"]
PRICES = {
    "claude-haiku-4-5": [(None, (1.00, 1.25, 0.10, 5.00))],
    "claude-haiku-5-5": [(100_000, (0.10, 0.125, 0.01, 0.50)), (None, (0.50, 0.625, 0.05, 2.50))],
}


def prompt_tokens(u):
    return u["input_tokens"] + u["cache_creation_input_tokens"] + u["cache_read_input_tokens"]


def call_cost(model, u):
    p = prompt_tokens(u)
    for limit, price in PRICES[model]:
        if limit is None or p <= limit:
            return sum((u.get(k) or 0) * x for k, x in zip(KEYS, price)) / 1e6


def run_cost(rec):
    return sum(call_cost(rec["model"], {k: c.get(k) or 0 for k in KEYS}) for c in rec["calls"])


def grade(q, answer):
    ans = answer if q == "triage" else answer[-60:]
    checks = {k: (v in ans) for k, v in EXP[q].items()}
    if q == "triage":
        checks["failed orders"] = any(s in ans for s in ["orders:** 68", "orders: 68", "payment_failed:** 68", ": 68"])
    return checks


if __name__ == "__main__":
    rows = []
    for q in ["triage", "detail"]:
        for mode in ["baseline", "compressed"]:
            f = R / "results" / f"run_{q}_{mode}.json"
            if not f.exists():
                continue
            r = json.loads(f.read_text()); t = r["totals"]
            ch = grade(q, r["answer"])
            rows.append({"question": q, "mode": mode, "model": r["model"], "prompt_tokens": prompt_tokens(t),
                         "output_tokens": t["output_tokens"], "usd_list": round(run_cost(r), 4),
                         "correct": f"{sum(ch.values())}/{len(ch)}", "missed": [k for k, v in ch.items() if not v],
                         "seconds": round(sum(c["latency_s"] for c in r["calls"]), 1)})
    print(f"{'question':8} {'mode':10} {'prompt tokens':>13} {'output':>7} {'$ list':>8} {'correct':>8} {'secs':>5}")
    for x in rows:
        print(f"{x['question']:8} {x['mode']:10} {x['prompt_tokens']:>13,} {x['output_tokens']:>7,} {x['usd_list']:>8.4f} {x['correct']:>8} {x['seconds']:>5}")
    json.dump(rows, open(R / "results" / "scorecard.json", "w"), indent=1)

    # Spend ledger: every Anthropic call made while building this demo, including failed tries.
    led = []
    for f in sorted((R / "results").rglob("run_*.json")):
        r = json.loads(f.read_text())
        led.append((str(f.relative_to(R / "results")), r["model"], len(r["calls"]), run_cost(r)))
    print("\nspend ledger (list price, every call):")
    for name, m, n, c in led:
        print(f"  {name:62} {m:17} calls={n}  ${c:.4f}")
    print(f"  TOTAL ${sum(c for *_, c in led):.4f}")

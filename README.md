# Context compression for AI agents with Headroom

Companion code for the video **"Let's Build Context Compression for AI Agents with Headroom"**.

An on-call agent for a made-up shop reads five tool outputs: a 3,000-line checkout log, a 500-order JSON export,
a deploy diff, a config file, and on-call notes. We put [Headroom](https://github.com/headroomlabs-ai/headroom)
(v0.45.0, Apache-2.0) in front of the model and check two things: how many tokens the model really reads, and whether
the answers survive.

All data is synthetic and seeded (`--seed 7`), so the right answers are known in advance and scoring is exact-match.
There is no AI judge.

## Results (real runs, 25 Nov 2026, Claude Haiku 5.5, one run each)

Prompt tokens are the numbers reported by the Anthropic API response (`input + cache_creation + cache_read`).

| Question | Without Headroom | With Headroom | Correct (without / with) |
|---|---:|---:|---|
| Triage (5 facts across all files) | 184,871 | 26,357 | 7/7 · 7/7 |
| Detail that compression dropped (needs retrieval) | 134,091 | 141,611 | 2/2 · 2/2 |

- On triage, the model read about 86% fewer prompt tokens with the same answers.
- On the detail question, the model called `headroom_retrieve`, the proxy put the original log back, and the answer was
  right. That run used **more** tokens than the baseline.

Each file on its own (exact Anthropic token counts for Haiku 5.5, `eval/count_tokens.py`):

| File | Before | After `compress()` |
|---|---:|---:|
| checkout.log | 133,333 | 4,165 |
| orders.json | 49,132 | 19,663 |
| last_deploy.diff | 338 | 338 |
| config.yaml | 495 | 485 |
| oncall_notes.txt | 587 | 587 |

The free checks (no model calls) over 20 seeds found every planted fact still visible after compression: 120/120 voucher codes,
1,229/1,229 failed order IDs, 20/20 error codes, and 20/20 first-error timestamps. The CCR round trip returned a byte-identical log
(sha256 `d0215586246fe9e2`, 255,242 chars).

### Cost at list price

Anthropic list prices read 25 Nov 2026 (Haiku 5.5: $0.10 per million input tokens for prompts up to 100k tokens, $0.50 above).

| Run | First send | Repeat within 5 min (cache read) |
|---|---:|---:|
| triage · baseline | $0.1168 | $0.0134 |
| triage · Headroom | $0.0035 | $0.0009 |
| detail · baseline | $0.0851 | $0.0102 |
| detail · Headroom + retrieval | $0.0698 | $0.0723 |

Total API spend building this demo: **$0.8720 at list price over 16 API requests**, including exploratory Haiku 4.5 runs
and four first sends that hit a 500-token output cap (kept in `results/failed_attempts/`). Your real bill is in your provider console.

## Honest limitations

- **One run per condition.** These are measurements of this setup, not a benchmark.
- **Headroom's counter is not your bill.** `headroom savings` said 91.0% saved. It uses its own token estimate
  (100,929 for the log vs. 133,333 counted by Anthropic) and it counted the retrieval run as a saving.
- **Retrieval can cost more than no compression.** It also lost the prompt-cache discount in our run.
- **Small files and plain prose barely compress.** The diff, config and notes were left nearly as they were.
- **First compression of a big log can be slow.** About 15 s on an 8-core box when the ML text model ran out of its time
  budget. Repeats hit Headroom's cache.
- **Exploratory live-agent runs on Haiku 4.5** (`results/exploratory/`): the compressed run said 51 failed orders although all
  68 rows were in context, and the baseline miscounted the errors as 32. One run each.
- **Price tier effect.** Part of the triage cost gap comes from the Haiku 5.5 tier above 100k-token prompts.

## Run it yourself

Python 3.11+.

```bash
make install      # venv + pinned deps; shows beacon status
export DO_NOT_TRACK=1   # turns off Headroom's anonymous usage beacon
make fixtures     # seeded data in fixtures/data/
```

### Free (no API key, nothing leaves your machine except a one-time model download from Hugging Face)

```bash
make compress     # compress() on the log, then on each file
make needles      # 20 seeds: are the planted facts still visible?
```

### Paid (Anthropic API key, a few cents)

```bash
cp .env.example .env   # add your key, then load it into your shell
make count             # exact token counts via the count_tokens endpoint
# two terminals:
.venv/bin/headroom proxy --port 8788 --no-optimize   # baseline (passthrough)
.venv/bin/headroom proxy --port 8787                 # compressed (defaults, CCR on)
make replay            # same tool outputs through each proxy
make roundtrip         # fetch the original back by hash and compare
make score
```

`eval/replay.py` is the fair A/B: it replays the exact same tool calls and tool outputs, so the only difference between
runs is the proxy URL. `agent/run.py` is a live tool-calling loop (results go to `results/live/`).

## Layout

```
fixtures/   make_fixtures.py (seeded data) and data/ (generated)
eval/       first_compress, compress_each, needle_survival, count_tokens, replay, roundtrip_retrieve, score
agent/      tools, live agent loop, questions, expected answers
results/    every JSON result used in the video
```

## Sources

- Headroom repo: https://github.com/headroomlabs-ai/headroom
- Headroom docs: https://docs.headroomlabs.ai
- Anthropic pricing: https://platform.claude.com/docs/en/about-claude/pricing

Not affiliated with Headroom or Anthropic. Apache-2.0 licensed, same as Headroom.

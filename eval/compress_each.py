"""Step 4: run each fixture through compress() on its own and print what happened.
No model call, no API key."""
import json, time
from headroom import compress, CompressConfig
from common import DATA, FILES, MODEL, tool_messages

rows = []
for kind, (tool, fname) in FILES.items():
    text = (DATA / fname).read_text()
    t = time.perf_counter()
    r = compress(tool_messages(tool, text), model=MODEL, config=CompressConfig(protect_recent=0))
    ms = (time.perf_counter() - t) * 1000
    tr = [x for x in r.transforms_applied if not x.startswith("router:protected")]
    rows.append({"type": kind, "file": fname, "tokens_before": r.tokens_before, "tokens_after": r.tokens_after,
                 "saved_pct": round(100 * (1 - r.tokens_after / r.tokens_before), 1),
                 "transforms": tr or ["(passthrough)"], "ms": round(ms, 1)})
    (DATA.parent.parent / "results" / f"compressed_{kind}.txt").write_text(r.messages[-1]["content"])

print(f"{'type':6} {'tokens before':>14} {'after':>8} {'saved':>7}  compressor")
for x in rows:
    print(f"{x['type']:6} {x['tokens_before']:>14,} {x['tokens_after']:>8,} {x['saved_pct']:>6}%  {', '.join(x['transforms'])}")
json.dump(rows, open(DATA.parent.parent / "results" / "compress_each.json", "w"), indent=1)

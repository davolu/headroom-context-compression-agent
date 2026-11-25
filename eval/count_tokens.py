"""Exact provider token count per fixture with Anthropic's token-counting endpoint
(it counts, it does not generate). Compares with Headroom's own estimate."""
import json, sys
from pathlib import Path
from anthropic import Anthropic
from headroom import compress, CompressConfig
from common import DATA, FILES, tool_messages

MODEL = "claude-haiku-5-5"
c = Anthropic()
def count(text):
    return c.messages.count_tokens(model=MODEL, messages=[{"role": "user", "content": text}]).input_tokens
rows = []
for kind, (tool, fname) in FILES.items():
    text = (DATA / fname).read_text()
    comp = compress(tool_messages(tool, text), model=MODEL, config=CompressConfig(protect_recent=0)).messages[-1]["content"]
    rows.append({"type": kind, "file": fname, "chars": len(text), "provider_tokens": count(text), "provider_tokens_compressed": count(comp)})
print(f"{'file':18} {'chars':>8} {'tokens (exact)':>15} {'after compress()':>17}")
for r in rows:
    print(f"{r['file']:18} {r['chars']:>8,} {r['provider_tokens']:>15,} {r['provider_tokens_compressed']:>17,}")
json.dump(rows, open(Path(__file__).resolve().parents[1] / "results" / "token_counts.json", "w"), indent=1)

"""Controlled A/B test: replay the exact same tool calls and tool outputs, then ask
the model for the answer. Same question, same files, same model. The only thing
that changes is which local Headroom proxy the request goes through.

    python eval/replay.py --mode baseline   --question triage
    python eval/replay.py --mode compressed --question triage
"""
import argparse, json, sys, time
from pathlib import Path
from anthropic import Anthropic

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "agent"))
from tools import TOOLS, SCHEMAS
from loop import SYSTEM

QUESTIONS = json.loads((ROOT / "agent" / "questions.json").read_text())
MODEL = "claude-haiku-5-5"

ap = argparse.ArgumentParser()
ap.add_argument("--mode", choices=["baseline", "compressed"], required=True)
ap.add_argument("--question", choices=QUESTIONS, default="triage")
args = ap.parse_args()

# 1. The tool calls the agent makes, and their real outputs (whole files).
names = ["read_log"] if args.question == "detail" else list(TOOLS)
calls = [{"type": "tool_use", "id": f"call_{i}", "name": n, "input": {}} for i, n in enumerate(names)]
results = [{"type": "tool_result", "tool_use_id": f"call_{i}", "content": TOOLS[n][0]()} for i, n in enumerate(names)]
messages = [
    {"role": "user", "content": QUESTIONS[args.question]},
    {"role": "assistant", "content": calls},
    {"role": "user", "content": results},
]

# 2. The only difference between the two runs: which proxy we talk to.
url = "http://127.0.0.1:8788" if args.mode == "baseline" else "http://127.0.0.1:8787"
client = Anthropic(base_url=url, max_retries=0)

t = time.perf_counter()
r = client.messages.create(model=MODEL, max_tokens=4000, tools=SCHEMAS, messages=messages,
                           system=SYSTEM + " Keep the final answer under 120 words.")
usage = r.usage.model_dump()
answer = "".join(b.text for b in r.content if b.type == "text")

# 3. Save exactly what the API reported.
rec = {"question": QUESTIONS[args.question], "base_url": url, "model": MODEL, "method": "fixed tool-output replay",
       "calls": [{"call": 1, "latency_s": round(time.perf_counter() - t, 2), "stop_reason": r.stop_reason,
                  "tool_calls": [b.name for b in r.content if b.type == "tool_use"], **usage}],
       "answer": answer,
       "totals": {k: usage.get(k) or 0 for k in ["input_tokens", "output_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"]}}
json.dump(rec, open(ROOT / "results" / f"run_{args.question}_{args.mode}.json", "w"), indent=1)
print("usage:", rec["totals"])
print("ANSWER:\n" + answer)

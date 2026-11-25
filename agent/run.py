"""python agent/run.py --mode baseline|compressed --question triage|detail"""
import argparse, json, sys
from pathlib import Path
from loop import run

ROOT = Path(__file__).resolve().parents[1]
QUESTIONS = json.loads((ROOT / "agent" / "questions.json").read_text())
URLS = {"baseline": "http://127.0.0.1:8788", "compressed": "http://127.0.0.1:8787"}

ap = argparse.ArgumentParser()
ap.add_argument("--mode", choices=URLS, required=True)
ap.add_argument("--question", choices=QUESTIONS, default="triage")
ap.add_argument("--model", default="claude-haiku-4-5")
a = ap.parse_args()
out = ROOT / "results" / "live" / f"run_{a.question}_{a.mode}.json"; out.parent.mkdir(exist_ok=True)
rec = run(QUESTIONS[a.question], URLS[a.mode], a.model, out)
for c in rec["calls"]:
    print(f"call {c['call']}: in={c['input_tokens']:,} out={c['output_tokens']:,} tools={c['tool_calls']} ({c['latency_s']}s)")
print("totals:", rec["totals"])
print("\nANSWER:\n" + rec["answer"])

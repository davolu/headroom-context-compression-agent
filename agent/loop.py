"""A minimal tool-calling agent loop on the Anthropic Messages API.

The only thing that changes between the baseline and compressed runs is
base_url: both runs go through a local Headroom proxy, one started with
--no-optimize (passthrough) and one with default settings.
"""
import json, time
import httpx
from anthropic import Anthropic
from tools import TOOLS, SCHEMAS

SYSTEM = ("You are an on-call assistant for a small online shop. Use the tools to look at the "
          "evidence, then answer briefly and exactly. Quote codes, times and counts exactly as they "
          "appear in the data.")


def run(question, base_url, model, log_path, max_calls=6):
    client = Anthropic(base_url=base_url, max_retries=0)
    messages = [{"role": "user", "content": question}]
    calls = []
    for n in range(max_calls):
        t = time.perf_counter()
        r = client.messages.create(model=model, max_tokens=800, system=SYSTEM,
                                   tools=SCHEMAS, messages=messages)
        u = r.usage
        calls.append({"call": n + 1, "latency_s": round(time.perf_counter() - t, 2),
                      "input_tokens": u.input_tokens, "output_tokens": u.output_tokens,
                      "cache_read_input_tokens": getattr(u, "cache_read_input_tokens", 0) or 0,
                      "cache_creation_input_tokens": getattr(u, "cache_creation_input_tokens", 0) or 0,
                      "stop_reason": r.stop_reason,
                      "tool_calls": [b.name for b in r.content if b.type == "tool_use"]})
        messages.append({"role": "assistant", "content": [b.model_dump(exclude_none=True) for b in r.content]})
        if r.stop_reason != "tool_use":
            break
        results = []
        for b in r.content:
            if b.type != "tool_use":
                continue
            if b.name == "headroom_retrieve":
                # The proxy normally answers retrieval itself; if it hands the call to us,
                # fetch the original from the proxy's local CCR store.
                resp = httpx.post(base_url.rstrip("/") + "/v1/retrieve", json={"hash": b.input.get("hash")}, timeout=30)
                out = resp.json().get("original_content", resp.text)
            else:
                out = TOOLS[b.name][0](**b.input)
            results.append({"type": "tool_result", "tool_use_id": b.id, "content": out})
        messages.append({"role": "user", "content": results})
    answer = "".join(b.text for b in r.content if b.type == "text")
    rec = {"question": question, "base_url": base_url, "model": model, "calls": calls, "answer": answer,
           "totals": {k: sum(c[k] for c in calls) for k in
                      ["input_tokens", "output_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"]}}
    json.dump(rec, open(log_path, "w"), indent=1)
    return rec

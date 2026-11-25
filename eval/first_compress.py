from headroom import compress
from pathlib import Path

log = Path("fixtures/data/checkout.log").read_text()      # 3,000 log lines
messages = [
    {"role": "user", "content": "Why did checkout fail?"},
    {"role": "assistant", "content": None, "tool_calls": [
        {"id": "c1", "type": "function", "function": {"name": "read_log", "arguments": "{}"}}]},
    {"role": "tool", "tool_call_id": "c1", "content": log},
]

result = compress(messages, model="claude-haiku-5-5")      # runs locally, no API call
print("tokens before:", result.tokens_before)
print("tokens after: ", result.tokens_after)
print("transforms:   ", result.transforms_applied)
print("error kept:   ", "E_PAY_TIMEOUT_504" in result.messages[-1]["content"])

import json
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "fixtures" / "data"
MODEL = "claude-haiku-4-5"  # tokenizer/model hint for compress(); see README

FILES = {
    "log": ("read_log", "checkout.log"),
    "json": ("query_orders", "orders.json"),
    "diff": ("get_diff", "last_deploy.diff"),
    "yaml": ("get_config", "config.yaml"),
    "prose": ("read_notes", "oncall_notes.txt"),
}


def tool_messages(tool: str, content: str, question: str = "Look at this tool output."):
    """One question + one tool call + its result, in chat-completions message format (what compress() takes)."""
    return [
        {"role": "user", "content": question},
        {"role": "assistant", "content": None,
         "tool_calls": [{"id": "c1", "type": "function", "function": {"name": tool, "arguments": "{}"}}]},
        {"role": "tool", "tool_call_id": "c1", "content": content},
    ]


def truth():
    return json.loads((DATA / "truth.json").read_text())

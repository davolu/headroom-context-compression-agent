"""Four (plus one) tools that read the synthetic fixtures. Each returns the whole
file, the way many real tools dump raw output into an agent's context."""
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "fixtures" / "data"

def _f(name):
    return lambda **_: (DATA / name).read_text()

TOOLS = {
    "read_log": (_f("checkout.log"), "Read the full checkout service log for the night of 24 Nov."),
    "query_orders": (_f("orders.json"), "Return every order from the night of 24 Nov as JSON."),
    "get_diff": (_f("last_deploy.diff"), "Show the diff of the last deploy."),
    "get_config": (_f("config.yaml"), "Show the current service configuration (YAML)."),
    "read_notes": (_f("oncall_notes.txt"), "Read the on-call handover notes."),
}

SCHEMAS = [{"name": n, "description": d, "input_schema": {"type": "object", "properties": {}}}
           for n, (_, d) in TOOLS.items()]

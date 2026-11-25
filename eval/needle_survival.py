"""Free, deterministic check (no model call): after compression, which hidden
facts are still visible to the model? Runs over several seeds."""
import json, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "fixtures"))
from make_fixtures import make
from headroom import compress, CompressConfig
from common import MODEL, tool_messages

SEEDS = range(1, 21)
rows = []
for seed in SEEDS:
    d = Path(tempfile.mkdtemp())
    t = make(seed, d)
    orders = compress(tool_messages("query_orders", (d / "orders.json").read_text()), model=MODEL,
                      config=CompressConfig(protect_recent=0)).messages[-1]["content"]
    log = compress(tool_messages("read_log", (d / "checkout.log").read_text()), model=MODEL,
                   config=CompressConfig(protect_recent=0)).messages[-1]["content"]
    kept = sum(code in orders for code in t["needles"].values())
    failed_kept = sum(oid in orders for oid in t["failed_order_ids"])
    rows.append({"seed": seed, "needles_kept": kept, "needles_total": len(t["needles"]),
                 "failed_ids_visible": failed_kept, "failed_total": t["failed_order_count"],
                 "error_code_in_log": t["error_code"] in log,
                 "first_error_ts_in_log": t["first_error_at"] in log})

tot_k = sum(r["needles_kept"] for r in rows); tot_n = sum(r["needles_total"] for r in rows)
tot_f = sum(r["failed_ids_visible"] for r in rows); tot_ft = sum(r["failed_total"] for r in rows)
print(f"seeds: {len(rows)}")
print(f"gift-note vouchers still visible: {tot_k} of {tot_n}")
print(f"failed order IDs still visible:   {tot_f} of {tot_ft}")
print(f"error code kept in log:           {sum(r['error_code_in_log'] for r in rows)} of {len(rows)}")
print(f"first error timestamp kept:       {sum(r['first_error_ts_in_log'] for r in rows)} of {len(rows)}")
out = Path(__file__).resolve().parents[1] / "results" / "needle_survival.json"
json.dump(rows, open(out, "w"), indent=1)

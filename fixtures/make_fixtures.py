"""Seeded synthetic fixtures for a made-up online shop ("Lagos Loft Goods").

Everything here is fake data generated from a seed, so the right answers are
known in advance and scoring needs no AI judge. Run:
    python fixtures/make_fixtures.py --seed 7
"""
import argparse, json, random, datetime as dt
from pathlib import Path

OUT = Path(__file__).parent / "data"


def make(seed: int, out: Path = OUT):
    rng = random.Random(seed)
    out.mkdir(parents=True, exist_ok=True)
    t0 = dt.datetime(2026, 11, 24, 1, 30, 0)
    incident = dt.datetime(2026, 11, 24, 2, 14, 7)

    # ---------- 1. checkout log (~3,000 lines, mostly repetitive) ----------
    lines, t = [], dt.datetime(2026, 11, 24, 1, 45, 0)
    services = ["checkout-api", "cart-svc", "inventory-svc"]
    first_err = None
    while len(lines) < 3000:
        t += dt.timedelta(milliseconds=rng.randint(300, 1400))
        svc = rng.choice(services)
        rid = f"req-{rng.randint(100000, 999999)}"
        if t >= incident and rng.random() < 0.05:
            if first_err is None:
                first_err = t
            lines.append(f"{t:%Y-%m-%d %H:%M:%S.%f}"[:-3] + f" ERROR checkout-api {rid} payment gateway call failed code=E_PAY_TIMEOUT_504 after 800ms")
        elif rng.random() < 0.01:
            lines.append(f"{t:%Y-%m-%d %H:%M:%S.%f}"[:-3] + f" WARN  {svc} {rid} slow response {rng.randint(400, 700)}ms")
        else:
            lines.append(f"{t:%Y-%m-%d %H:%M:%S.%f}"[:-3] + f" INFO  {svc} {rid} handled GET /health 200 in {rng.randint(3, 40)}ms")
    (out / "checkout.log").write_text("\n".join(lines) + "\n")

    # ---------- 2. orders JSON (500 records) with planted needles ----------
    orders, failed = [], []
    for i in range(500):
        ts = t0 + dt.timedelta(seconds=i * 9)
        o = {
            "order_id": f"ORD-{10000 + i}",
            "created_at": ts.isoformat(),
            "customer_city": rng.choice(["Lagos", "Abuja", "Ibadan", "Kano", "Enugu", "Port Harcourt"]),
            "items": rng.randint(1, 5),
            "amount_ngn": rng.randint(4000, 90000),
            "status": "paid",
            "gift_note": "",
        }
        if ts >= incident and rng.random() < 0.3:
            o["status"] = "payment_failed"
            failed.append(o["order_id"])
        orders.append(o)
    # Needles: voucher codes in gift notes of ordinary paid orders (no error words).
    needle_rows = sorted(rng.sample([k for k, o in enumerate(orders) if o["status"] == "paid"], 6))
    needles = {}
    for k in needle_rows:
        code = "GIFT-" + "".join(rng.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(5))
        orders[k]["gift_note"] = f"Happy birthday! Use voucher {code} next time."
        needles[orders[k]["order_id"]] = code
    (out / "orders.json").write_text(json.dumps({"orders": orders}, indent=1))

    # ---------- 3. last deploy diff ----------
    diff = """diff --git a/config/payments.yaml b/config/payments.yaml
index 3f1c2aa..9b7e410 100644
--- a/config/payments.yaml
+++ b/config/payments.yaml
@@ -8,11 +8,11 @@ payments:
   provider: paystackish-sandbox
   currency: NGN
   retries: 2
-  gateway_timeout_ms: 5000
+  gateway_timeout_ms: 800
   webhook_path: /hooks/payments
   idempotency: true
diff --git a/web/src/banner.txt b/web/src/banner.txt
index 11aa2c3..44bb5d1 100644
--- a/web/src/banner.txt
+++ b/web/src/banner.txt
@@ -1,3 +1,3 @@
-Free delivery on orders above 50,000 NGN
+Free delivery on orders above 45,000 NGN this week
 Follow us for new arrivals
 Questions? Use the chat button
"""
    (out / "last_deploy.diff").write_text(diff)

    # ---------- 4. config YAML with comments ----------
    cfg = ["# Lagos Loft Goods: service configuration (synthetic demo data)", "# Edit with care. Comments below explain each block.", ""]
    for blk in ["cart", "inventory", "search", "email", "images", "analytics"]:
        cfg += [f"# ---- {blk} ----", f"# {blk} settings tuned for the November sale.", f"{blk}:",
                f"  enabled: true", f"  cache_ttl_s: {rng.choice([30, 60, 120, 300])}", f"  max_workers: {rng.randint(2, 16)}", ""]
    cfg += ["# ---- payments ----", "# Gateway timeout in milliseconds. Changed in the last deploy.", "payments:",
            "  provider: paystackish-sandbox", "  currency: NGN", "  retries: 2", "  gateway_timeout_ms: 800",
            "  webhook_path: /hooks/payments", "  idempotency: true", ""]
    (out / "config.yaml").write_text("\n".join(cfg))

    # ---------- 5. on-call notes (plain prose) ----------
    notes = ("On-call handover notes. The night was mostly quiet. Traffic followed the usual pattern for a weekday, "
             "with a small bump after the newsletter went out. The image service restarted once during a routine "
             "node rotation and recovered on its own. Nobody needed to be paged for that. The search index rebuild "
             "finished on schedule. The payment provider's sandbox status page showed no incidents. "
             "Reminder for the morning team: the payments owner this week is Chiamaka Obi, and she asked to be "
             "tagged on any change to payment timeouts. The warehouse team also asked that stock counts be "
             "double-checked before the sale starts. ") * 3
    (out / "oncall_notes.txt").write_text(notes)

    first_err_s = f"{first_err:%Y-%m-%d %H:%M:%S.%f}"[:-3]
    truth = {
        "seed": seed,
        "error_code": "E_PAY_TIMEOUT_504",
        "first_error_at": first_err_s,
        "failed_order_count": len(failed),
        "failed_order_ids": failed,
        "changed_setting": "gateway_timeout_ms",
        "old_value": 5000,
        "new_value": 800,
        "payments_owner": "Chiamaka Obi",
        "needles": needles,
    }
    (out / "truth.json").write_text(json.dumps(truth, indent=1))
    return truth


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    t = make(a.seed)
    print(json.dumps({k: v for k, v in t.items() if k != "failed_order_ids"}, indent=1))

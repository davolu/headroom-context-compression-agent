"""CCR round trip: fetch the original back from the proxy's local store by hash and
check it is byte-for-byte the file the tool returned. Needs `headroom proxy` running."""
import hashlib, json, re, sqlite3, sys
from pathlib import Path
import httpx

R = Path(__file__).resolve().parents[1]
PROXY = "http://127.0.0.1:8787"
compressed = (R / "results" / "compressed_log.txt").read_text()
h = re.search(r"hash=([0-9a-f]+)", compressed).group(1)
print("marker in compressed log:", re.search(r"\[\d+ lines compressed to \d+\. Retrieve more: hash=[0-9a-f]+\]", compressed).group(0))
got = httpx.get(f"{PROXY}/v1/retrieve/{h}", timeout=30).json()["original_content"]
orig = (R / "fixtures" / "data" / "checkout.log").read_text()
sha = lambda s: hashlib.sha256(s.encode()).hexdigest()[:16]
print("sha256 original :", sha(orig))
print("sha256 retrieved:", sha(got))
print("byte-identical  :", got == orig, f"(compared {len(orig):,} chars)")
st = httpx.get(f"{PROXY}/v1/retrieve/stats", timeout=30).json()["store"]
print("store backend   :", st["backend"]["backend_type"], "| entries:", st["entry_count"], "| ttl:", st["default_ttl_seconds"], "s | retrievals:", st["total_retrievals"])
db = Path(st["backend"]["db_path"])
con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
print("sqlite tables   :", [r[0] for r in con.execute("select name from sqlite_master where type='table'")])

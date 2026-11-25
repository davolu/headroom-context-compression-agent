# Free steps (no API key, no model calls): install fixtures compress needles
# Paid steps (Anthropic API, a few cents): count proxies replay score
export DO_NOT_TRACK=1
PY ?= .venv/bin/python

install:
	python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
	.venv/bin/headroom telemetry

fixtures:
	$(PY) fixtures/make_fixtures.py --seed 7

compress:
	$(PY) eval/first_compress.py
	$(PY) eval/compress_each.py

needles:
	$(PY) eval/needle_survival.py

count:
	$(PY) eval/count_tokens.py

proxies:
	@echo "Run these in two terminals:"
	@echo "  .venv/bin/headroom proxy --port 8788 --no-optimize   # baseline"
	@echo "  .venv/bin/headroom proxy --port 8787                 # compressed"

replay:
	$(PY) eval/replay.py --mode baseline --question triage
	$(PY) eval/replay.py --mode compressed --question triage
	$(PY) eval/replay.py --mode baseline --question detail
	$(PY) eval/replay.py --mode compressed --question detail

roundtrip:
	$(PY) eval/roundtrip_retrieve.py

score:
	$(PY) eval/score.py

.PHONY: install fixtures compress needles count proxies replay roundtrip score

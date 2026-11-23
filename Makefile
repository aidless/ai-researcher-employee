.PHONY: check eval test

# Stdlib only: recompute the README check block. No network, no API key,
# no third-party install.
check:
	python3 eval/check_claims.py

# Acceptance cases alone. `make check` runs these too.
eval:
	python3 eval/run_cases.py

# Optional. Requires pytest, which `make check` does not import.
test:
	python3 -m pytest tests/ -q

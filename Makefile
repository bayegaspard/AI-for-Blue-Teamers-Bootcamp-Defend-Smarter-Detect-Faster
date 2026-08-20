# Convenience wrapper around the lab scripts.
#   make smoke     — prove the AI pipeline works (no GPU needed)
#   make verify    — check the real Ollama + Wazuh from .env
#   make core      — start mock-ollama + ai-soc-assistant
#   make full      — start everything (core + targets + attack + logs)
#   make down      — stop containers
#   make teardown  — stop + remove images/volumes
.PHONY: smoke verify core targets full logs down teardown

smoke:
	bash scripts/smoke_test.sh

verify:
	python3 scripts/verify_env.py

core:
	bash scripts/lab_up.sh core

targets:
	bash scripts/lab_up.sh core targets

full:
	bash scripts/lab_up.sh core targets attack logs

logs:
	bash scripts/lab_up.sh logs

down:
	bash scripts/lab_down.sh

teardown:
	bash scripts/teardown.sh

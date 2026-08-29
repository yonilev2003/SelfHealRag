.PHONY: setup baseline advanced eval trajectories verify-no-leak dev-loop

setup:
	@bash scripts/setup.sh

dev-loop:
	@python3 advanced/build_index.py
	@python3 advanced/tuner.py

baseline:
	@bash scripts/run_baseline.sh

advanced:
	@bash scripts/run_advanced.sh

eval:
	@python3 eval/score.py

trajectories:
	@bash scripts/collect_trajectories.sh

verify-no-leak:
	@python3 scripts/audit_no_peek.py
	@echo "verify-no-leak: OK"

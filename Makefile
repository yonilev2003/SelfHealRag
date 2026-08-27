.PHONY: setup baseline advanced eval trajectories

setup:
	@bash scripts/setup.sh

baseline:
	@bash scripts/run_baseline.sh

advanced:
	@bash scripts/run_advanced.sh

eval:
	@python3 eval/score.py

trajectories:
	@bash scripts/collect_trajectories.sh

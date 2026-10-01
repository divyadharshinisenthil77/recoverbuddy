"""
Script to execute the 8-week longitudinal A/B simulation and error analysis.
"""
import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from simulation.experiment_runner import ExperimentRunner
from simulation.error_analysis import ErrorAnalyzer

if __name__ == "__main__":
    print("Running 8-Week Synthetic Longitudinal Simulation (Baseline vs RecoverBuddy)...")
    runner = ExperimentRunner(seed=42)
    path, results = runner.save_results()
    print(f"Simulation completed and exported to {path}")

    print("\nRunning Error Analysis on synthetic cohort failure modes...")
    analyzer = ErrorAnalyzer()
    err_path, err_results = analyzer.save_analysis()
    print(f"Error diagnostics exported to {err_path}")

    kpis = results["summary_kpis"]
    print("\n================== 8-WEEK SIMULATION KPI RESULTS ==================")
    for k, v in kpis.items():
        print(f"{k:25}: Baseline = {v['baseline']:>8}  |  RecoverBuddy = {v['mvp']:>8}  |  Gain = {v['improvement_pct']}")
    print("===================================================================")

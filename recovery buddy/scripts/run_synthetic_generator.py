"""
Script to generate synthetic longitudinal datasets (20 patients x 8 weeks).
"""
import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from synthetic_data.generator import SyntheticDataGenerator

if __name__ == "__main__":
    print("Generating 20-patient x 8-week longitudinal synthetic dataset...")
    gen = SyntheticDataGenerator(seed=42, num_patients=20, weeks=8)
    j_path, c_path = gen.export_files("synthetic_data")
    print(f"Generated JSON dataset: {j_path}")
    print(f"Generated CSV dataset: {c_path}")

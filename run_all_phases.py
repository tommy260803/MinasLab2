import subprocess
import sys

phases = [
    "ml/phase1_business_understanding.py",
    "ml/phase2_data_understanding.py",
    "ml/phase3_data_preparation.py",
    "ml/phase4_modeling.py",
    "ml/phase5_evaluation.py"
]

for phase in phases:
    print(f"\n{'='*50}\n> Ejecutando {phase}...\n{'='*50}")
    subprocess.run([sys.executable, phase], check=True)
    print(f"OK: {phase} completado exitosamente.\n")

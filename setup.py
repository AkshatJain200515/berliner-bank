import os
import subprocess
import sys


def run(cmd, description=""):
    print(f"  {description}..." if description else f"  Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


if not os.path.exists("venv"):
    print("[1/3] Creating virtual environment...")
    run([sys.executable, "-m", "venv", "venv"], "Creating venv")
else:
    print("[1/3] Virtual environment already exists, skipping.")


if os.name == "nt":
    python = os.path.join("venv", "Scripts", "python.exe")
    activate_hint = r"venv\Scripts\activate"
else:
    python = os.path.join("venv", "bin", "python")
    activate_hint = "source venv/bin/activate"

print("\n[2/3] Installing dependencies (Flask)...")
run([python, "-m", "pip", "install", "--upgrade", "pip", "--quiet"])
run([python, "-m", "pip", "install", "Flask", "--quiet"])

print("\n[3/3] Setting up the database...")
run([python, "-c", "from database import init_db; init_db(); print('  Database ready.')"])

print("\n========================================")
print("  Setup complete!")
print(f"  Activate env : {activate_hint}")
print("  Start server  : python app.py")
print("========================================\n")

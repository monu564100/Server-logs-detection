import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent


def run_step(script_path: Path) -> None:
    print(f"\n[STEP] Running {script_path.relative_to(ROOT_DIR)}")
    result = subprocess.run([sys.executable, str(script_path)], cwd=ROOT_DIR)
    if result.returncode != 0:
        raise RuntimeError(f"{script_path.name} failed with exit code {result.returncode}")


def start_dashboard() -> None:
    dashboard_path = ROOT_DIR / "src" / "dashboard.py"
    print("\n[STEP] Launching dashboard on http://127.0.0.1:8050")
    subprocess.run([sys.executable, str(dashboard_path)], cwd=ROOT_DIR)


def main() -> None:
    try:
        run_step(ROOT_DIR / "src" / "pipeline.py")
        start_dashboard()
    except Exception as exc:
        print(f"\nPipeline stopped: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()

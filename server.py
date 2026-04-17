import subprocess
import sys
import os
from datetime import datetime
from pathlib import Path
import smtplib
from email.message import EmailMessage

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"
PARSED_FILE = DATA_DIR / "parsed_logs.parquet"
FEATURES_ANOMALY_FILE = DATA_DIR / "features_with_anomaly.parquet"
ANOMALY_XLSX_FILE = DATA_DIR / "anomalies.xlsx"
CRITICAL_IPS_XLSX_FILE = DATA_DIR / "critical_ips.xlsx"


def run_step(script_path: Path) -> None:
    print(f"\n[STEP] Running {script_path.relative_to(ROOT_DIR)}")
    result = subprocess.run([sys.executable, str(script_path)], cwd=ROOT_DIR)
    if result.returncode != 0:
        raise RuntimeError(f"{script_path.name} failed with exit code {result.returncode}")


def load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _get_env_value(*keys: str) -> str:
    for key in keys:
        val = os.getenv(key)
        if val:
            return val.strip()
    return ""


def build_critical_ips_excel() -> Path:
    if not PARSED_FILE.exists() or not FEATURES_ANOMALY_FILE.exists():
        raise FileNotFoundError("Missing parsed or anomaly parquet files. Run pipeline first.")

    logs_df = pd.read_parquet(PARSED_FILE)
    features_df = pd.read_parquet(FEATURES_ANOMALY_FILE)

    logs_df["timestamp"] = pd.to_datetime(logs_df["timestamp"], errors="coerce")
    features_df["time_bin"] = pd.to_datetime(features_df["time_bin"], errors="coerce")

    attack_mask = features_df.get("attack_prediction", pd.Series([""] * len(features_df))) == "Attack"
    critical_mask = features_df.get("severity", pd.Series([""] * len(features_df))) == "Critical"

    critical_windows = features_df[attack_mask & critical_mask].copy()
    if critical_windows.empty:
        critical_windows = features_df[attack_mask].copy()

    details: list[pd.DataFrame] = []
    for _, row in critical_windows.iterrows():
        start_time = pd.to_datetime(row["time_bin"], errors="coerce")
        if pd.isna(start_time):
            continue
        end_time = start_time + pd.Timedelta(minutes=5)
        subset = logs_df[
            (logs_df["timestamp"] >= start_time)
            & (logs_df["timestamp"] < end_time)
            & (logs_df["ip"] != "Unknown")
        ].copy()
        if subset.empty:
            continue
        subset["window_start"] = start_time
        subset["severity"] = row.get("severity", "Attack")
        details.append(subset)

    critical_logs = pd.concat(details, ignore_index=True) if details else pd.DataFrame(
        columns=["timestamp", "service", "level", "message", "ip", "source_file", "window_start", "severity"]
    )

    if critical_logs.empty:
        critical_ips = pd.DataFrame(
            columns=["ip", "occurrences", "first_seen", "last_seen", "services", "levels"]
        )
    else:
        critical_ips = (
            critical_logs.groupby("ip", dropna=False)
            .agg(
                occurrences=("ip", "size"),
                first_seen=("timestamp", "min"),
                last_seen=("timestamp", "max"),
                services=("service", lambda x: ", ".join(sorted(set(map(str, x))))),
                levels=("level", lambda x: ", ".join(sorted(set(map(str, x))))),
            )
            .reset_index()
            .sort_values("occurrences", ascending=False)
        )

    with pd.ExcelWriter(CRITICAL_IPS_XLSX_FILE, engine="openpyxl") as writer:
        critical_ips.to_excel(writer, sheet_name="critical_ips", index=False)
        critical_logs.to_excel(writer, sheet_name="critical_log_rows", index=False)
        critical_windows.to_excel(writer, sheet_name="critical_windows", index=False)

    print(f"[STEP] Critical IP report saved to {CRITICAL_IPS_XLSX_FILE}")
    return CRITICAL_IPS_XLSX_FILE


def send_security_email() -> None:
    load_env_file(ROOT_DIR / ".env")

    smtp_host = _get_env_value("EMAIL_HOST", "SMTP_HOST", "MAIL_HOST") or "smtp.gmail.com"
    smtp_port = int(_get_env_value("EMAIL_PORT", "SMTP_PORT") or "587")
    email_user = _get_env_value("EMAIL_USER", "Email_user", "EMAIL_FROM")
    email_password = _get_env_value("EMAIL_PASSWORD", "Email_password", "EMAIL_PASS")
    email_to = _get_env_value("EMAIL_TO", "EMAIL_RECEIVER") or "monu56410000@gmail.com"

    if not email_user or not email_password:
        raise RuntimeError("Email credentials not found in .env. Set EMAIL_USER and EMAIL_PASSWORD.")

    critical_report = build_critical_ips_excel()

    body = """Hello,

Attached are the latest anomaly outputs from LogAnomalyPlatform:
1. anomalies.xlsx
2. critical_ips.xlsx (critical IP list)

Recommended actions to protect the server:
- Block repeatedly suspicious IPs using firewall/ACL rules.
- Enable fail2ban or equivalent auto-blocking for brute-force patterns.
- Restrict SSH/RDP access by IP allowlisting and disable password-only login where possible.
- Patch OS and exposed services to current security updates.
- Review privileged account activity and enforce MFA for admin access.
- Set alerting for repeated ERROR/CRITICAL events and unusual traffic bursts.
- Rotate exposed credentials and store secrets in a secured vault.

This email was automatically generated when server.py was executed.
"""

    message = EmailMessage()
    message["Subject"] = f"LogAnomaly Security Alert - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    message["From"] = email_user
    message["To"] = email_to
    message.set_content(body)

    attachment_paths = [ANOMALY_XLSX_FILE, critical_report]
    for attachment_path in attachment_paths:
        if not attachment_path.exists():
            continue
        with attachment_path.open("rb") as file_handle:
            message.add_attachment(
                file_handle.read(),
                maintype="application",
                subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                filename=attachment_path.name,
            )

    with smtplib.SMTP(smtp_host, smtp_port) as smtp:
        smtp.starttls()
        smtp.login(email_user, email_password)
        smtp.send_message(message)

    print(f"[STEP] Security report email sent to {email_to}")


def start_dashboard() -> None:
    dashboard_path = ROOT_DIR / "src" / "dashboard.py"
    print("\n[STEP] Launching dashboard on http://127.0.0.1:8050")
    subprocess.run([sys.executable, str(dashboard_path)], cwd=ROOT_DIR)


def main() -> None:
    try:
        run_step(ROOT_DIR / "src" / "pipeline.py")
        send_security_email()
        start_dashboard()
    except Exception as exc:
        print(f"\nPipeline stopped: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()

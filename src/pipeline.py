from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import shutil
from typing import Iterable, Optional

import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

PARSED_FILE = DATA_DIR / "parsed_logs.parquet"
FEATURES_FILE = DATA_DIR / "features.parquet"
FEATURES_ANOMALY_FILE = DATA_DIR / "features_with_anomaly.parquet"
ANOMALY_XLSX_FILE = DATA_DIR / "anomalies.xlsx"
TRAINING_REPORT_FILE = DATA_DIR / "training_report.json"

PRIMARY_LOCAL_LOG = DATA_DIR / "Linux.log"

IP_REGEX = re.compile(r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b")
LEVEL_REGEX = re.compile(r"\b(INFO|WARN|WARNING|ERROR|DEBUG|CRITICAL|TRACE|FATAL)\b", flags=re.IGNORECASE)
TS_REGEX = re.compile(r"(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:\.\d+)?)")

FEATURE_COLUMNS = [
    "log_count",
    "error_ratio",
    "warn_ratio",
    "avg_message_len",
    "unique_services",
    "unique_ips",
]


def assign_attack_labels(features: pd.DataFrame) -> pd.DataFrame:
    features = features.copy()
    n_rows = len(features)
    if n_rows == 0:
        features["attack_prediction"] = []
        features["severity"] = []
        return features

    # Lower decision_function means more anomalous; use a fallback to always flag top-risk windows.
    min_anomalies = max(1, int(round(n_rows * 0.05)))
    current_anomalies = int((features["anomaly"] == -1).sum())

    if current_anomalies < min_anomalies:
        top_idx = features.nsmallest(min_anomalies, "anomaly_score").index
        features.loc[top_idx, "anomaly"] = -1

    features["attack_prediction"] = features["anomaly"].map({-1: "Attack", 1: "Normal"}).fillna("Normal")

    features["severity"] = "Normal"
    attack_mask = features["attack_prediction"] == "Attack"
    if attack_mask.any():
        attack_scores = features.loc[attack_mask, "anomaly_score"]
        q33 = attack_scores.quantile(0.33)
        q66 = attack_scores.quantile(0.66)
        features.loc[attack_mask & (features["anomaly_score"] <= q33), "severity"] = "Critical"
        features.loc[attack_mask & (features["anomaly_score"] > q33) & (features["anomaly_score"] <= q66), "severity"] = "High"
        features.loc[attack_mask & (features["anomaly_score"] > q66), "severity"] = "Medium"

    return features


def add_prediction_metrics(features: pd.DataFrame) -> pd.DataFrame:
    features = features.copy()
    if features.empty:
        features["prediction_confidence_pct"] = []
        features["prediction_accuracy_level_pct"] = []
        return features

    # Convert anomaly score to risk range [0,1], where 1 is most suspicious.
    score_min = float(features["anomaly_score"].min())
    score_max = float(features["anomaly_score"].max())
    denom = (score_max - score_min) if score_max > score_min else 1.0
    risk = (score_max - features["anomaly_score"]) / denom

    confidence = pd.Series(0.0, index=features.index)
    attack_mask = features["attack_prediction"] == "Attack"
    confidence.loc[attack_mask] = 50.0 + 50.0 * risk.loc[attack_mask]
    confidence.loc[~attack_mask] = 50.0 + 50.0 * (1.0 - risk.loc[~attack_mask])
    features["prediction_confidence_pct"] = confidence.round(2)

    # Accuracy-level proxy from score separation (no ground-truth labels in unsupervised logs).
    if attack_mask.any() and (~attack_mask).any():
        normal_mean = float(features.loc[~attack_mask, "anomaly_score"].mean())
        attack_mean = float(features.loc[attack_mask, "anomaly_score"].mean())
        score_std = float(features["anomaly_score"].std())
        score_std = score_std if score_std > 1e-9 else 1.0
        separation = (normal_mean - attack_mean) / score_std
        accuracy_level = max(55.0, min(99.0, 50.0 + 15.0 * separation))
    else:
        accuracy_level = 60.0

    features["prediction_accuracy_level_pct"] = round(accuracy_level, 2)
    return features


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def prepare_parquet_target(path: Path) -> None:
    # Older runs may have created directory-style parquet paths.
    if path.exists() and path.is_dir():
        shutil.rmtree(path)


def discover_log_files(dataset_path: Path) -> list[Path]:
    log_files: list[Path] = []
    for ext in ("*.log", "*.txt", "*.out"):
        log_files.extend(dataset_path.rglob(ext))

    # Fallback: include files without extension if no logs found.
    if not log_files:
        for file_path in dataset_path.rglob("*"):
            if file_path.is_file() and file_path.suffix == "":
                log_files.append(file_path)

    return sorted(set(log_files))


def discover_local_log_files() -> list[Path]:
    if PRIMARY_LOCAL_LOG.exists() and PRIMARY_LOCAL_LOG.is_file():
        return [PRIMARY_LOCAL_LOG]

    local_logs: list[Path] = []
    for ext in ("*.log", "*.txt", "*.out"):
        local_logs.extend(DATA_DIR.rglob(ext))
    return sorted(set([p for p in local_logs if p.is_file()]))


def discover_training_files(input_path: Optional[Path] = None) -> list[Path]:
    if input_path is None:
        return discover_local_log_files()

    candidate = input_path.expanduser().resolve()
    if candidate.is_file():
        return [candidate]

    if candidate.is_dir():
        return discover_log_files(candidate)

    raise FileNotFoundError(f"Training input path not found: {candidate}")


def parse_timestamp(text: str) -> pd.Timestamp:
    ts_match = TS_REGEX.search(text)
    if ts_match:
        parsed = pd.to_datetime(ts_match.group(1), errors="coerce")
        if pd.notna(parsed):
            return parsed
    return pd.NaT


def parse_level(text: str) -> str:
    level_match = LEVEL_REGEX.search(text)
    if not level_match:
        return "INFO"
    level = level_match.group(1).upper()
    if level == "WARNING":
        return "WARN"
    return level


def parse_service(source_file: Path, line: str) -> str:
    parts = line.split()
    if len(parts) >= 3 and parts[2].endswith(":"):
        return parts[1]
    return source_file.parent.name or "linux"


def parse_message(line: str) -> str:
    if ":" in line:
        return line.split(":", 1)[1].strip()
    return line.strip()


def extract_ip(text: str) -> str:
    ip_match = IP_REGEX.search(text)
    return ip_match.group(0) if ip_match else "Unknown"


def parse_log_line(line: str, source_file: Path) -> Optional[dict]:
    if not line or not line.strip():
        return None

    timestamp = parse_timestamp(line)
    level = parse_level(line)
    service = parse_service(source_file, line)
    message = parse_message(line)
    ip_address = extract_ip(line)

    return {
        "timestamp": timestamp,
        "service": service,
        "level": level,
        "message": message,
        "ip": ip_address,
        "source_file": str(source_file),
    }


def parse_logs_from_files(files: Iterable[Path]) -> pd.DataFrame:
    records: list[dict] = []
    for file_idx, file_path in enumerate(files):
        synthetic_start = pd.Timestamp("2024-01-01") + pd.Timedelta(days=file_idx)
        try:
            with file_path.open("r", encoding="utf-8", errors="ignore") as handle:
                for line_idx, raw_line in enumerate(handle):
                    parsed = parse_log_line(raw_line.rstrip("\n"), file_path)
                    if parsed is not None:
                        if pd.isna(parsed["timestamp"]):
                            # Keep temporal ordering when source logs have no explicit timestamp.
                            parsed["timestamp"] = synthetic_start + pd.Timedelta(seconds=line_idx)
                        records.append(parsed)
        except OSError as exc:
            print(f"Skipping unreadable file: {file_path} ({exc})")

    if not records:
        return pd.DataFrame(columns=["timestamp", "service", "level", "message", "ip", "source_file"])

    df_logs = pd.DataFrame(records)
    df_logs["timestamp"] = pd.to_datetime(df_logs["timestamp"], errors="coerce")
    df_logs = df_logs.dropna(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
    return df_logs


def run_parse_step(input_path: Optional[Path] = None) -> pd.DataFrame:
    ensure_dirs()
    log_files = discover_training_files(input_path)
    source = "local data folder" if input_path is None else str(input_path)

    if not log_files:
        if PARSED_FILE.exists():
            print("No raw logs found. Reusing existing parsed dataset from data/parsed_logs.parquet")
            df_logs = pd.read_parquet(PARSED_FILE)
            if df_logs.empty:
                raise RuntimeError("Existing parsed dataset is empty. Provide local raw logs to continue.")
            return df_logs

        raise RuntimeError(
            "No local training log files found. Place logs in data/Linux.log or pass --input with your file/folder."
        )

    print(f"Found {len(log_files)} log files from {source}. Parsing...")
    for file_path in log_files:
        print(f"Using log source: {file_path}")

    df_logs = parse_logs_from_files(log_files)
    if df_logs.empty:
        raise RuntimeError("Parsing finished but no valid log rows were produced.")

    prepare_parquet_target(PARSED_FILE)
    df_logs.to_parquet(PARSED_FILE, index=False)
    print(f"Parsed logs saved to: {PARSED_FILE}")
    print(f"Parsed row count: {len(df_logs)}")

    if "source_file" in df_logs.columns:
        src_counts = df_logs["source_file"].value_counts().head(3)
        print("Top parsed sources:")
        for src, cnt in src_counts.items():
            print(f"  {src}: {cnt} rows")

    return df_logs


def run_feature_step(df_logs: Optional[pd.DataFrame] = None, window_minutes: int = 5) -> pd.DataFrame:
    ensure_dirs()
    if df_logs is None:
        if not PARSED_FILE.exists():
            raise FileNotFoundError(f"Missing parsed logs file: {PARSED_FILE}")
        df_logs = pd.read_parquet(PARSED_FILE)

    if df_logs.empty:
        raise RuntimeError("Parsed logs are empty. Cannot build features.")

    df_logs = df_logs.copy()
    df_logs["timestamp"] = pd.to_datetime(df_logs["timestamp"], errors="coerce")
    df_logs = df_logs.dropna(subset=["timestamp"])
    df_logs["time_bin"] = df_logs["timestamp"].dt.floor(f"{window_minutes}min")

    features = df_logs.groupby("time_bin").agg(
        log_count=("message", "count"),
        error_ratio=("level", lambda x: (x == "ERROR").mean()),
        warn_ratio=("level", lambda x: (x == "WARN").mean()),
        avg_message_len=("message", lambda x: x.astype(str).str.len().mean()),
        unique_services=("service", "nunique"),
        unique_ips=("ip", lambda x: x[x != "Unknown"].nunique()),
    ).reset_index()

    prepare_parquet_target(FEATURES_FILE)
    features.to_parquet(FEATURES_FILE, index=False)
    print(f"Features saved to: {FEATURES_FILE}")
    return features


def _write_training_report(
    *,
    features_with_anomaly: pd.DataFrame,
    contamination: float,
    n_estimators: int,
    random_state: int,
) -> None:
    attack_count = int((features_with_anomaly["attack_prediction"] == "Attack").sum())
    report = {
        "model": "IsolationForest",
        "mode": "unsupervised",
        "parameters": {
            "contamination": contamination,
            "n_estimators": n_estimators,
            "random_state": random_state,
        },
        "training_windows": int(len(features_with_anomaly)),
        "predicted_attack_windows": attack_count,
        "attack_window_ratio": round(attack_count / max(len(features_with_anomaly), 1), 6),
        "feature_columns": FEATURE_COLUMNS,
    }
    TRAINING_REPORT_FILE.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Training report saved to: {TRAINING_REPORT_FILE}")


def run_train_step(
    features: Optional[pd.DataFrame] = None,
    *,
    contamination: float = 0.05,
    n_estimators: int = 200,
    random_state: int = 42,
) -> pd.DataFrame:
    ensure_dirs()
    if features is None:
        if not FEATURES_FILE.exists():
            raise FileNotFoundError(f"Missing features file: {FEATURES_FILE}")
        features = pd.read_parquet(FEATURES_FILE)

    if features.empty:
        raise RuntimeError("Feature table is empty. Cannot train model.")

    features = features.copy()
    x = features[FEATURE_COLUMNS].fillna(0)

    scaler = StandardScaler()
    x_scaled = scaler.fit_transform(x)

    model = IsolationForest(
        contamination=contamination,
        n_estimators=n_estimators,
        random_state=random_state,
    )
    model.fit(x_scaled)

    features["anomaly"] = model.predict(x_scaled)
    features["anomaly_score"] = model.decision_function(x_scaled)
    features = assign_attack_labels(features)
    features = add_prediction_metrics(features)

    prepare_parquet_target(FEATURES_ANOMALY_FILE)
    features.to_parquet(FEATURES_ANOMALY_FILE, index=False)

    print(f"Features with anomalies saved to: {FEATURES_ANOMALY_FILE}")
    attack_count = int((features["attack_prediction"] == "Attack").sum())
    print(f"Training windows: {len(features)} | Predicted attack windows: {attack_count}")
    _write_training_report(
        features_with_anomaly=features,
        contamination=contamination,
        n_estimators=n_estimators,
        random_state=random_state,
    )
    return features


def export_anomalies_to_excel(
    features_with_anomaly: Optional[pd.DataFrame] = None,
    logs_df: Optional[pd.DataFrame] = None,
) -> Path:
    if features_with_anomaly is None:
        if not FEATURES_ANOMALY_FILE.exists():
            raise FileNotFoundError(f"Missing anomaly features file: {FEATURES_ANOMALY_FILE}")
        features_with_anomaly = pd.read_parquet(FEATURES_ANOMALY_FILE)

    if logs_df is None:
        if not PARSED_FILE.exists():
            raise FileNotFoundError(f"Missing parsed logs file: {PARSED_FILE}")
        logs_df = pd.read_parquet(PARSED_FILE)

    anomalies = features_with_anomaly[features_with_anomaly["attack_prediction"] == "Attack"].copy() if "attack_prediction" in features_with_anomaly.columns else features_with_anomaly[features_with_anomaly["anomaly"] == -1].copy()
    if anomalies.empty:
        anomalies = features_with_anomaly.nsmallest(min(10, len(features_with_anomaly)), "anomaly_score").copy()

    logs_df = logs_df.copy()
    logs_df["timestamp"] = pd.to_datetime(logs_df["timestamp"], errors="coerce")

    detail_frames: list[pd.DataFrame] = []
    for _, row in anomalies.iterrows():
        start_time = pd.to_datetime(row["time_bin"])
        end_time = start_time + pd.Timedelta(minutes=5)
        mask = (logs_df["timestamp"] >= start_time) & (logs_df["timestamp"] < end_time)
        subset = logs_df[mask].copy()
        if subset.empty:
            continue
        subset["anomaly_time_bin"] = start_time
        subset["anomaly_score"] = row["anomaly_score"]
        detail_frames.append(subset)

    anomaly_logs = pd.concat(detail_frames, ignore_index=True) if detail_frames else pd.DataFrame(
        columns=["timestamp", "service", "level", "message", "ip", "source_file", "anomaly_time_bin", "anomaly_score"]
    )

    with pd.ExcelWriter(ANOMALY_XLSX_FILE, engine="openpyxl") as writer:
        anomalies.to_excel(writer, sheet_name="anomaly_windows", index=False)
        anomaly_logs.to_excel(writer, sheet_name="anomaly_logs", index=False)

    print(f"Anomaly Excel report saved to: {ANOMALY_XLSX_FILE}")
    return ANOMALY_XLSX_FILE


def run_full_pipeline(
    *,
    input_path: Optional[Path] = None,
    window_minutes: int = 5,
    contamination: float = 0.05,
    n_estimators: int = 200,
    random_state: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Path]:
    logs = run_parse_step(input_path=input_path)
    features = run_feature_step(logs, window_minutes=window_minutes)
    features_with_anomaly = run_train_step(
        features,
        contamination=contamination,
        n_estimators=n_estimators,
        random_state=random_state,
    )
    excel_path = export_anomalies_to_excel(features_with_anomaly, logs)
    return logs, features, features_with_anomaly, excel_path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run log anomaly pipeline steps from a single file.")
    parser.add_argument(
        "--step",
        choices=["parse", "feature", "train", "full"],
        default="full",
        help="Pipeline step to run (default: full).",
    )
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Path to your own log file or folder. If omitted, uses data/Linux.log or data/*.log.",
    )
    parser.add_argument(
        "--window-minutes",
        type=int,
        default=5,
        help="Aggregation window size in minutes for feature engineering.",
    )
    parser.add_argument(
        "--contamination",
        type=float,
        default=0.05,
        help="IsolationForest expected anomaly fraction (0.0 to 0.5).",
    )
    parser.add_argument(
        "--n-estimators",
        type=int,
        default=200,
        help="Number of trees in IsolationForest.",
    )
    parser.add_argument(
        "--random-state",
        type=int,
        default=42,
        help="Random seed used by IsolationForest.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    input_path = Path(args.input) if args.input else None

    if args.step == "parse":
        run_parse_step(input_path=input_path)
    elif args.step == "feature":
        run_feature_step(window_minutes=args.window_minutes)
    elif args.step == "train":
        run_train_step(
            contamination=args.contamination,
            n_estimators=args.n_estimators,
            random_state=args.random_state,
        )
    else:
        run_full_pipeline(
            input_path=input_path,
            window_minutes=args.window_minutes,
            contamination=args.contamination,
            n_estimators=args.n_estimators,
            random_state=args.random_state,
        )


if __name__ == "__main__":
    main()

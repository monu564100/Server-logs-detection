import time
import pandas as pd
import numpy as np
import joblib
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import requests
import os
from datetime import datetime, timedelta
import re

# ---------- Configuration ----------
SLACK_WEBHOOK_URL = "YOUR_SLACK_WEBHOOK_URL"  # Replace with your actual webhook
LOG_FOLDER = "data/live"
PARSED_FILE = "data/parsed_logs.parquet"
FEATURES_FILE = "data/features.parquet"
FEATURES_ANOMALY_FILE = "data/features_with_anomaly.parquet"
MODEL_FILE = "models/isolation_forest.pkl"
SCALER_FILE = "models/scaler.pkl"
# -----------------------------------

def send_slack_alert(message):
    if SLACK_WEBHOOK_URL and SLACK_WEBHOOK_URL != "YOUR_SLACK_WEBHOOK_URL":
        payload = {"text": message}
        try:
            requests.post(SLACK_WEBHOOK_URL, json=payload)
        except Exception as e:
            print(f"Slack alert failed: {e}")

def parse_log_line(line):
    pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+)\s+(\S+)\s+(\w+):\s+(.*)'
    match = re.match(pattern, line)
    if match:
        timestamp, service, level, message = match.groups()
        return {'timestamp': pd.to_datetime(timestamp), 'service': service, 'level': level, 'message': message}
    return None

def process_new_file(filepath):
    print(f"Processing {filepath}")
    new_logs = []
    with open(filepath, 'r') as f:
        for line in f:
            parsed = parse_log_line(line.strip())
            if parsed:
                new_logs.append(parsed)

    if not new_logs:
        return

    # Load existing logs
    if os.path.exists(PARSED_FILE):
        df_existing = pd.read_parquet(PARSED_FILE)
    else:
        df_existing = pd.DataFrame(columns=['timestamp', 'service', 'level', 'message'])

    df_new = pd.DataFrame(new_logs)
    df_combined = pd.concat([df_existing, df_new], ignore_index=True).drop_duplicates().sort_values('timestamp')
    df_combined.to_parquet(PARSED_FILE, index=False)

    # Recompute features for new windows only (simplified: recompute all)
    # In production, you'd only update affected windows.
    df_combined['time_bin'] = df_combined['timestamp'].dt.floor('5min')
    features = df_combined.groupby('time_bin').agg(
        log_count=('message', 'count'),
        error_ratio=('level', lambda x: (x == 'ERROR').mean()),
        warn_ratio=('level', lambda x: (x == 'WARN').mean()),
        avg_message_len=('message', lambda x: x.str.len().mean()),
        unique_services=('service', 'nunique')
    ).reset_index()
    features.to_parquet(FEATURES_FILE, index=False)

    # Load model and predict
    model = joblib.load(MODEL_FILE)
    scaler = joblib.load(SCALER_FILE)
    feature_cols = ['log_count', 'error_ratio', 'warn_ratio', 'avg_message_len', 'unique_services']
    X = features[feature_cols].fillna(0)
    X_scaled = scaler.transform(X)
    features['anomaly'] = model.predict(X_scaled)
    features['anomaly_score'] = model.decision_function(X_scaled)
    features.to_parquet(FEATURES_ANOMALY_FILE, index=False)

    # Check for new anomalies (only in the new windows)
    # For simplicity, we'll just alert on any anomalies in the latest window.
    latest_window = features.iloc[-1] if not features.empty else None
    if latest_window is not None and latest_window['anomaly'] == -1:
        msg = f"🚨 Anomaly detected in window {latest_window['time_bin']}\n"
        msg += f"Log count: {latest_window['log_count']}, Error ratio: {latest_window['error_ratio']:.2f}"
        send_slack_alert(msg)

class LogFileHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.log'):
            time.sleep(1)  # Wait for file to be fully written
            process_new_file(event.src_path)

if __name__ == "__main__":
    os.makedirs(LOG_FOLDER, exist_ok=True)
    event_handler = LogFileHandler()
    observer = Observer()
    observer.schedule(event_handler, LOG_FOLDER, recursive=False)
    observer.start()
    print(f"Monitoring {LOG_FOLDER} for new log files...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

# Log Anomaly Detection Platform

A real‑time big data log analysis and anomaly detection system built with Python, Dask, and Dash.

## Features

- Parses large log files using Dask (scalable)
- Engineers time‑window features (log count, error ratio, etc.)
- Trains Isolation Forest model to detect anomalies
- Interactive Dash dashboard with:
  - Log volume scatter plot (normal vs anomaly)
  - Error rate over time line chart
  - Filter by service
  - View raw logs for any anomalous window
- Real‑time monitoring of new log files
- Slack alerts for new anomalies (optional)
- Export anomalies as CSV
- One‑click model retraining

## Quick Start

1. Clone this repo
2. Create virtual environment: python -m venv venv
3. Activate: .\venv\Scripts\Activate (Windows) or source venv/bin/activate (Mac/Linux)
4. Install dependencies: pip install -r requirements.txt
5. Generate sample logs: python src/generate_logs.py
6. Run the full pipeline: python src/parse_logs.py → python src/feature_engineering.py → python src/train_model.py
7. Launch dashboard: python src/dashboard.py
8. (Optional) Start real‑time monitor: python src/log_monitor.py

## Demo

![Dashboard Screenshot](screenshot.png)  <!-- Add a screenshot later -->

## Requirements

- Python 3.8+
- See equirements.txt

## License

MIT

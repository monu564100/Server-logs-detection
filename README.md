# 🔍 Log Anomaly Detection Platform

> A real-time big data log analysis and anomaly detection system built with **Python**, **Dask**, and **Dash**.

![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat-square&logo=python&logoColor=white)
![Dask](https://img.shields.io/badge/Dask-Scalable-FC6E27?style=flat-square&logo=dask&logoColor=white)
![Dash](https://img.shields.io/badge/Dash-Interactive-00B4D8?style=flat-square&logo=plotly&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-ML-F7931E?style=flat-square&logo=scikit-learn&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-22C55E?style=flat-square)

---

## ✨ Features

- ⚡ **Scalable Log Parsing** — Processes large log files using Dask (parallel & distributed)
- 🧠 **Anomaly Detection** — Trains an Isolation Forest model on time-window features (log count, error ratio, etc.)
- 📊 **Interactive Dashboard** powered by Dash:
  - Log volume scatter plot (normal vs. anomaly)
  - Error rate over time line chart
  - Filter by service
  - View raw logs for any anomalous window
- 👁️ **Real-Time Monitoring** — Watches for new log files and processes them automatically
- 🔔 **Slack Alerts** — Optional notifications for new anomalies
- 📥 **Export to CSV** — Download all detected anomalies
- 🔄 **One-Click Model Retraining** — Retrain directly from the dashboard

---

## 🖥️ Dashboard Preview

![Dashboard Screenshot](screenshot.png)

---

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/your-username/log-anomaly-platform.git
cd log-anomaly-platform
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# Windows
.\venv\Scripts\Activate

# Mac / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Generate sample logs

```bash
python src/generate_logs.py
```

### 5. Run the full pipeline

```bash
python src/parse_logs.py
python src/feature_engineering.py
python src/train_model.py
```

### 6. Launch the dashboard

```bash
python src/dashboard.py
```

Then open [http://localhost:8050](http://localhost:8050) in your browser.

### 7. (Optional) Start the real-time monitor

```bash
python src/log_monitor.py
```

---

## 📁 Project Structure

```
log-anomaly-platform/
├── src/
│   ├── generate_logs.py       # Generate sample log data
│   ├── parse_logs.py          # Parse raw logs with Dask
│   ├── feature_engineering.py # Build time-window features
│   ├── train_model.py         # Train Isolation Forest model
│   ├── dashboard.py           # Launch the Dash UI
│   └── log_monitor.py         # Real-time file watcher
├── data/                      # Log files and processed data
├── models/                    # Saved model artifacts
├── requirements.txt
└── README.md
```

---

## 📦 Requirements

- Python 3.8+
- See [`requirements.txt`](requirements.txt) for the full list

Key dependencies:

| Package | Purpose |
|---|---|
| `dask` | Scalable log parsing |
| `pandas` | Data wrangling |
| `scikit-learn` | Isolation Forest model |
| `dash` / `plotly` | Interactive dashboard |
| `slack-sdk` | Slack alerts (optional) |

---

## ⚙️ Configuration

To enable **Slack alerts**, add your webhook URL to a `.env` file:

```env
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/your/webhook/url
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

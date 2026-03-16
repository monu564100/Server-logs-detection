# 🔍 Log Anomaly Detection Platform

<div align="center">

**A real-time big data log analysis and anomaly detection system built with Python, Dask, and Dash.**

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Dask](https://img.shields.io/badge/Dask-Distributed-FC6E27?style=for-the-badge&logo=dask&logoColor=white)](https://dask.org)
[![Dash](https://img.shields.io/badge/Dash-Plotly-00B4D8?style=for-the-badge&logo=plotly&logoColor=white)](https://dash.plotly.com)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-ML-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)](https://scikit-learn.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-22C55E?style=for-the-badge)](LICENSE)

</div>

---

## 📸 Dashboard Preview

![Dashboard Screenshot](screenshot.png)

---

## ✨ Features

| Feature | Description |
|---|---|
| ⚡ **Scalable Parsing** | Processes large log files with Dask — parallel, distributed, never runs out of memory |
| 🧠 **Isolation Forest** | Unsupervised ML model trained on time-window features (log count, error ratio, latency) |
| 📊 **Interactive Dashboard** | Scatter plots, error timelines, service filters, and raw log drilldown via Dash |
| 👁️ **Real-Time Monitor** | Watches directories for new log files and auto-processes them |
| 🔔 **Slack Alerts** | Optional webhook notifications when anomalies are detected |
| 📥 **CSV Export** | Download all flagged anomalies for offline analysis |
| 🔄 **One-Click Retrain** | Trigger model retraining directly from the dashboard UI |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        DATA INGESTION                        │
│                                                             │
│   /var/log/*.log  ──►  log_monitor.py  ──►  parse_logs.py  │
│                         (file watcher)     (Dask parser)    │
└───────────────────────────────┬─────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                     FEATURE ENGINEERING                      │
│                                                             │
│         feature_engineering.py                              │
│         · Log count per time window                         │
│         · Error ratio  · Unique services                    │
│         · Request rate · P99 latency                        │
└───────────────────────────────┬─────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                      ML MODEL LAYER                          │
│                                                             │
│         train_model.py  ──►  Isolation Forest               │
│                              · Anomaly score threshold       │
│                              · Labels: normal / anomaly      │
└──────────────┬────────────────┬────────────────┬────────────┘
               │                │                │
               ▼                ▼                ▼
        dashboard.py       slack alert       anomalies.csv
        (Dash UI)          (webhook)         (CSV export)
```

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
```

```bash
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

Open [http://localhost:8050](http://localhost:8050) in your browser.

### 7. (Optional) Start real-time monitoring

```bash
python src/log_monitor.py
```

---

## 📁 Project Structure

```
log-anomaly-platform/
├── src/
│   ├── generate_logs.py         # Synthetic log data generator
│   ├── parse_logs.py            # Dask-powered log parser
│   ├── feature_engineering.py   # Time-window feature builder
│   ├── train_model.py           # Isolation Forest trainer
│   ├── dashboard.py             # Dash UI · localhost:8050
│   └── log_monitor.py           # Real-time file watcher
├── data/                        # Raw & processed log files
├── models/                      # Saved model artifacts (.pkl)
├── requirements.txt
└── README.md
```

---

## 📦 Dependencies

| Package | Version | Purpose |
|---|---|---|
| `dask` | latest | Scalable log parsing |
| `pandas` | latest | Data wrangling |
| `scikit-learn` | latest | Isolation Forest model |
| `dash` | latest | Interactive dashboard |
| `plotly` | latest | Charts & visualisations |
| `slack-sdk` | latest | Slack alerts *(optional)* |

---

## ⚙️ Configuration

To enable Slack alerts, create a `.env` file in the project root:

```env
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/your/webhook/url
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).


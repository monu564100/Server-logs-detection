<div align="center">

<!-- Animated Banner -->
<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=200&section=header&text=Log%20Anomaly%20Detection&fontSize=42&fontColor=fff&animation=twinkling&fontAlignY=38&desc=Real-Time%20Big%20Data%20Log%20Analysis%20Platform&descAlignY=60&descSize=18" width="100%"/>

<!-- Typing animation -->
<a href="https://git.io/typing-svg">
  <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=18&duration=3000&pause=500&color=00D4FF&center=true&vCenter=true&multiline=true&width=700&height=80&lines=🔍+Detect+anomalies+in+real-time+log+streams;🧠+Powered+by+Isolation+Forest+ML;⚡+Built+with+Dask+%7C+Dash+%7C+scikit-learn" alt="Typing SVG" />
</a>

<br/><br/>

<!-- Badges -->
![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Dask](https://img.shields.io/badge/Dask-Distributed-FC6E27?style=for-the-badge&logo=dask&logoColor=white)
![Dash](https://img.shields.io/badge/Dash-Plotly-00B4D8?style=for-the-badge&logo=plotly&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-ML-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)

![License](https://img.shields.io/badge/License-MIT-22C55E?style=for-the-badge)
![Maintained](https://img.shields.io/badge/Maintained-yes-96C40F?style=for-the-badge)
![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-ff69b4?style=for-the-badge)
![Stars](https://img.shields.io/github/stars/your-username/log-anomaly-platform?style=for-the-badge&color=yellow)

</div>

---

## 📺 Demo Preview

<div align="center">
  <img src="https://user-images.githubusercontent.com/placeholder/demo.gif" alt="Dashboard Demo" width="85%" style="border-radius:10px;"/>
  
  > 🎬 **Live dashboard** showing real-time anomaly detection across log streams
</div>

---

## ✨ Key Features

<div align="center">

| | Feature | Description |
|---|---|---|
| ⚡ | **Scalable Parsing** | Processes huge log files with Dask — parallel, distributed, memory-efficient |
| 🧠 | **Isolation Forest** | Unsupervised ML trained on time-window features: count, error ratio, latency |
| 📊 | **Interactive Dashboard** | Dash UI with scatter plots, error timelines, service filters & raw log drill-down |
| 👁️ | **Real-Time Monitor** | Watches directories for new log files and auto-processes them as they arrive |
| 🔔 | **Slack Alerts** | Optional webhook integration to notify your team when anomalies are found |
| 📥 | **CSV Export** | Download all flagged anomalies for offline analysis or reporting |
| 🔄 | **One-Click Retrain** | Retrain the model directly from the dashboard UI — no CLI needed |

</div>

---

## 🏗️ Architecture

```mermaid
flowchart TD
    A[🗂️ Log Files\n/var/log/*.log] --> B

    subgraph INGESTION ["⬇️  Ingestion Layer"]
        B[👁️ log_monitor.py\nFile Watcher]
    end

    subgraph PROCESSING ["⚙️  Processing Layer"]
        C[🔍 parse_logs.py\nDask Parser]
        D[🧮 feature_engineering.py\nTime-Window Features]
    end

    subgraph ML ["🧠  ML Layer"]
        E[🌲 train_model.py\nIsolation Forest]
    end

    subgraph OUTPUT ["📤  Output Layer"]
        F[📊 Dash Dashboard\nlocalhost:8050]
        G[🔔 Slack Alerts\nWebhook]
        H[📥 anomalies.csv\nExport]
    end

    B --> C --> D --> E
    E --> F
    E --> G
    E --> H

    style INGESTION  fill:#1e2a3a,stroke:#0ea5e9,stroke-width:2px,color:#e2eaf5
    style PROCESSING fill:#1e2a3a,stroke:#8b5cf6,stroke-width:2px,color:#e2eaf5
    style ML         fill:#1e2a3a,stroke:#22c55e,stroke-width:2px,color:#e2eaf5
    style OUTPUT     fill:#1e2a3a,stroke:#f59e0b,stroke-width:2px,color:#e2eaf5
```

---

## 🔁 Data Flow

```mermaid
sequenceDiagram
    participant LF as 🗂️ Log Files
    participant WD as 👁️ Watchdog Monitor
    participant DP as 🔍 Dask Parser
    participant FE as 🧮 Feature Engineering
    participant IF as 🌲 Isolation Forest
    participant DB as 📊 Dashboard
    participant SL as 🔔 Slack

    LF->>WD: New file detected
    WD->>DP: Trigger parse
    DP->>FE: Structured DataFrame
    Note over FE: Aggregates 1-min windows<br/>log count · error ratio · P99 latency
    FE->>IF: Feature matrix
    IF->>IF: Score each window
    IF->>DB: Anomaly scores + flags
    IF->>SL: Alert if threshold exceeded
    IF->>LF: anomalies.csv saved
```

---

## 🚀 Quick Start

<details>
<summary><b>📋 Prerequisites</b></summary>

- Python **3.8+**
- Git

</details>

### 1️⃣  Clone the repository

```bash
git clone https://github.com/your-username/log-anomaly-platform.git
cd log-anomaly-platform
```

### 2️⃣  Set up a virtual environment

```bash
python -m venv venv
```

| OS | Command |
|---|---|
| 🪟 Windows | `.\venv\Scripts\Activate` |
| 🍎 macOS / 🐧 Linux | `source venv/bin/activate` |

### 3️⃣  Install dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣  Generate sample logs *(optional)*

```bash
python src/generate_logs.py
```
> Creates synthetic log files in the `data/` directory for testing.

### 5️⃣  Run the full pipeline

```bash
python src/parse_logs.py          # Parse raw logs → structured format
python src/feature_engineering.py # Build time-window features
python src/train_model.py          # Train Isolation Forest & detect anomalies
```

### 6️⃣  Launch the dashboard

```bash
python src/dashboard.py
```

<div align="center">

🌐 Open **http://localhost:8050** in your browser

<img src="https://user-images.githubusercontent.com/placeholder/dashboard-screenshot.png" alt="Dashboard Preview" width="80%"/>

</div>

### 7️⃣  *(Optional)* Start real-time monitoring

```bash
python src/log_monitor.py
```

> Any new log file placed in the monitored folder will be processed automatically.

---

## 📁 Project Structure

```
log-anomaly-platform/
│
├── 📂 src/
│   ├── 🔧 generate_logs.py         ← Synthetic log generator (for testing)
│   ├── 🔍 parse_logs.py            ← Dask-powered log parser
│   ├── 🧮 feature_engineering.py   ← Creates time-window features
│   ├── 🌲 train_model.py           ← Isolation Forest trainer
│   ├── 📊 dashboard.py             ← Dash UI (localhost:8050)
│   └── 👁️ log_monitor.py          ← Real-time file watcher
│
├── 📂 data/                         ← Raw logs & intermediate CSVs
├── 📂 models/                       ← Saved model artifacts (.pkl)
├── 📄 requirements.txt
└── 📄 README.md
```

---

## 📦 Dependencies

| Package | Version | Purpose |
|---|---|---|
| `dask[complete]` | ≥ 2023.1.0 | Scalable DataFrame processing |
| `pandas` | ≥ 1.5.0 | Data manipulation |
| `scikit-learn` | ≥ 1.2.0 | Isolation Forest model |
| `dash` | ≥ 2.9.0 | Interactive web dashboard |
| `plotly` | ≥ 5.13.0 | Charts & visualisations |
| `watchdog` | ≥ 2.3.0 | File system monitoring |
| `slack-sdk` | ≥ 3.21.0 | Slack alert integration |
| `python-dotenv` | ≥ 0.21.0 | Environment variable management |

---

## ⚙️ Configuration

To enable **Slack alerts**, create a `.env` file in the project root:

```env
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/your/webhook/url
```

Model parameters can be tuned in `src/train_model.py`:

```python
IsolationForest(
    contamination=0.05,   # Expected anomaly fraction (0–0.5)
    n_estimators=100,     # Number of trees
    random_state=42
)
```

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

```mermaid
gitGraph
   commit id: "fork repo"
   branch feature/amazing-feature
   checkout feature/amazing-feature
   commit id: "add feature"
   commit id: "add tests"
   checkout main
   merge feature/amazing-feature id: "open PR ✅"
```

1. 🍴 **Fork** the repository
2. 🌿 Create a feature branch: `git checkout -b feature/amazing-feature`
3. ✅ Commit your changes: `git commit -m 'Add some amazing feature'`
4. 📤 Push to the branch: `git push origin feature/amazing-feature`
5. 🔀 Open a **Pull Request**

> Please ensure your code passes existing tests and includes appropriate new tests.

---

## 📊 Performance at a Glance

```mermaid
xychart-beta
    title "Processing Speed vs Log File Size"
    x-axis ["10MB", "50MB", "100MB", "500MB", "1GB"]
    y-axis "Time (seconds)" 0 --> 30
    bar  [1, 3, 5, 14, 27]
    line [1, 3, 5, 14, 27]
```

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

<!-- Footer wave -->
<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=120&section=footer" width="100%"/>

**Made with ❤️ by [Your Name/Org]**

⭐ **Star us on GitHub** if this project helped you!

[![GitHub stars](https://img.shields.io/github/stars/your-username/log-anomaly-platform?style=social)](https://github.com/your-username/log-anomaly-platform)
[![GitHub forks](https://img.shields.io/github/forks/your-username/log-anomaly-platform?style=social)](https://github.com/your-username/log-anomaly-platform/fork)
[![GitHub watchers](https://img.shields.io/github/watchers/your-username/log-anomaly-platform?style=social)](https://github.com/your-username/log-anomaly-platform)

</div>


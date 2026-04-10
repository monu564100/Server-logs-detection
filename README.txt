Log Anomaly Platform - Study Notes
==================================

1) What this project currently does
-----------------------------------
This project detects suspicious behavior (possible attacks) from Linux log data.
It performs an end-to-end pipeline:

Step 1: Parse raw Linux logs
Step 2: Build time-window features
Step 3: Train Isolation Forest model
Step 4: Predict attack/normal windows
Step 5: Show results in dashboard (including critical IPs)
Step 6: Export anomaly report to Excel


2) Main model used
------------------
Model: IsolationForest (unsupervised anomaly detection)
Library: scikit-learn
Model usage: trained and used directly in-memory during pipeline run

Why Isolation Forest:
- Works without labeled attack/normal ground truth
- Finds outlier windows compared to normal behavior
- Good baseline for log anomaly detection

Supporting preprocessing:
- StandardScaler (fit and used in-memory during pipeline run)


3) Dataset used for training
----------------------------
Primary training source (current):
- data/Linux.log

Pipeline behavior:
- If data/Linux.log exists, it is used directly (priority)
- Otherwise local logs in data/ are used (*.log, *.txt, *.out)
- You can also pass a custom local file/folder using --input

Current verified source behavior:
- The parser prints source file path(s)
- Parsed source counts are printed
- Parsed rows currently come from local data sources


4) Training logic and feature logic
-----------------------------------
Input file:
- data/Linux.log

Parsing output:
- data/parsed_logs.parquet

Parsed columns:
- timestamp
- service
- level
- message
- ip
- source_file

Feature engineering output:
- data/features.parquet

Time bin size:
- 5-minute windows

Feature columns used for training:
- log_count
- error_ratio
- warn_ratio
- avg_message_len
- unique_services
- unique_ips

Training output:
- data/features_with_anomaly.parquet

Prediction columns produced:
- anomaly (Isolation Forest output)
- anomaly_score
- attack_prediction (Attack or Normal)
- severity (Critical, High, Medium, Normal)
- prediction_confidence_pct
- prediction_accuracy_level_pct

Training report output:
- data/training_report.json (model type, parameters, training window counts)


5) Attack prediction behavior
-----------------------------
Since this is unsupervised learning, there are no true labels in Linux.log.
So project logic does:

- Uses Isolation Forest raw predictions
- Adds fallback rule to mark top-risk windows if model returns too few anomalies
- Creates attack_prediction label from anomaly output
- Assigns severity tiers based on anomaly score ranking

Important:
- prediction_accuracy_level_pct is an estimated model quality indicator
- It is not supervised test accuracy (no labeled ground truth available)


6) Critical IP logic
--------------------
Critical IPs are derived from windows predicted as Attack.
Dashboard computes IP stats for logs in attack windows and ranks them.

Critical IP indicators include:
- number of logs from IP in attack windows
- number of ERROR logs from IP in attack windows
- weighted attack score for ranking


7) Files that are core to current working system
-------------------------------------------------
- server.py
- src/pipeline.py
- src/dashboard.py
- data/Linux.log

Generated artifacts:
- data/parsed_logs.parquet
- data/features.parquet
- data/features_with_anomaly.parquet
- data/anomalies.xlsx


8) How to run
-------------
Recommended single command:
- python server.py

This executes in order:
1) python src/pipeline.py
2) python src/dashboard.py


9) Dashboard outputs
--------------------
Dashboard shows:
- Total logs
- Total predicted attack windows
- Attack percentage
- Unique IPs
- Critical IPs
- Prediction Accuracy Level
- Avg Prediction Confidence

Tabs include:
- Volume and Anomalies
- Error Ratio
- Top IPs
- Critical IPs

Also includes:
- Raw logs in selected anomaly window (with IP)
- Excel export button for anomaly report


10) Notes for future improvement
--------------------------------
If you want more realistic security detection quality, next upgrades can be:
- Add labeled benchmark data for true accuracy evaluation
- Add attack type classification rules (scan, brute force, privilege escalation)
- Add sequence-based models (LSTM/Transformer) for event order patterns
- Add per-service baseline models instead of single global model
- Add drift detection for changing log patterns

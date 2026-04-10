# Log Anomaly Platform

This project runs an end-to-end Linux log anomaly detection flow.

## Dataset priority

1. Primary dataset: `data/Linux.log` (local real dataset)
2. Fallback only if local file is missing: `omduggineni/loghub-linux-log-data` via `kagglehub`

## Install

```bash
pip install -r requirements.txt
```

## Run full sequence

```bash
python server.py
```

`server.py` runs:

1. `python src/parse_logs.py`
2. `python src/feature_engineering.py`
3. `python src/train_model.py`
4. `python src/dashboard.py`

## Main outputs

- `data/parsed_logs.parquet`
- `data/features.parquet`
- `data/features_with_anomaly.parquet`
- `data/anomalies.xlsx`

## Study guide

Detailed explanation of model, dataset, logic, and training is in `README.txt`.

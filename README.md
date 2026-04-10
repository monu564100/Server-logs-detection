# Log Anomaly Platform

This project runs an end-to-end Linux log anomaly detection flow.

## Dataset source

Training is done on your own local logs.

Default source:
1. `data/Linux.log`
2. If missing, any local `data/*.log` / `data/*.txt` / `data/*.out`

Optional custom source:
- pass `--input` with your log file or folder path.

## Install

```bash
pip install -r requirements.txt
```

## Run full sequence

```bash
python server.py
```

`server.py` runs:

1. `python src/pipeline.py`
2. `python src/dashboard.py`

You can also run only the pipeline directly:

```bash
python src/pipeline.py
```

Train with your own file/folder and custom Isolation Forest settings:

```bash
python src/pipeline.py --input data/Linux.log --contamination 0.05 --n-estimators 200 --random-state 42
```

Training summary is exported to:
- `data/training_report.json`
4. `python src/dashboard.py`

## Main outputs

- `data/parsed_logs.parquet`
- `data/features.parquet`
- `data/features_with_anomaly.parquet`
- `data/anomalies.xlsx`

## Study guide

Detailed explanation of model, dataset, logic, and training is in `README.txt`.

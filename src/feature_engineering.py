import dask.dataframe as dd
import pandas as pd
from dask.diagnostics import ProgressBar

# Load parsed logs (timestamp is a column, not index)
ddf = dd.read_parquet('data/parsed_logs.parquet')

# Convert to pandas for feature engineering (small enough)
df = ddf.compute()

# Verify timestamp is datetime
df['timestamp'] = pd.to_datetime(df['timestamp'])

# Create 5-minute time bins
df['time_bin'] = df['timestamp'].dt.floor('5min')

# Aggregate features
features = df.groupby('time_bin').agg(
    log_count=('message', 'count'),
    error_ratio=('level', lambda x: (x == 'ERROR').mean()),
    warn_ratio=('level', lambda x: (x == 'WARN').mean()),
    avg_message_len=('message', lambda x: x.str.len().mean()),
    unique_services=('service', 'nunique')
).reset_index()

# Save features
features.to_parquet('data/features.parquet', index=False)
print("Features saved to data/features.parquet")

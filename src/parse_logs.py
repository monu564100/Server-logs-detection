import dask.dataframe as dd
import pandas as pd
from dask.diagnostics import ProgressBar

ddf = dd.read_csv('data/sample_logs.log', header=None, names=['raw'], blocksize='100MB')
pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+)\s+(\S+)\s+(\w+):\s+(.*)'
extracted = ddf['raw'].str.extract(pattern, expand=True)
extracted.columns = ['timestamp', 'service', 'level', 'message']
ddf_parsed = extracted.dropna()
ddf_parsed['timestamp'] = dd.to_datetime(ddf_parsed['timestamp'])
with ProgressBar():
    ddf_parsed.to_parquet('data/parsed_logs.parquet')

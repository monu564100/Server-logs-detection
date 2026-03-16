import dash
from dash import dcc, html, Input, Output, callback_context
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
import joblib
import base64
import io
import subprocess
import os
from datetime import datetime

# Load data
df_features = pd.read_parquet('data/features_with_anomaly.parquet')
df_logs = pd.read_parquet('data/parsed_logs.parquet')
model = joblib.load('models/isolation_forest.pkl')
scaler = joblib.load('models/scaler.pkl')

services = ['All'] + sorted(df_logs['service'].unique().tolist())

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Log Anomaly Detection Dashboard", style={'text-align': 'center'}),

    # Summary cards
    html.Div([
        html.Div([
            html.H4("Total Logs"),
            html.H2(id='total-logs')
        ], className='card', style={'display': 'inline-block', 'margin': '10px', 'padding': '10px', 'border': '1px solid #ddd'}),
        html.Div([
            html.H4("Total Anomalies"),
            html.H2(id='total-anomalies')
        ], className='card', style={'display': 'inline-block', 'margin': '10px', 'padding': '10px', 'border': '1px solid #ddd'}),
        html.Div([
            html.H4("Anomaly %"),
            html.H2(id='anomaly-percent')
        ], className='card', style={'display': 'inline-block', 'margin': '10px', 'padding': '10px', 'border': '1px solid #ddd'}),
    ], style={'text-align': 'center'}),

    # Buttons
    html.Div([
        html.Button("Export Anomalies as CSV", id="btn-export"),
        dcc.Download(id="download-anomalies"),
        html.Button("Retrain Model", id="btn-retrain", style={'margin-left': '20px'}),
        html.Div(id='retrain-status')
    ], style={'margin': '20px'}),

    # Auto-refresh interval
    dcc.Interval(id='interval-component', interval=60*1000, n_intervals=0),  # 60 seconds

    # Service filter
    html.Label("Filter by Service:"),
    dcc.Dropdown(
        id='service-dropdown',
        options=[{'label': s, 'value': s} for s in services],
        value='All',
        clearable=False,
        style={'width': '300px', 'margin-bottom': '20px'}
    ),

    dcc.Tabs(id='tabs', value='tab-1', children=[
        dcc.Tab(label='Log Volume & Anomalies', value='tab-1'),
        dcc.Tab(label='Error Rate Over Time', value='tab-2'),
    ]),

    html.Div(id='tab-content'),

    # Raw logs section
    html.Hr(),
    html.H3("Raw Logs for Selected Anomaly Window"),
    html.Label("Select a time window (from top anomalies):"),
    dcc.Dropdown(id='window-dropdown', options=[], value=None),
    html.Div(id='raw-logs-output', style={'white-space': 'pre-wrap', 'font-family': 'monospace', 'max-height': '400px', 'overflow-y': 'scroll'})
])

# Callback to refresh data on interval
@app.callback(
    [Output('total-logs', 'children'),
     Output('total-anomalies', 'children'),
     Output('anomaly-percent', 'children'),
     Output('tab-content', 'children', allow_duplicate=True),
     Output('window-dropdown', 'options', allow_duplicate=True)],
    [Input('interval-component', 'n_intervals'),
     Input('service-dropdown', 'value'),
     Input('tabs', 'value')],
    prevent_initial_call=True
)
def refresh_data(n, selected_service, tab):
    # Reload data
    df_features_new = pd.read_parquet('data/features_with_anomaly.parquet')
    df_logs_new = pd.read_parquet('data/parsed_logs.parquet')
    
    # Update global variables (not ideal, but works for demo)
    global df_features, df_logs
    df_features = df_features_new
    df_logs = df_logs_new

    total_logs = f"{len(df_logs):,}"
    total_anomalies = (df_features['anomaly'] == -1).sum()
    anomaly_percent = f"{((df_features['anomaly'] == -1).mean() * 100):.1f}%"

    # Update tab content
    if tab == 'tab-1':
        tab_content = render_volume_tab(selected_service)
    elif tab == 'tab-2':
        tab_content = render_error_tab(selected_service)

    # Update dropdown options
    top_anomalies = df_features.nsmallest(10, 'anomaly_score')[['time_bin']]
    dropdown_options = [{'label': str(row['time_bin']), 'value': str(row['time_bin'])} 
                        for _, row in top_anomalies.iterrows()]

    return total_logs, total_anomalies, anomaly_percent, tab_content, dropdown_options

def render_volume_tab(selected_service):
    fig = go.Figure()
    normal = df_features[df_features['anomaly'] == 1]
    fig.add_trace(go.Scatter(x=normal['time_bin'], y=normal['log_count'],
                             mode='markers', name='Normal',
                             marker=dict(color='blue', size=4)))
    anomalous = df_features[df_features['anomaly'] == -1]
    fig.add_trace(go.Scatter(x=anomalous['time_bin'], y=anomalous['log_count'],
                             mode='markers', name='Anomaly',
                             marker=dict(color='red', size=8, symbol='x')))
    fig.update_layout(title=f'Log Count per 5-min Window (Service: {selected_service})',
                      xaxis_title='Time', yaxis_title='Number of Logs')

    top_anomalies = df_features.nsmallest(10, 'anomaly_score')[['time_bin', 'log_count', 'error_ratio', 'anomaly_score']]
    table = html.Table([
        html.Thead(html.Tr([html.Th(col) for col in top_anomalies.columns]))
    ] + [
        html.Tr([html.Td(str(top_anomalies.iloc[i][col])) for col in top_anomalies.columns])
        for i in range(len(top_anomalies))
    ])

    return html.Div([
        dcc.Graph(figure=fig),
        html.H4("Top Anomalous Windows"),
        table
    ])

def render_error_tab(selected_service):
    df_error = df_features[['time_bin', 'error_ratio']].copy()
    fig = px.line(df_error, x='time_bin', y='error_ratio', title='Error Ratio Over Time')
    if selected_service != 'All':
        fig.update_layout(title=f'Error Ratio Over Time (Service: {selected_service})')
    return dcc.Graph(figure=fig)

# Callback for dropdown updates (triggered by service filter or interval)
@app.callback(
    Output('window-dropdown', 'options'),
    [Input('service-dropdown', 'value'),
     Input('interval-component', 'n_intervals')]
)
def update_dropdown(selected_service, _):
    top_anomalies = df_features.nsmallest(10, 'anomaly_score')[['time_bin']]
    dropdown_options = [{'label': str(row['time_bin']), 'value': str(row['time_bin'])} 
                        for _, row in top_anomalies.iterrows()]
    return dropdown_options

# Callback for raw logs
@app.callback(
    Output('raw-logs-output', 'children'),
    [Input('window-dropdown', 'value'),
     Input('service-dropdown', 'value')]
)
def display_raw_logs(selected_window, selected_service):
    if selected_window is None:
        return "Select a time window to view raw logs."
    
    selected_time = pd.to_datetime(selected_window)
    start_time = selected_time
    end_time = selected_time + pd.Timedelta(minutes=5)
    
    mask = (df_logs['timestamp'] >= start_time) & (df_logs['timestamp'] < end_time)
    if selected_service != 'All':
        mask &= (df_logs['service'] == selected_service)
    
    logs_in_window = df_logs[mask]
    
    if logs_in_window.empty:
        return "No logs found in this window with selected filter."
    
    log_lines = []
    for _, row in logs_in_window.iterrows():
        log_lines.append(f"{row['timestamp']} {row['service']} {row['level']}: {row['message']}")
    
    return html.Pre('\n'.join(log_lines))

# Export anomalies as CSV
@app.callback(
    Output("download-anomalies", "data"),
    Input("btn-export", "n_clicks"),
    prevent_initial_call=True
)
def export_anomalies(n_clicks):
    df_anomalies = df_features[df_features['anomaly'] == -1].copy()
    return dcc.send_data_frame(df_anomalies.to_csv, "anomalies.csv")

# Retrain model
@app.callback(
    Output('retrain-status', 'children'),
    Input('btn-retrain', 'n_clicks'),
    prevent_initial_call=True
)
def retrain_model(n_clicks):
    try:
        # Run retrain.py script
        result = subprocess.run(['python', 'src/retrain.py'], capture_output=True, text=True)
        if result.returncode == 0:
            return html.Div("✅ Model retrained successfully!", style={'color': 'green'})
        else:
            return html.Div(f"❌ Retrain failed: {result.stderr}", style={'color': 'red'})
    except Exception as e:
        return html.Div(f"❌ Error: {str(e)}", style={'color': 'red'})

if __name__ == '__main__':
    app.run(debug=True)

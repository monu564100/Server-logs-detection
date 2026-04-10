from __future__ import annotations

from pathlib import Path

import dash
from dash import Input, Output, dcc, html
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go

from pipeline import (
    ANOMALY_XLSX_FILE,
    FEATURES_ANOMALY_FILE,
    PARSED_FILE,
    export_anomalies_to_excel,
    run_full_pipeline,
)


def ensure_pipeline_outputs() -> None:
    if FEATURES_ANOMALY_FILE.exists() and PARSED_FILE.exists():
        return
    print("Running full pipeline: parse -> features -> train -> excel export")
    run_full_pipeline()


def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    features = pd.read_parquet(FEATURES_ANOMALY_FILE)
    logs = pd.read_parquet(PARSED_FILE)
    features["time_bin"] = pd.to_datetime(features["time_bin"], errors="coerce")
    logs["timestamp"] = pd.to_datetime(logs["timestamp"], errors="coerce")
    if "ip" not in logs.columns:
        logs["ip"] = "Unknown"
    if "attack_prediction" not in features.columns:
        features["attack_prediction"] = features["anomaly"].map({-1: "Attack", 1: "Normal"}).fillna("Normal")
    if "severity" not in features.columns:
        features["severity"] = features["attack_prediction"].map({"Attack": "High", "Normal": "Normal"}).fillna("Normal")
    if "prediction_confidence_pct" not in features.columns:
        features["prediction_confidence_pct"] = 60.0
    if "prediction_accuracy_level_pct" not in features.columns:
        features["prediction_accuracy_level_pct"] = 60.0
    return features, logs


ensure_pipeline_outputs()
df_features, df_logs = load_data()

services = ["All"] + sorted(df_logs["service"].dropna().unique().tolist())

app = dash.Dash(__name__)

app.layout = html.Div(
    [
        html.H1("Log Anomaly Detection Dashboard", style={"text-align": "center"}),
        html.P(
            "Pipeline order: parse logs -> build features -> train model -> show results.",
            style={"text-align": "center", "color": "#444"},
        ),
        html.Div(
            [
                html.Div(
                    [html.H4("Total Logs"), html.H2(id="total-logs")],
                    style={"display": "inline-block", "margin": "8px", "padding": "12px", "border": "1px solid #ddd"},
                ),
                html.Div(
                    [html.H4("Total Anomalies"), html.H2(id="total-anomalies")],
                    style={"display": "inline-block", "margin": "8px", "padding": "12px", "border": "1px solid #ddd"},
                ),
                html.Div(
                    [html.H4("Anomaly %"), html.H2(id="anomaly-percent")],
                    style={"display": "inline-block", "margin": "8px", "padding": "12px", "border": "1px solid #ddd"},
                ),
                html.Div(
                    [html.H4("Unique IPs"), html.H2(id="total-ips")],
                    style={"display": "inline-block", "margin": "8px", "padding": "12px", "border": "1px solid #ddd"},
                ),
                html.Div(
                    [html.H4("Critical IPs"), html.H2(id="critical-ips")],
                    style={"display": "inline-block", "margin": "8px", "padding": "12px", "border": "1px solid #ddd"},
                ),
                html.Div(
                    [html.H4("Prediction Accuracy Level"), html.H2(id="prediction-accuracy")],
                    style={"display": "inline-block", "margin": "8px", "padding": "12px", "border": "1px solid #ddd"},
                ),
                html.Div(
                    [html.H4("Avg Prediction Confidence"), html.H2(id="prediction-confidence")],
                    style={"display": "inline-block", "margin": "8px", "padding": "12px", "border": "1px solid #ddd"},
                ),
            ],
            style={"text-align": "center"},
        ),
        html.Div(
            [
                html.Button("Refresh Pipeline", id="btn-refresh"),
                html.Button("Export Anomalies to Excel", id="btn-export", style={"margin-left": "12px"}),
                dcc.Download(id="download-excel"),
                html.Div(id="pipeline-status", style={"margin-top": "12px"}),
            ],
            style={"margin": "20px 0"},
        ),
        dcc.Interval(id="interval-component", interval=60 * 1000, n_intervals=0),
        html.Label("Filter by Service:"),
        dcc.Dropdown(
            id="service-dropdown",
            options=[{"label": s, "value": s} for s in services],
            value="All",
            clearable=False,
            style={"width": "320px", "margin-bottom": "16px"},
        ),
        dcc.Tabs(
            id="tabs",
            value="tab-1",
            children=[
                dcc.Tab(label="Volume & Anomalies", value="tab-1"),
                dcc.Tab(label="Error Ratio", value="tab-2"),
                dcc.Tab(label="Top IPs", value="tab-3"),
                dcc.Tab(label="Critical IPs", value="tab-4"),
            ],
        ),
        html.Div(id="tab-content"),
        html.Hr(),
        html.H3("Raw Logs for Selected Anomaly Window (Includes IP)"),
        dcc.Dropdown(id="window-dropdown", options=[], value=None),
        html.Div(id="raw-logs-output", style={"white-space": "pre-wrap", "font-family": "monospace", "max-height": "380px", "overflow-y": "scroll"}),
    ],
    style={"padding": "20px"},
)


def current_data(selected_service: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    features = df_features.copy()
    logs = df_logs.copy()
    if selected_service != "All":
        logs = logs[logs["service"] == selected_service].copy()
        if not logs.empty:
            logs["time_bin"] = logs["timestamp"].dt.floor("5min")
            valid_bins = logs["time_bin"].unique()
            features = features[features["time_bin"].isin(valid_bins)].copy()
    return features, logs


def render_volume_tab(features: pd.DataFrame) -> html.Div:
    fig = go.Figure()
    normal = features[features["attack_prediction"] == "Normal"]
    anomalous = features[features["attack_prediction"] == "Attack"]

    fig.add_trace(
        go.Scatter(
            x=normal["time_bin"],
            y=normal["log_count"],
            mode="markers",
            name="Normal",
            marker={"color": "#1f77b4", "size": 5},
        )
    )
    fig.add_trace(
        go.Scatter(
            x=anomalous["time_bin"],
            y=anomalous["log_count"],
            mode="markers",
            name="Anomaly",
            marker={"color": "#d62728", "size": 9, "symbol": "x"},
        )
    )
    fig.update_layout(title="Log Count per 5-minute Window", xaxis_title="Time", yaxis_title="Log Count")

    top = features.nsmallest(10, "anomaly_score")[
        ["time_bin", "log_count", "error_ratio", "unique_ips", "anomaly_score", "severity", "attack_prediction"]
    ]
    table = html.Table(
        [html.Thead(html.Tr([html.Th(col) for col in top.columns]))]
        + [
            html.Tr([html.Td(str(top.iloc[i][col])) for col in top.columns])
            for i in range(len(top))
        ]
    )

    return html.Div([dcc.Graph(figure=fig), html.H4("Top Anomaly Windows"), table])


def render_error_tab(features: pd.DataFrame) -> dcc.Graph:
    fig = px.line(features, x="time_bin", y="error_ratio", title="Error Ratio Over Time")
    return dcc.Graph(figure=fig)


def render_ip_tab(logs: pd.DataFrame) -> html.Div:
    known_ips = logs[logs["ip"] != "Unknown"] if "ip" in logs.columns else logs.iloc[0:0]
    if known_ips.empty:
        return html.Div("No concrete IPs found in current filter.")

    ip_counts = known_ips.groupby("ip").size().reset_index(name="count").sort_values("count", ascending=False).head(15)
    fig = px.bar(ip_counts, x="ip", y="count", title="Top IPs by Log Volume")
    return html.Div([dcc.Graph(figure=fig)])


def render_critical_ip_tab(features: pd.DataFrame, logs: pd.DataFrame) -> html.Div:
    attack_windows = set(features.loc[features["attack_prediction"] == "Attack", "time_bin"].tolist())
    if not attack_windows:
        return html.Div("No attack windows found in current view.")

    logs = logs.copy()
    logs["time_bin"] = logs["timestamp"].dt.floor("5min")
    critical_logs = logs[(logs["time_bin"].isin(attack_windows)) & (logs["ip"] != "Unknown")]
    if critical_logs.empty:
        return html.Div("No concrete critical IPs found in attack windows.")

    ip_stats = (
        critical_logs.groupby("ip")
        .agg(log_count=("message", "count"), error_count=("level", lambda x: (x == "ERROR").sum()))
        .reset_index()
        .sort_values(["error_count", "log_count"], ascending=False)
        .head(20)
    )
    ip_stats["attack_score"] = ip_stats["error_count"] * 2 + ip_stats["log_count"]
    fig = px.bar(ip_stats, x="ip", y="attack_score", title="Critical IPs (from predicted attack windows)")

    table = html.Table(
        [html.Thead(html.Tr([html.Th(col) for col in ip_stats.columns]))]
        + [
            html.Tr([html.Td(str(ip_stats.iloc[i][col])) for col in ip_stats.columns])
            for i in range(len(ip_stats))
        ]
    )
    return html.Div([dcc.Graph(figure=fig), html.H4("Critical IP Table"), table])


@app.callback(
    [
        Output("total-logs", "children"),
        Output("total-anomalies", "children"),
        Output("anomaly-percent", "children"),
        Output("total-ips", "children"),
        Output("critical-ips", "children"),
        Output("prediction-accuracy", "children"),
        Output("prediction-confidence", "children"),
        Output("tab-content", "children"),
        Output("window-dropdown", "options"),
    ],
    [Input("interval-component", "n_intervals"), Input("service-dropdown", "value"), Input("tabs", "value")],
)
def refresh_view(_, selected_service: str, tab: str):
    features, logs = current_data(selected_service)

    total_logs = f"{len(logs):,}"
    anomalies = int((features["attack_prediction"] == "Attack").sum()) if not features.empty else 0
    anomaly_percent = f"{((features['attack_prediction'] == 'Attack').mean() * 100):.1f}%" if not features.empty else "0.0%"
    unique_ips = logs.loc[logs["ip"] != "Unknown", "ip"].nunique() if not logs.empty else 0

    logs_with_bin = logs.copy()
    logs_with_bin["time_bin"] = logs_with_bin["timestamp"].dt.floor("5min") if not logs_with_bin.empty else pd.Series(dtype="datetime64[ns]")
    attack_bins = set(features.loc[features["attack_prediction"] == "Attack", "time_bin"].tolist())
    critical_ips = logs_with_bin[(logs_with_bin["time_bin"].isin(attack_bins)) & (logs_with_bin["ip"] != "Unknown")]["ip"].nunique() if not logs_with_bin.empty else 0
    prediction_accuracy = float(features["prediction_accuracy_level_pct"].iloc[0]) if not features.empty else 0.0
    prediction_confidence = float(features["prediction_confidence_pct"].mean()) if not features.empty else 0.0

    if tab == "tab-2":
        tab_content = render_error_tab(features)
    elif tab == "tab-3":
        tab_content = render_ip_tab(logs)
    elif tab == "tab-4":
        tab_content = render_critical_ip_tab(features, logs)
    else:
        tab_content = render_volume_tab(features)

    top_anomalies = features.nsmallest(min(10, len(features)), "anomaly_score")[["time_bin"]] if not features.empty else pd.DataFrame(columns=["time_bin"])
    options = [{"label": str(row["time_bin"]), "value": str(row["time_bin"])} for _, row in top_anomalies.iterrows()]
    return (
        total_logs,
        f"{anomalies:,}",
        anomaly_percent,
        f"{unique_ips:,}",
        f"{critical_ips:,}",
        f"{prediction_accuracy:.1f}%",
        f"{prediction_confidence:.1f}%",
        tab_content,
        options,
    )


@app.callback(
    Output("raw-logs-output", "children"),
    [Input("window-dropdown", "value"), Input("service-dropdown", "value")],
)
def render_raw_logs(selected_window: str | None, selected_service: str):
    if not selected_window:
        return "Select an anomaly window to view logs with IP addresses."

    start = pd.to_datetime(selected_window)
    end = start + pd.Timedelta(minutes=5)

    logs = df_logs.copy()
    mask = (logs["timestamp"] >= start) & (logs["timestamp"] < end)
    if selected_service != "All":
        mask &= logs["service"] == selected_service

    subset = logs[mask]
    if subset.empty:
        return "No logs found for this window and service filter."

    lines = [
        f"{row.timestamp} {row.service} {row.level} ip={row.ip}: {row.message}"
        for row in subset.itertuples(index=False)
    ]
    return html.Pre("\n".join(lines))


@app.callback(
    Output("download-excel", "data"),
    Input("btn-export", "n_clicks"),
    prevent_initial_call=True,
)
def download_excel(_):
    path = export_anomalies_to_excel(df_features, df_logs)
    return dcc.send_file(str(path))


@app.callback(
    Output("pipeline-status", "children"),
    Input("btn-refresh", "n_clicks"),
    prevent_initial_call=True,
)
def rerun_pipeline(_):
    global df_features, df_logs
    try:
        run_full_pipeline()
        df_features, df_logs = load_data()
        return html.Div("Pipeline rerun completed: parse -> features -> train -> dashboard refreshed.", style={"color": "green"})
    except Exception as exc:
        return html.Div(f"Pipeline rerun failed: {exc}", style={"color": "red"})


if __name__ == "__main__":
    app.run(debug=True)

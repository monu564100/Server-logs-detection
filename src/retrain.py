import pandas as pd
import joblib
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

print("Loading features...")
df = pd.read_parquet('data/features.parquet')

feature_cols = ['log_count', 'error_ratio', 'warn_ratio', 'avg_message_len', 'unique_services']
X = df[feature_cols].fillna(0)

print("Scaling features...")
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

print("Training Isolation Forest...")
model = IsolationForest(contamination=0.05, random_state=42)
model.fit(X_scaled)

print("Saving model and scaler...")
joblib.dump(model, 'models/isolation_forest.pkl')
joblib.dump(scaler, 'models/scaler.pkl')

# Update features_with_anomaly
df['anomaly'] = model.predict(X_scaled)
df['anomaly_score'] = model.decision_function(X_scaled)
df.to_parquet('data/features_with_anomaly.parquet', index=False)

print("Retraining complete.")

import random
import time
from datetime import datetime, timedelta

LOG_LEVELS = ["INFO", "WARN", "ERROR", "DEBUG"]
SERVICES = ["auth", "kernel", "app", "database", "network"]
MESSAGES = {
    "INFO": ["User logged in", "Request processed", "Cache hit"],
    "WARN": ["Slow response", "Disk usage > 80%", "Retrying connection"],
    "ERROR": ["Connection refused", "Out of memory", "File not found"],
    "DEBUG": ["Debugging detail", "Variable value: x=42"]
}

def generate_log_line(timestamp):
    level = random.choices(LOG_LEVELS, weights=[70, 15, 5, 10])[0]
    service = random.choice(SERVICES)
    msg = random.choice(MESSAGES[level])
    if random.random() < 0.02:  # 2% anomaly
        if level != "ERROR":
            level = "ERROR"
            msg = "CRITICAL: " + random.choice(MESSAGES["ERROR"])
        else:
            msg = msg + " (repeated 100 times)"
    return f"{timestamp} {service} {level}: {msg}"

start = datetime.now() - timedelta(days=7)
with open("data/sample_logs.log", "w") as f:
    for i in range(100000):
        ts = start + timedelta(seconds=i*6)
        f.write(generate_log_line(ts) + "\n")

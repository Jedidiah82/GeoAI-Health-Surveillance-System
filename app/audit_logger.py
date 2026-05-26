import os
import csv
from datetime import datetime

LOG_FILE = "logs/audit_log.csv"


def log_event(user_role, action, district=None):
    os.makedirs("logs", exist_ok=True)

    file_exists = os.path.isfile(LOG_FILE)

    with open(LOG_FILE, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        if not file_exists:
            writer.writerow(["timestamp", "user_role", "action", "district"])

        writer.writerow([
            datetime.now().isoformat(timespec="seconds"),
            user_role,
            action,
            district
        ])
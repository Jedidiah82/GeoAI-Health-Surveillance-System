import os
import shutil
from datetime import datetime

SOURCE_FILE = "data/geoai_surveillance_outputs.csv"
BACKUP_FOLDER = "data/refresh_backups"
LOG_FILE = "logs/refresh_log.csv"


def simulate_refresh():
    os.makedirs(BACKUP_FOLDER, exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    backup_file = os.path.join(
        BACKUP_FOLDER,
        f"geoai_surveillance_outputs_backup_{timestamp}.csv"
    )

    if os.path.exists(SOURCE_FILE):
        shutil.copy2(SOURCE_FILE, backup_file)

    file_exists = os.path.isfile(LOG_FILE)

    with open(LOG_FILE, "a", encoding="utf-8") as log:
        if not file_exists:
            log.write("timestamp,action,source_file,backup_file\n")

        log.write(
            f"{datetime.now().isoformat(timespec='seconds')},"
            f"scheduled_refresh_simulated,"
            f"{SOURCE_FILE},"
            f"{backup_file}\n"
        )

    return {
        "status": "success",
        "message": "Scheduled refresh simulation completed",
        "backup_file": backup_file
    }
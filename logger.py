import datetime
import os

LOG_LEVELS = {"Trace": 0, "Info": 1, "Debug": 2}


class Logger:
    def __init__(self, log_file_path="app.log", level="Info"):
        self.log_file_path = log_file_path
        self.level = level

        # Ensure the log directory exists
        os.makedirs(os.path.dirname(self.log_file_path), exist_ok=True) if os.path.dirname(self.log_file_path) else None

    def log(self, message, level="Info"):
        if LOG_LEVELS[level] > LOG_LEVELS[self.level]:
            return  # Skip messages below current log level

        timestamp = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")

        if level == "Trace":
            full_message = f"{timestamp} [{level}] {message}"
        else:
            full_message = f"{timestamp} [{level}] \t{message}"

        try:
            with open(self.log_file_path, "a", encoding="utf-8") as f:
                f.write(full_message + "\n")
        except Exception as e:
            print(f"Logging failed: {e}")

    def set_level(self, level):
        if level in LOG_LEVELS:
            self.level = level

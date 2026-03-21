import logging
import os
from datetime import datetime


class ToolLogger:

    def __init__(self):

        os.makedirs("logs", exist_ok=True)

        log_file = os.path.join(
            "logs",
            f"tool_{datetime.now().strftime('%Y%m%d')}.log"
        )

        self.logger = logging.getLogger("GraphTool")

        if not self.logger.handlers:
            self.logger.setLevel(logging.INFO)

            formatter = logging.Formatter(
                "%(asctime)s | %(levelname)s | %(message)s"
            )

            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setFormatter(formatter)

            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)

            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)

    def info(self, msg):
        self.logger.info(msg)

    def warning(self, msg):
        self.logger.warning(msg)

    def error(self, msg):
        self.logger.error(msg)
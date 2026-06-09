import logging
from pathlib import Path


LOG_DIR = Path("log")
LOG_FILE = LOG_DIR / "ssh_key_gen.log"


def setup_logging():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        encoding="utf-8",
    )


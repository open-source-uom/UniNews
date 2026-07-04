from pathlib import Path

APP_NAME = "UniNews"

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"
FEEDS_FILE = DATA_DIR / "feeds.json"

APP_DATA_DIR = BASE_DIR / ".local_data"
APP_DATA_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_PATH = APP_DATA_DIR / "uninews.db"

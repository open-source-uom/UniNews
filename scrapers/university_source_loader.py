import json
from pathlib import Path

from settings import DATA_DIR

UNIVERSITY_LISTS_DIR = DATA_DIR / "university_lists"


def load_university_source_config(file_name: str) -> dict:
    config_path = UNIVERSITY_LISTS_DIR / file_name

    if not config_path.exists():
        raise FileNotFoundError(f"Missing university source list: {config_path}")

    with open(config_path, "r", encoding="utf-8") as file:
        config = json.load(file)

    validate_university_source_config(config, config_path)

    return config


def validate_university_source_config(config: dict, config_path: Path) -> None:
    if "university" not in config:
        raise ValueError(f"{config_path} is missing 'university'")

    if "sources" not in config:
        raise ValueError(f"{config_path} is missing 'sources'")

    if not isinstance(config["sources"], list):
        raise ValueError(f"{config_path}: 'sources' must be a list")

    required_fields = [
        "label",
        "base_url",
        "first_page",
        "item_selector",
        "title_selector",
    ]

    for index, source in enumerate(config["sources"], start=1):
        for field in required_fields:
            if not source.get(field):
                raise ValueError(f"{config_path}: source #{index} is missing '{field}'")

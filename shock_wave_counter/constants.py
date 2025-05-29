"""Constants for the Shock Wave Counter application."""

from pathlib import Path

APP_NAME: str = "shock_wave_counter"
DEFAULT_DB_DIR: Path = Path.home() / ".local" / "share" / APP_NAME
DEFAULT_DB_FILE: Path = DEFAULT_DB_DIR / "strikes.db"

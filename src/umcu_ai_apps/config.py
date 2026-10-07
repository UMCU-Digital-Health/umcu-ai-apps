import os
import tomllib
from importlib.metadata import version
from logging.config import dictConfig
from pathlib import Path


def configure_logging() -> None:
    """Configure logging for the application."""

    config_folder = Path(__file__).parents[2] / "config"

    config_path = (
        config_folder / "logging.plain.toml"
        if "CONNECT_SERVER" in os.environ
        else config_folder / "logging.rich.toml"
    )

    with config_path.open("rb") as file:
        config = tomllib.load(file)

    dictConfig(config)


VERSION = version("umcu-ai-apps")

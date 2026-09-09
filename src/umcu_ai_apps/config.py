import tomllib
from importlib.metadata import version
from logging.config import dictConfig
from pathlib import Path


def configure_logging() -> None:
    """Configure logging for the application."""
    config_path = Path(__file__).parents[2] / "config" / "logging_config.toml"

    with config_path.open("rb") as file:
        config = tomllib.load(file)

    dictConfig(config)


VERSION = version("umcu-ai-apps")

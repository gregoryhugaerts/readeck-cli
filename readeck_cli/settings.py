"""Settings for the program."""

from typing import Self

from attrs import define
from dotenv import dotenv_values, set_key
from pyreadeck import PyReadeck
from rich.prompt import Prompt


@define(kw_only=True)
class Settings:
    """App Settings."""

    api_key: str
    base_url: str

    @classmethod
    def load(cls) -> Self:
        """Load settings from env file or prompt for missing values."""
        settings = dotenv_values()
        if not settings.get("base_url"):
            settings["base_url"] = Prompt.ask("Readeck URL: ")
            set_key(".env", "base_url", settings["base_url"])  # type: ignore[arg-type]
        if not settings.get("api_key"):
            username = Prompt.ask("Username: ")
            password = Prompt.ask("Password: ", password=True)
            settings["api_key"] = PyReadeck.authenticate(
                settings["base_url"],  # type: ignore[arg-type]
                "pyreadeck",
                username,
                password,
            )
            set_key(".env", "api_key", settings["api_key"])  # type: ignore[arg-type]
        return cls(api_key=settings["api_key"], base_url=settings["base_url"])  # type: ignore[arg-type]

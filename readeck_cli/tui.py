from typing import Any, Callable, ClassVar

import httpx
from textual.app import App, ComposeResult
from textual.binding import BindingType
from textual.screen import Screen
from textual.widgets import (
    Footer,
    Header,
    Label,
    ListItem,
    ListView,
    MarkdownViewer,
)

from pyreadeck import PyReadeck
from settings import Settings

_SETTINGS = Settings.load()
_CLIENT = PyReadeck(_SETTINGS.api_key, _SETTINGS.base_url)


class Bookmarks(ListView):
    def on_mount(self) -> None:
        self._get_bookmarks()
        self.extend([ListItem(Label(bookmark.title)) for bookmark in self._bookmarks])

    def _get_bookmarks(self):
        try:
            self._bookmarks = _CLIENT.bookmarks()
        except (httpx.ConnectTimeout, httpx.ConnectError):
            self._bookmarks = []

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        selected = self._bookmarks[event.list_view.index]
        article = self.app.query_one(Article)
        article.loading = True
        md = self._get_article(selected)
        if  md:
            article.document.update(str(md))
            self.app.action_focus_next()
        article.loading = False

    def _get_article(self, selected):
        try:
            md = _CLIENT.bookmark_export(selected.id, "md")
        except (httpx.ConnectTimeout, httpx.ConnectError):
            md = None
        return md


class Article(MarkdownViewer):
    DEFAULT_CSS = """
    Article {
        max-height: 70vh;
    }
    """
    BINDINGS: ClassVar[list[BindingType]] = [("q", "close", "Close")]

    def action_close(self) -> None:
        self.document.update("")
        bookmarks = self.app.query_one(Bookmarks)
        bookmarks.focus()


class MainScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield Bookmarks()
        yield Article()


class SettingsScreen(Screen):
    pass


class ReadeckApp(App):
    BINDINGS: ClassVar[list[BindingType]] = [("q", "quit", "Quit")]
    SCREENS: ClassVar[dict[str, Callable[[], Screen[Any]]]] = {
        "main": MainScreen,
        "settings": SettingsScreen,
    }

    def on_mount(self) -> None:
        self.theme = "solarized-light"

    def on_ready(self) -> None:
        self.push_screen("main")

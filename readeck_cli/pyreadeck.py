"""Wrapper for readeck API and associated classes."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003
from enum import Enum, unique
from typing import Literal
from urllib.parse import urljoin

import httpx
from attrs import define, field
from cattrs.preconf.json import make_converter


@unique
class BookmarkType(Enum):
    """Type of bookmark contents."""

    ARTICLE = "article"
    PHOTO = "photo"
    VIDEO = "video"


@unique
class SortEnum(Enum):
    """Sort options."""

    CREATED = "created"
    CREATED_DESC = "-created"
    DOMAIN = "domain"
    DOMAIN_DESC = "-domain"
    DURATION = "duration"
    DURATION_DESC = "-duration"
    PUBLISHED = "published"
    PUBLISHED_DESC = "-published"
    SITE = "site"
    SITE_DESC = "-site"
    TITLE = "title"
    TITLE_DESC = "-title"


@define
class BookmarkFilter:
    """Filter options for bookmark list."""

    limit: int | None = None
    offset: int | None = None
    sort: list[SortEnum] | None = None
    search: str | None = None
    title: str | None = None
    author: str | None = None
    site: str | None = None
    type: BookmarkType | None = None
    labels: str | None = None
    is_marked: bool | None = None
    is_archived: bool | None = None
    range_start: str | None = None
    range_end: str | None = None
    id: str | None = None
    collection: str | None = None


@define
class Bookmark:
    """Readeck bookmark."""

    authors: list[str]
    created: datetime
    description: str
    document_type: str
    has_article: bool
    href: str
    id: str
    is_archived: bool
    is_deleted: bool
    is_marked: bool
    labels: list[str]
    lang: str
    loaded: bool
    resources: dict[str, str]
    site: str
    site_name: str
    state: int
    text_direction: str
    title: str
    type: BookmarkType
    updated: datetime
    url: str
    published: bool | None = None


@define
class PyReadeck:
    """Readeck API wrapper."""

    _api_key: str
    _base_url: str
    _converter = make_converter()
    _client: httpx.Client = field(init=False)

    def __attrs_post_init__(self):
        self._client = httpx.Client(
            base_url=urljoin(self._base_url, "/api/"),
            headers=self._get_headers(),
            timeout=5,
        )

    @classmethod
    def authenticate(
        cls,
        base_url: str,
        application: str,
        username: str,
        password: str,
    ) -> str:
        """Make a new application token."""
        url = urljoin(base_url, "/api/auth")
        authdata = {
            "application": application,
            "username": username,
            "password": password,
        }
        r = httpx.post(url, json=authdata)
        r.raise_for_status()
        return r.json()["token"]

    def _get_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._api_key}"}

    def _get_response(
        self,
        path: str,
        params: dict[str, str] | None = None,
    ) -> httpx.Response:
        r = self._client.get(
            path,
            params=params,
        )
        r.raise_for_status()
        return r

    def bookmarks(self, filter_options: BookmarkFilter | None = None) -> list[Bookmark]:
        """Get a `Bookmark` list."""
        if filter_options:
            filter_options = self._converter.unstructure(filter_options)
            # remove None values
            filter_options = {k: v for k, v in filter_options.items() if v is not None}  # type: ignore[assignment,union-attr]
        r = self._get_response("bookmarks", filter_options)  # type: ignore[arg-type]
        return self._converter.structure(r.json(), list[Bookmark])

    def bookmark(self, bookmark_id: str) -> Bookmark:
        """Get `Bookmark` details."""
        r = self._get_response(f"/bookmark/{bookmark_id}")
        return self._converter.structure(r.json(), Bookmark)

    def create_bookmark(
        self,
        url: str,
        labels: list[str] | None = None,
        title: str | None = None,
    ) -> dict[str, str]:
        data = {"labels": labels, "title": title, "url": url}
        r = self._client.post("/bookmarks", json=data)
        r.raise_for_status()
        return r.json()

    def delete_bookmark(self, bookmark_id: str) -> None:
        """Delete `Bookmark`."""
        r = self._client.delete(f"/bookmark/{bookmark_id}")
        r.raise_for_status()

    def bookmark_export(
        self,
        bookmark_id: str,
        output_format: Literal["md", "epub"],
    ) -> str | bytes:
        """Export bookmark as markdown or epub."""
        path = f"bookmarks/{bookmark_id}/article.{output_format}"
        r = self._get_response(path)
        if output_format == "md":
            return r.text
        return r.content

"""
Author and Authors — model objects for a translation author's identity
and the collection of authors within a single Repository.

`Repository` keeps its public `add_author`/`remove_author`/`update_author`/
`clean_authors` methods (no breaking change for existing callers); their
implementation delegates to `Authors`, which operates directly on the
existing `repository["authors"]` StrictNestedDictionary section — there is
no parallel storage to keep in sync.

`Authors` is intentionally stateless: email lookups scan
`repository["authors"]` rather than maintaining a separate index. Each
Repository (e.g. Config's `package` and `application`) has its own,
independent author set; cross-repository email deduplication, when
needed, is the caller's responsibility (see Config.add_author), not
something `Authors` enforces on its own.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, TypedDict, cast, overload
from uuid import UUID

from ndict_tools import StrictNestedDictionary
from ndict_tools.exception import StackedValueError

from .._checks import ensure_type
from .._compat import override
from .._json import JSONInput

if TYPE_CHECKING:
    from .repository import Repository


class AuthorPayload(TypedDict):
    """
    An author as a plain mapping, as read from a settings file.

    :meth:`Author.from_payload` checks a raw payload against this shape.
    """

    first_name: str
    last_name: str
    email: str
    url: str
    languages: list[str]


class Author(StrictNestedDictionary):
    """
    Represents a single author: identity and link to translation languages.

    Subclasses StrictNestedDictionary, exactly like Repository, so that
    nested-key access, serialization (to_dict, inherited) and storage
    inside a Repository's `authors` section behave consistently with the
    rest of the model layer.

    The five fields are given together, or none of them: ndict-tools copies
    an author by building an empty one with ``Author(default_setup=...)``
    and filling its keys. An empty author is meant for that use only.
    """

    @overload
    def __init__(
        self,
        first_name: str,
        last_name: str,
        email: str,
        url: str,
        languages: list[str],
        *,
        default_setup: Mapping[str, object] | None = None,
    ) -> None: ...

    @overload
    def __init__(
        self, *, default_setup: Mapping[str, object] | None = None
    ) -> None: ...

    def __init__(
        self,
        first_name: str | None = None,
        last_name: str | None = None,
        email: str | None = None,
        url: str | None = None,
        languages: list[str] | None = None,
        *,
        default_setup: Mapping[str, object] | None = None,
    ) -> None:
        fields = (first_name, last_name, email, url, languages)
        if all(field is None for field in fields):
            super().__init__(default_setup=default_setup)
            return
        if (
            first_name is None
            or last_name is None
            or email is None
            or url is None
            or languages is None
        ):
            names = ("first_name", "last_name", "email", "url", "languages")
            absent = [name for name, field in zip(names, fields) if field is None]
            raise TypeError(
                "Author takes first_name, last_name, email, url and languages "
                + f"together, or none of them; missing: {', '.join(absent)}"
            )
        ensure_type(languages, list, "author['languages'] must be a list of strings")
        super().__init__(default_setup=default_setup)
        self["first_name"] = first_name
        self["last_name"] = last_name
        self["email"] = email
        self["url"] = url
        self["languages"] = languages

    @classmethod
    def from_payload(
        cls, data: object, *, default_setup: Mapping[str, object] | None = None
    ) -> "Author":
        """Validate and build an Author from a plain mapping.

        ``data`` is a raw payload, typically read from a settings file: any
        value is accepted and checked here.

        Preserves the exact validation contract previously enforced by
        Repository's private ``_validate_author_payload`` (same exception
        types and messages).
        """
        if not isinstance(data, dict):
            raise TypeError("author must be a dictionary")
        required = {"first_name", "last_name", "email", "url", "languages"}
        missing = required - set(data.keys())
        if missing:
            raise KeyError(f"author is missing required keys: {sorted(missing)}")
        ensure_type(
            data["languages"], list, "author['languages'] must be a list of strings"
        )
        return cls(
            first_name=data["first_name"],
            last_name=data["last_name"],
            email=data["email"],
            url=data["url"],
            languages=data["languages"],
            default_setup=default_setup,
        )

    @override
    @classmethod
    def from_dict(
        cls, dictionary: Mapping[str, object], **class_options: object
    ) -> "Author":
        """
        Build an author from a plain mapping through :meth:`from_payload`.

        Overrides _StackedDict.from_dict(), which would build an empty
        author and copy the keys without checking them. Pickle goes through
        this method too, so an unpickled author is checked like a payload.
        """
        setup = class_options.get("default_setup")
        ensure_type(
            setup, (Mapping, type(None)), "default_setup must be a mapping or None"
        )
        # Checked just above: a mapping of settings, or None.
        return cls.from_payload(
            dictionary, default_setup=cast("Mapping[str, object] | None", setup)
        )


def _validate_uuid4_string(value: str, name: str = "author_id") -> None:
    """Validate that a value is a UUID4 string; raise consistent errors."""
    ensure_type(value, str, f"{name} must be a string")
    try:
        parsed = UUID(value)
    except ValueError:
        raise ValueError(f"{name} must be a valid UUID4 string")
    if parsed.version != 4:
        raise ValueError(f"{name} must be a valid UUID4 string")


class Authors:
    """Manager for the `authors` section of a single Repository."""

    @staticmethod
    def add(repository: "Repository", author_id: str, author: Author) -> None:
        _validate_uuid4_string(author_id)
        if author_id in repository["authors"].keys():
            raise ValueError(f"Author '{author_id}' already exists")
        repository[["authors", author_id]] = author

    @staticmethod
    def remove(repository: "Repository", author_id: str) -> None:
        _validate_uuid4_string(author_id)
        if author_id not in repository["authors"].keys():
            raise ValueError(f"Author '{author_id}' does not exist")
        del repository["authors"][author_id]

    @staticmethod
    def update(
        repository: "Repository", author_id: str, updates: dict[str, JSONInput]
    ) -> None:
        _validate_uuid4_string(author_id)
        ensure_type(updates, dict, "updates must be a dictionary")
        if author_id not in repository["authors"].keys():
            raise ValueError(f"Author '{author_id}' does not exist")
        current = repository[["authors", author_id]]
        for key, value in updates.items():
            if key not in current.keys():
                raise KeyError(f"Key '{key}' is not a valid field for author")
            if type(value) is not type(current[key]):
                raise TypeError(
                    f"Type mismatch for '{key}': expected {type(current[key])}, got {type(value)}"
                )
            current[key] = value

    @staticmethod
    def get_id_by_email(repository: StrictNestedDictionary, email: str) -> str | None:
        """Find the author UUID owning the given email.

        Uses ndict-tools' own value-search primitive (ancestors(), a DFS
        over the tree) instead of a manual scan: the email value's
        ancestry path, excluding its own key, is exactly the author_id.
        """
        try:
            ancestry = repository["authors"].ancestors(email)
        except StackedValueError:
            return None
        return ancestry[-1] if ancestry else None

    @staticmethod
    def clean(repository: "Repository") -> None:
        repository["authors"] = StrictNestedDictionary()

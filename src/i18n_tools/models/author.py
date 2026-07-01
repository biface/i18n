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

from typing import TYPE_CHECKING, Any
from uuid import UUID

from ndict_tools import StrictNestedDictionary
from ndict_tools.exception import StackedValueError

if TYPE_CHECKING:
    from .repository import Repository

_DEFAULT_SETUP = {"indent": 2}


class Author(StrictNestedDictionary):
    """
    Represents a single author: identity and link to translation languages.

    Subclasses StrictNestedDictionary, exactly like Repository, so that
    nested-key access, serialization (to_dict, inherited) and storage
    inside a Repository's `authors` section behave consistently with the
    rest of the model layer.
    """

    def __init__(
        self,
        first_name: str,
        last_name: str,
        email: str,
        url: str,
        languages: list[str],
    ) -> None:
        if not isinstance(languages, list):
            raise TypeError("author['languages'] must be a list of strings")
        super().__init__(default_setup=_DEFAULT_SETUP)
        self["first_name"] = first_name
        self["last_name"] = last_name
        self["email"] = email
        self["url"] = url
        self["languages"] = languages

    @classmethod
    def from_payload(cls, data: dict[str, Any]) -> "Author":
        """Validate and build an Author from a plain mapping.

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
        return cls(
            first_name=data["first_name"],
            last_name=data["last_name"],
            email=data["email"],
            url=data["url"],
            languages=data["languages"],
        )

    @classmethod
    def from_dict(cls, dictionary: dict[str, Any], **class_options) -> "Author":
        """
        Override of _StackedDict.from_dict() — the recursive-construction
        hook documented in ndict-tools' Extending guide. Author's __init__
        has a domain-specific signature incompatible with the generic
        cls(**class_options) reconstruction the base implementation
        performs, so this redirects to from_payload() instead. Closes a
        latent trap: without this override, Author would crash if ever
        reconstructed through that generic path (e.g. as a default_factory
        for a nested structure), exactly as it did before this fix.
        """
        return cls.from_payload(dictionary)


def _validate_uuid4_string(value: str, name: str = "author_id") -> None:
    """Validate that a value is a UUID4 string; raise consistent errors."""
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
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
        repository: "Repository", author_id: str, updates: dict[str, Any]
    ) -> None:
        _validate_uuid4_string(author_id)
        if not isinstance(updates, dict):
            raise TypeError("updates must be a dictionary")
        if author_id not in repository["authors"].keys():
            raise ValueError(f"Author '{author_id}' does not exist")
        current = repository[["authors", author_id]]
        for key, value in updates.items():
            if key not in current.keys():
                raise KeyError(f"Key '{key}' is not a valid field for author")
            if type(value) != type(current[key]):
                raise TypeError(
                    f"Type mismatch for '{key}': expected {type(current[key])}, got {type(value)}"
                )
            current[key] = value

    @staticmethod
    def get_id_by_email(repository: "Repository", email: str) -> str | None:
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
        repository["authors"] = repository._new_section({})

"""
Fallback Module
===============

This module resolves the ordered chain of language tags to consult when a
requested language is only partially translated. It turns the language
hierarchy declared in a Repository into a concrete, ordered list of
language tags — nothing more. It performs no I/O and knows nothing about
Message, Book, or Corpus; it produces data for those layers to consume.

Key Responsibilities:
    - Resolve a requested language tag into an ordered fallback chain.
    - Consult a Repository's declared hierarchy and global fallback
      language to build that chain.
    - Stay a pure, side-effect-free function — no filesystem access, no
      dependency on the content model (Message/Book/Corpus).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import langcodes

from .locale import normalize_language_tag

if TYPE_CHECKING:
    from .models.repository import Repository


def resolve(lang: str, repository: "Repository") -> list[str]:
    """
    Resolve the ordered fallback chain for a requested language.

    Algorithm:
        1. The requested language itself (normalized).
        2. Its IETF parent tag (e.g. ``fr`` for ``fr-CH``), if different.
        3. Language variants declared under that parent in
           ``repository.hierarchy`` (e.g. ``fr-FR``, ``fr-BE`` under
           ``fr``) — also consulted when the requested tag *is itself*
           a parent key.
        4. The repository's global fallback language
           (``repository.fallback``) and its own declared variants.

    Duplicates are dropped, first occurrence wins, so the returned list
    always starts with the (normalized) requested language and never
    repeats a tag.

    This function is pure: it only reads ``repository.hierarchy`` and
    ``repository.fallback``, performs no filesystem access, and does not
    know about Message, Book, or Corpus. Consumers (e.g.
    ``Corpus.get_book()``) are responsible for turning the returned tags
    into actual loaded content and for deciding what happens if none of
    them are available.

    :param lang: Requested language tag (e.g. ``"fr-CH"``).
    :type lang: str
    :param repository: Repository whose ``hierarchy``/``fallback`` declare
        the resolution rules.
    :type repository: Repository
    :return: Ordered, de-duplicated list of language tags to try, always
        starting with the normalized requested language.
    :rtype: list[str]
    :raises ValueError: If ``lang`` is not a valid IETF language tag.
    """
    normalized = normalize_language_tag(lang)

    chain: list[str] = []
    seen: set[str] = set()

    def _add(tag: str) -> None:
        if tag and tag not in seen:
            chain.append(tag)
            seen.add(tag)

    # 1. Requested language
    _add(normalized)

    # 2. IETF parent tag, if different from the requested tag itself
    parent = langcodes.Language.get(normalized).language
    parent_tag = normalize_language_tag(parent) if parent else None
    if parent_tag and parent_tag != normalized:
        _add(parent_tag)

    # 3. Variants declared under the parent — or under the requested tag
    # itself, if the requested tag is already a parent key in hierarchy.
    lookup_key = parent_tag or normalized
    if lookup_key in repository.hierarchy:
        for variant in repository.hierarchy[lookup_key]:
            _add(variant)

    # 4. Global fallback language and its own declared variants
    global_fallback = repository.fallback
    if global_fallback:
        _add(global_fallback)
        if global_fallback in repository.hierarchy:
            for variant in repository.hierarchy[global_fallback]:
                _add(variant)

    return chain

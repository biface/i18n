"""
Encyclopaedia: the Corpora of a repository, keyed by module and domain.
"""

from i18n_tools._checks import ensure_type
from i18n_tools._compat import override
from i18n_tools.models.corpus import Corpus


class Encyclopaedia:
    """
    Collection of Corpora across all domains and modules of a repository.

    ``Encyclopaedia`` is keyed by ``(module, domain)`` pairs (DD-07).  Corpora
    are loaded lazily: a ``Corpus`` is inserted via ``add_corpus()`` and
    retrieved via ``get_corpus()``.  The lazy-loading hook (loading from disk
    on first access) is reserved for v1.0.0 once ``core.py`` is in place.

    References
    ----------
    - biface/i18n#42 : four-level model hierarchy (DD-07)
    """

    def __init__(self) -> None:
        """
        Initialise an empty Encyclopaedia.

        References
        ----------
        - biface/i18n#42 : four-level model hierarchy (DD-07)
        """
        # Key: (module, domain) -> Corpus
        self._corpora: dict[tuple[str, str], Corpus] = {}

    def add_corpus(self, module: str, corpus: Corpus) -> None:
        """
        Register a Corpus under ``(module, corpus.domain)``.

        :param module: Module identifier (e.g. ``"src/app"``).
        :type module: str
        :param corpus: Corpus to register.
        :type corpus: Corpus
        :raises TypeError: If ``module`` is not a string or ``corpus`` is not a Corpus.
        :raises ValueError: If a Corpus is already registered for ``(module, domain)``.

        References
        ----------
        - biface/i18n#42 : four-level model hierarchy (DD-07)
        """
        ensure_type(module, str, f"module must be a string, got {type(module)}")
        ensure_type(corpus, Corpus, f"Expected a Corpus instance, got {type(corpus)}")
        key = (module, corpus.domain)
        if key in self._corpora:
            raise ValueError(
                f"A Corpus for module='{module}', domain='{corpus.domain}' is already registered"
            )
        self._corpora[key] = corpus

    def get_corpus(self, module: str, domain: str) -> Corpus:
        """
        Retrieve the Corpus for ``(module, domain)``.

        :param module: Module identifier.
        :type module: str
        :param domain: Domain name.
        :type domain: str
        :return: The registered Corpus.
        :rtype: Corpus
        :raises KeyError: If no Corpus is registered for ``(module, domain)``.

        References
        ----------
        - biface/i18n#42 : four-level model hierarchy (DD-07)
        """
        key = (module, domain)
        if key not in self._corpora:
            raise KeyError(
                f"No Corpus registered for module='{module}', domain='{domain}'"
            )
        return self._corpora[key]

    def __contains__(self, key: tuple[str, str]) -> bool:
        """Return True if ``(module, domain)`` is registered."""
        return key in self._corpora

    def __len__(self) -> int:
        """Number of registered Corpora."""
        return len(self._corpora)

    @override
    def __repr__(self) -> str:
        keys = list(self._corpora.keys())
        return f"Encyclopaedia(corpora={keys})"

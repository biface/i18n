"""
Translator and Translators — model objects for an automatic translation
service entry (e.g. a paid API like Google Translate, DeepL) and the
collection of such services within a single Repository.

`Repository` keeps its public `add_translator`/`update_translator`/
`remove_translator`/`clean_translators` methods (no breaking change for
existing callers); their implementation delegates to `Translators`, which
operates directly on the existing `repository["translators"]`
StrictNestedDictionary section.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import TYPE_CHECKING, Any

from ndict_tools import StrictNestedDictionary

from .._checks import ensure_type
from .._compat import override
from ..api import validate_url_format

if TYPE_CHECKING:
    from .repository import Repository


class Translator(StrictNestedDictionary):
    """
    Represents a single automatic translation service entry.

    Subclasses StrictNestedDictionary, exactly like Repository and Author,
    so that nested-key access and serialization behave consistently with
    the rest of the model layer.
    """

    def __init__(
        self,
        details: dict[str, Any],
        pricing: dict[str, Any],
        technical: dict[str, Any],
        *,
        default_setup: Mapping[str, object] | None = None,
    ) -> None:
        payload = {"details": details, "pricing": pricing, "technical": technical}
        self.validate_payload(payload)
        super().__init__(default_setup=default_setup)
        self["details"] = StrictNestedDictionary(details)
        self["pricing"] = StrictNestedDictionary(pricing)
        self["technical"] = StrictNestedDictionary(technical)

    @classmethod
    def from_payload(cls, data: dict[str, Any]) -> "Translator":
        """Validate and build a Translator from a plain mapping."""
        cls.validate_payload(data)
        return cls(
            details=data["details"],
            pricing=data["pricing"],
            technical=data["technical"],
        )

    @override
    @classmethod
    def from_dict(
        cls, dictionary: dict[str, Any], **class_options: object
    ) -> "Translator":
        """
        Override of _StackedDict.from_dict() — see Author.from_dict() for
        the rationale (ndict-tools' Extending guide). Redirects to
        from_payload() instead of the incompatible generic
        cls(**class_options) reconstruction.
        """
        return cls.from_payload(dictionary)

    @staticmethod
    def validate_payload(translator: object) -> None:
        """Validate the structure of a translator mapping.

        ``translator`` is a raw payload, typically read from a settings file:
        any value is accepted and checked here.

        Expected nested structure and minimal type checks:
          - details: { name: str, status: str, url: str }
          - pricing: { cost_per_translation: float|int|None, payment_plan: str|None }
          - technical:
              api: { key: str, key_expiration: str|None|"", request_limit: int }
              performance: { max_text_size: int, priority: int, success_rate: float|int }

        Additionally validates details.url via validate_url_format (syntax
        only — no network call, KI-01/DD-NN) and checks key_expiration
        format YYYY-MM-DD when provided (non-empty).

        Preserves the exact validation contract previously enforced by
        Repository's private ``_validate_translator_payload`` (same
        exception types and messages).
        """
        if not isinstance(translator, dict):
            raise TypeError("Translator must be a dictionary")

        # Top-level required keys
        top_required = {"details", "pricing", "technical"}
        missing_top = top_required - set(translator.keys())
        if missing_top:
            raise KeyError(
                f"Translator is missing required keys: {sorted(missing_top)}"
            )

        # details validation
        details = translator.get("details")
        if not isinstance(details, dict):
            raise TypeError("Translator['details'] must be a dictionary")
        det_required = {"name", "status", "url"}
        missing_det = det_required - set(details.keys())
        if missing_det:
            raise KeyError(
                f"Translator['details'] is missing required keys: {sorted(missing_det)}"
            )
        if not isinstance(details.get("name"), str):
            raise TypeError("Translator[['details', 'name']] must be a string")
        if not isinstance(details.get("status"), str):
            raise TypeError("Translator[['details', 'status']] must be a string")
        if not isinstance(details.get("url"), str):
            raise TypeError("Translator[['details', 'url']] must be a string")
        # Structural validation only — no network call (KI-01, DD-NN).
        # The real availability check (api.validate_api_url) is invoked
        # explicitly elsewhere (Config/CLI), never from this synchronous path.
        url = details.get("url")
        if not isinstance(url, str):
            raise TypeError("Translator[['details', 'url']] must be a string")
        result = validate_url_format(url)

        if result.get("error"):
            raise ValueError(result["error"])

        # pricing validation
        pricing = translator.get("pricing")
        if not isinstance(pricing, dict):
            raise TypeError("Translator['pricing'] must be a dictionary")
        pr_required = {"cost_per_translation", "payment_plan"}
        missing_pr = pr_required - set(pricing.keys())
        if missing_pr:
            raise KeyError(
                f"Translator['pricing'] is missing required keys: {sorted(missing_pr)}"
            )
        cpt = pricing.get("cost_per_translation")
        if cpt is not None and not isinstance(cpt, (int, float)):
            raise TypeError(
                "Translator[['pricing', 'cost_per_translation']] must be a number or None"
            )
        plan = pricing.get("payment_plan")
        if plan is not None and not isinstance(plan, str):
            raise TypeError(
                "Translator[['pricing', 'payment_plan']] must be a string or None"
            )

        # technical validation
        technical = translator.get("technical")
        if not isinstance(technical, dict):
            raise TypeError("Translator['technical'] must be a dictionary")
        tech_required = {"api", "performance"}
        missing_tech = tech_required - set(technical.keys())
        if missing_tech:
            raise KeyError(
                f"Translator['technical'] is missing required keys: {sorted(missing_tech)}"
            )

        # technical.api
        api = technical.get("api")
        if not isinstance(api, dict):
            raise TypeError("Translator[['technical', 'api']] must be a dictionary")
        api_required = {"key", "key_expiration", "request_limit"}
        missing_api = api_required - set(api.keys())
        if missing_api:
            raise KeyError(
                f"Translator[['technical', 'api']] is missing required keys: {sorted(missing_api)}"
            )
        if not isinstance(api.get("key"), str):
            raise TypeError("Translator[['technical', 'api', 'key']] must be a string")
        key_exp = api.get("key_expiration")
        if key_exp is not None and not isinstance(key_exp, str):
            raise TypeError(
                "Translator[['technical', 'api', 'key_expiration']] must be a string or None"
            )
        if isinstance(key_exp, str) and key_exp.strip():
            try:
                _ = datetime.strptime(key_exp, "%Y-%m-%d")
            except ValueError:
                raise ValueError(
                    "Translator[['technical', 'api', 'key_expiration']] must be in 'YYYY-MM-DD' format"
                )
        if not isinstance(api.get("request_limit"), int):
            raise TypeError(
                "Translator[['technical', 'api', 'request_limit']] must be an integer"
            )

        # technical.performance
        perf = technical.get("performance")
        if not isinstance(perf, dict):
            raise TypeError(
                "Translator[['technical', 'performance']] must be a dictionary"
            )
        perf_required = {"max_text_size", "priority", "success_rate"}
        missing_perf = perf_required - set(perf.keys())
        if missing_perf:
            raise KeyError(
                f"Translator[['technical', 'performance']] is missing required keys: {sorted(missing_perf)}"
            )
        if not isinstance(perf.get("max_text_size"), int):
            raise TypeError(
                "Translator[['technical', 'performance', 'max_text_size']] must be an integer"
            )
        if not isinstance(perf.get("priority"), int):
            raise TypeError(
                "Translator[['technical', 'performance', 'priority']] must be an integer"
            )
        sr = perf.get("success_rate")
        if not isinstance(sr, (int, float)):
            raise TypeError(
                "Translator[['technical', 'performance', 'success_rate']] must be a number"
            )


class Translators:
    """Manager for the `translators` section of a single Repository."""

    @staticmethod
    def add(repository: "Repository", name: str, translator: dict[str, Any]) -> None:
        ensure_type(name, str, "Translator name must be a string")
        ensure_type(translator, dict, "Translator content must be a dictionary")

        translator_obj = Translator.from_payload(translator)

        if not isinstance(repository["translators"], StrictNestedDictionary):
            repository["translators"] = StrictNestedDictionary()

        if name in repository["translators"].keys():
            raise ValueError(f"Translator '{name}' already exists")

        repository[["translators", name]] = translator_obj

    @staticmethod
    def update(repository: "Repository", name: str, updates: dict[str, Any]) -> None:
        ensure_type(name, str, "name must be a string")
        ensure_type(updates, dict, "updates must be a dictionary")

        translators = repository["translators"]
        if name not in translators.keys():
            raise ValueError(f"Translator '{name}' does not exist")

        existing_translator = translators[name]

        def validate_and_apply(
            target: dict[str, Any], patch: dict[str, Any], path: str = ""
        ) -> None:
            for key, value in patch.items():
                full_path = f"{path}.{key}" if path else key
                if key not in target:
                    raise KeyError(
                        f"Key '{full_path}' is not a valid field for translator"
                    )
                if isinstance(target[key], dict):
                    if not isinstance(value, dict):
                        raise TypeError(
                            f"Type mismatch for '{full_path}': expected dict, got {type(value)}"
                        )
                    validate_and_apply(target[key], value, full_path)
                else:
                    if type(value) is not type(target[key]):
                        raise TypeError(
                            f"Type mismatch for '{full_path}': expected {type(target[key])}, got {type(value)}"
                        )
                    target[key] = value

        validate_and_apply(existing_translator, updates)

    @staticmethod
    def remove(repository: "Repository", name: str) -> None:
        ensure_type(name, str, "name must be a string")
        translators = repository["translators"]
        if name not in translators.keys():
            raise ValueError(f"Translator '{name}' does not exist")
        del translators[name]

    @staticmethod
    def clean(repository: "Repository") -> None:
        repository["translators"] = StrictNestedDictionary()

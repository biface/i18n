"""
Message: one identifier's translations and metadata, in one language.
"""

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal, TypedDict

from ndict_tools import StrictNestedDictionary

from i18n_tools.__static__ import __version__ as i18n_tools_version
from i18n_tools._checks import ensure_type, is_type
from i18n_tools._compat import override
from i18n_tools.converter import (
    i18n_tools_format_to_message_dict,
    message_to_i18n_tools_format,
)
from i18n_tools.locale import normalize_language_tag

if TYPE_CHECKING:
    from i18n_tools.formatter.plurals import PluralRule


class DeclensionFields(TypedDict, total=False):
    """
    Keyword contract for the texts of one declension.

    The same keys describe the principal and every variant.
    """

    singular: str
    plurals: list[str]


@dataclass(slots=True)
class Declension:
    """
    One singular text and zero or more plural texts.

    The principal of a message and each of its variants are declensions.
    Segment 0 is the singular, segments 1 to n are the plurals: a singular
    with three plurals has four segments. An empty string marks an absent
    text.

    :param singular: Text of segment 0.
    :type singular: str
    :param plurals: Texts of segments 1 to n, in order.
    :type plurals: list[str]
    :raises TypeError: If a text is not a string, or ``plurals`` is not a
        list.
    """

    singular: str = ""
    plurals: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        ensure_type(
            self.singular,
            str,
            f"Declension singular must be a string, got {type(self.singular)}",
        )
        ensure_type(
            self.plurals,
            list,
            f"Declension plurals must be a list, got {type(self.plurals)}",
        )
        for text in self.plurals:
            ensure_type(
                text, str, f"Declension plural must be a string, got {type(text)}"
            )

    @property
    def segments(self) -> list[str]:
        """
        All texts of the declension, singular first.

        :return: ``[singular, *plurals]``, a new list.
        :rtype: list[str]
        """
        return [self.singular, *self.plurals]

    @classmethod
    def from_segments(cls, segments: list[str]) -> "Declension":
        """
        Build a declension from its texts, singular first.

        :param segments: ``[singular, *plurals]``; must not be empty.
        :type segments: list[str]
        :return: The declension.
        :rtype: Declension
        :raises ValueError: If ``segments`` is empty.
        :raises TypeError: If ``segments`` is not a list, or a text is not
            a string.
        """
        ensure_type(
            segments, list, f"Declension segments must be a list, got {type(segments)}"
        )
        if len(segments) == 0:
            raise ValueError("A declension has at least one segment (the singular)")
        return cls(segments[0], list(segments[1:]))


def _ensure_coordinate(value: int | None, name: str) -> None:
    """Check an optional location coordinate: None or an int >= 0."""
    if value is None:
        return
    if is_type(value, bool) or not is_type(value, int):
        raise TypeError(f"Location {name} must be an int or None, got {type(value)}")
    if value < 0:
        raise ValueError(f"Location {name} must be >= 0, got {value}")


@dataclass(frozen=True, slots=True)
class Location:
    """
    A place in source code that uses a message.

    ``variant`` and ``segment`` locate the text the source code asks for,
    with the addressing of the message: ``variant=0`` is the principal,
    ``segment=0`` is the singular. A coordinate left to None is not fixed
    at that call site; a location with no coordinate refers to the whole
    message.

    :param file: Path of the source file.
    :type file: str
    :param line: Line number in that file, starting at 1.
    :type line: int
    :param variant: Declension used at that call site, if fixed.
    :type variant: int | None
    :param segment: Segment used at that call site, if fixed.
    :type segment: int | None
    :raises TypeError: If a field has the wrong type.
    :raises ValueError: If ``file`` is empty, ``line`` is below 1 or a
        coordinate is negative.
    """

    file: str
    line: int
    variant: int | None = None
    segment: int | None = None

    def __post_init__(self) -> None:
        ensure_type(
            self.file, str, f"Location file must be a string, got {type(self.file)}"
        )
        if self.file == "":
            raise ValueError("Location file must not be empty")
        if is_type(self.line, bool) or not is_type(self.line, int):
            raise TypeError(f"Location line must be an int, got {type(self.line)}")
        if self.line < 1:
            raise ValueError(f"Location line must be >= 1, got {self.line}")
        _ensure_coordinate(self.variant, "variant")
        _ensure_coordinate(self.segment, "segment")


def _check_index_dict(dictionary: dict[int, Any]) -> bool:
    """
    Validate that dictionary keys are within the range [1, len(dictionary)].

    Args:
        dictionary (dict[int, Any]): The dictionary to validate.

    Returns:
        bool: True if all keys are within the valid range, False otherwise.
    """
    for key in dictionary.keys():
        if key not in range(1, len(dictionary) + 1):
            return False
    return True


def _build_empty_metadata() -> StrictNestedDictionary:
    return StrictNestedDictionary(
        {
            "version": i18n_tools_version,
            "language": "",
            "location": [],
            "flags": ["python-format"],
            # "comments": {"user": [], "auto": []},
            "user_comments": [],
            "auto_comments": [],
            "count": {
                "singular": 0,
                "plurals": [],
            },
        },
        default_setup={"indent": 2},
    )


def extract_variables(text: str) -> list[str]:
    """
    Extract variable names from a formatted string.

    Args:
        text (str): The formatted string.

    Returns:
        list[str]: List of variable names.
    """
    # Find all {variable} patterns in the string
    pattern = r"\{([^{}]+)\}"
    return re.findall(pattern, text)


class Message:
    """
    A class for handling internationalization messages using the i18n_tools specifications.

    This class provides functionality to create, store, and format messages for
    internationalization purposes. It uses the native i18n_tools format for storing
    messages and supports formatting using f-strings with variables.

    **Terminology:**

        * message is the content of a translation and its options
        * translation is the list of singular message and its plurals, each element of the list is a *token*
        * alternative is a different *option* of the translation in the message
        * component  is a token inside a translation or an alternative
        * option is an alternative translation

        message va devenir translation,
        translation va devenir variant,
        component va devenir segment


    Attributes:

        id (str): A unique identifier assigned to each message, ensuring that messages can be easily referenced and managed within the translation system.
        default (str): The primary text of the message, serving as the default translation when no specific alternatives or plural forms are required.
        options (dict[int, str]): A collection of alternative translations that can be used in different contexts or scenarios, allowing for flexibility in message presentation based on specific needs.
        default_plurals (dict[int, str]): A set of translations that account for different pluralization rules, accommodating languages with multiple plural forms.
        options_plurals (dict[int, dict[int, str]]): Plural forms associated with alternative translations, providing comprehensive support for various linguistic pluralization requirements.
        context (str): Additional information that clarifies the usage context of the message, helping to disambiguate messages with similar or identical text. It is maintained for compatibility with other format.
        metadata (StrictNestedDictionary): The metadata attribute of the Message class contains detailed information about the translation, aiding in its management and usage. The structure of the metadata is as follows:

            - version (str): Indicates the version of the metadata structure, allowing for future changes in format while maintaining backward compatibility.
            - language (str): Is the IETF Language Tag code used in the message. It is built with language code library.
            - location (List[Tuple[int, str]]): A list of source file locations where the message is used, including the file path and line number. This helps in tracking the usage of the message within the codebase.
            - flags (list[str]): A set of indicators that provide additional information about the message, such as whether it is fuzzy or uses a specific format like Python-format.
            - comments (str): Notes or comments from translators, offering insights or additional context about the message.
            - count (dict[str, Any]): Counting translation of standard and alternatives.

                - singular (int): The number of times the singular form of the message is used, helping in understanding the frequency and importance of the message.
                - plurals (list[int]): A list of counts for the different plural forms of the message, providing information on the usage of each plural form.
    """

    id: str
    default: str
    options: dict[int, str]
    default_plurals: dict[int, str]
    options_plurals: StrictNestedDictionary
    context: str
    metadata: StrictNestedDictionary
    plural_rule: "PluralRule | None"

    def __check_plural_forms__(self, value: dict[int, str] | None = None) -> bool:
        """
        Check if the plural_forms attribute or the provided value has the correct data structure.

        Args:
            value (dict[int, str] | None, optional): The value to check. If None, checks self.plural_forms. Defaults to None.

        Returns:
            bool: True if the structure is valid, False otherwise.
        """
        # Determine which value to check
        data_to_check = value if value is not None else self.default_plurals

        return _check_index_dict(data_to_check)

    def __check_alternatives__(self, value: dict[int, str] | None = None) -> bool:
        """
        Check if the alternatives attribute or the provided value has the correct data structure.

        Args:
            value (dict[int, str] | None, optional): The value to check. If None, checks self.alternatives. Defaults to None.

        Returns:
            bool: True if the structure is valid, False otherwise.
        """
        # Determine which value to check
        data_to_check = value if value is not None else self.options

        # Check that all keys are integers and all values are strings
        return _check_index_dict(data_to_check)

    def __check_alternative_plural_forms__(
        self, value: dict[int, Any] | StrictNestedDictionary | None = None
    ) -> bool:
        """
        Check if the alternative_plural_forms attribute or the provided value has the correct data structure.

        Args:
            value (dict[int, Any] | StrictNestedDictionary | None, optional): The value to check. If None, checks self.alternative_plural_forms. Defaults to None.

        Returns:
            bool: True if the structure is valid, False otherwise.
        """

        # Determine which value to check
        data_to_check = value if value is not None else self.options_plurals
        __check = _check_index_dict(data_to_check)

        # Check that all keys are integers and all values are dictionaries
        if __check:
            for val in data_to_check.values():
                __check = _check_index_dict(val)

        return __check

    def __check_metadata__(self, value: dict[str, Any]) -> bool:
        """
        Check if the metadata attribute or the provided value has the correct data structure.

        Args:
            value (dict[str, Any] | None, optional): The value to check. If None, checks self.metadata. Defaults to None.

        Returns:
            bool: True if the structure is valid, False otherwise.
        """
        __check = True

        if isinstance(value, StrictNestedDictionary):
            paths = value.paths()
        else:
            paths = StrictNestedDictionary(value).paths()

        for path in paths:
            if path not in self.metadata.paths():
                __check = False

        return __check

    def __count_singular__(self) -> int:
        """
        Get the count of singulars in translation and alternatives.

        Returns:
            int: The count of presently stored singulars.
        """
        count = 1 if len(self.default) > 0 else 0
        count += len(self.options) if len(self.options) > 0 else 0

        return count

    def __count_plurals__(self) -> list[int]:
        """
        Get the list of plurals for each singular or alternative singular.

        Returns:
            list[int]: The list of count of plurals for each singular.
        """
        counts = [len(self.default_plurals)]
        for index in range(1, len(self.options) + 1):
            if index in self.options_plurals.keys():
                counts.append(len(self.options_plurals[index]))
            else:
                counts.append(0)

        return counts

    # --- Internal helpers for factorization ---
    def _assert_valid_option(self, option: int) -> None:
        """Ensure the given option index refers to an existing variant.

        Raises IndexError with a consistent message if out of range.
        """
        if not (0 < option <= len(self.options)):
            raise IndexError(f"The variant location ({option}) is out of range")

    def _assert_valid_token_in_option(self, option: int, index: int) -> None:
        """Ensure the given token index refers to an existing plural of an option.

        Expects the option to exist. Raises IndexError if token is out of range.
        """
        if not (0 < index <= len(self.options_plurals[option])):
            raise IndexError(
                f"The token location ({index}) of the variant location ({option}) is out of range"
            )

    def _assert_valid_default_plural_token(self, index: int) -> None:
        """Ensure the given token index refers to an existing default plural.
        Raises IndexError if token is out of range.
        """
        if not (0 < index <= len(self.default_plurals)):
            raise IndexError(f"The token location ({index}) is out of range")

    def _refresh_counts(self, singular: bool = False, plurals: bool = False) -> None:
        """Refresh metadata counts.
        If both flags are False, refresh both counts; otherwise refresh selected ones.
        """
        if not singular and not plurals:
            self.metadata[["count", "singular"]] = self.__count_singular__()
            self.metadata[["count", "plurals"]] = self.__count_plurals__()
            return
        if singular:
            self.metadata[["count", "singular"]] = self.__count_singular__()
        if plurals:
            self.metadata[["count", "plurals"]] = self.__count_plurals__()

    def __init__(
        self,
        id: str,
        default: str = "",
        options: dict[int, str] | None = None,
        default_plurals: dict[int, str] | None = None,
        options_plurals: dict[int, dict[int, str]] | None = None,
        context: str = "",
        metadata: dict[str, Any] | None = None,
    ):
        """
        Initialize a new Message instance.

        Args:
            id (str): The unique identifier for the message.
            default (str, optional): The main translation text. Defaults to "".
            options (dict[int, str], optional): Alternative translations. Defaults to None.
            default_plurals (dict[int, str], optional): Plural forms of the main translation. Defaults to None.
            options_plurals (dict[int, dict[int, str]], optional): Plural forms for alternative translations. Defaults to None.
            context (str, optional): Context information for the translation. Defaults to "".
            metadata (dict[str, Any], optional): Metadata about the translation. Defaults to None.
        """
        self.id = id
        self.default = default
        self.options = {}
        self.default_plurals = {}
        self.options_plurals = StrictNestedDictionary()
        self.context = context
        self.metadata = _build_empty_metadata()
        self.plural_rule = None

        # Process standard attributes with a parameterized loop

        for attr_name, attr_value, check_method in [
            ("options", options, self.__check_alternatives__),
            ("default_plurals", default_plurals, self.__check_plural_forms__),
            (
                "options_plurals",
                (
                    StrictNestedDictionary(options_plurals)
                    if options_plurals is not None and len(options_plurals) > 0
                    else None
                ),
                self.__check_alternative_plural_forms__,
            ),
        ]:
            if attr_value is not None:
                if check_method(attr_value):
                    setattr(self, attr_name, attr_value)
                else:
                    raise ValueError(f"The {attr_name} value is malformed")

        if metadata is not None:
            self.add_metadata(**metadata)

        # Update counters in metadata

        self.metadata[["count", "singular"]] = self.__count_singular__()
        self.metadata[["count", "plurals"]] = self.__count_plurals__()

        # End of __init__

    # Managing messages

    def get_id(self) -> str:
        """
        Get the unique identifier for the message.

        Returns:
            str: The message identifier.
        """
        return self.id

    def add_message(self, **kwargs) -> None:
        """
        Add translation-related attributes to the message.

        Args:
            **kwargs: Keyword arguments corresponding to message attributes to set.
                Supported keys: "translation" (str), "options" (dict[int, str]),
                "default_plurals" (dict[int, str]), "options_plurals" (dict[int, dict[int, str]]).

        Raises:
            ValueError: If "translation" is missing or empty, or if a provided attribute value is malformed.
        """
        __translation = kwargs.pop("default", None)

        if __translation is None:
            raise ValueError("At least one translation is required")
        else:
            self.default = __translation

            # Process attributes with a parameterized loop using validation methods
            for attr_name, check_method in [
                ("options", self.__check_alternatives__),
                ("default_plurals", self.__check_plural_forms__),
                ("options_plurals", self.__check_alternative_plural_forms__),
            ]:
                value = kwargs.pop(attr_name, None)
                if value is not None:
                    if check_method(value):
                        if attr_name == "options_plurals":
                            setattr(self, attr_name, StrictNestedDictionary(value))
                        else:
                            setattr(self, attr_name, value)
                    else:
                        raise ValueError(f"The {attr_name} value is malformed")

    def update_message(self, **kwargs) -> None:
        """
        Update translation-related attributes to the message.

        Args:
            **kwargs: Keyword arguments corresponding to message attributes to set.
                Supported keys: "translation" (str), "options" (dict[int, str]),
                "default_plurals" (dict[int, str]), "options_plurals" (dict[int, dict[int, str]]).

        Raises:
            ValueError: If "translation" is missing or empty, or if a provided attribute value is malformed.
        """

        translation = kwargs.pop("default", None)
        if translation is not None and translation != "":
            self.default = translation

        for attr_name, check_method in [
            ("options", self.__check_alternatives__),
            ("default_plurals", self.__check_plural_forms__),
            ("options_plurals", self.__check_alternative_plural_forms__),
        ]:
            value = kwargs.pop(attr_name, None)
            if value is not None:
                if check_method(value):
                    if attr_name == "options_plurals":
                        value = StrictNestedDictionary(value)
                    setattr(self, attr_name, value)
                else:
                    raise ValueError(f"The '{attr_name}' value is malformed")

    def remove_message(self) -> None:
        """
        Removes all translations in Message instance and setup to default emtpy values including metadata.
        :return:
        """
        self.id = ""
        self.default = ""
        self.options = {}
        self.default_plurals = {}
        self.options_plurals = StrictNestedDictionary()
        self.context = ""
        self.metadata = _build_empty_metadata()

    @property
    def message(self) -> list[list[str]]:
        """
        The list of translations in Message instance.

        :return: The list of translations in Message instance.
        :rtype: list[list[str]]
        """
        msg = [self.principal]
        msg.extend(self.variants)
        return msg

    @message.setter
    def message(self, value: list[list[str]]) -> None:
        """
        Set the translations in Message instance.

        :param value: the list of translations in Message instance.
        :return: nothing (void function)
        :rtype: None
        """
        self.principal = value[0]
        self.variants = value[1:]

    # Managing main

    def get_principal(self) -> list[str]:
        """
        Get the main translation and its plural forms.

        Returns:
            list[str]: A formatted list containing the main translation and all plural forms.
        """
        translations = [self.default]
        if self.default_plurals:
            translations.extend(self.default_plurals.values())
        return translations

    def get_principal_plurals(self) -> list[str]:
        """
        Get the main translation's plural forms.

        Returns:
            list[str]: The list of plural forms.
        """
        plurals = []
        if self.default_plurals:
            plurals.extend(self.default_plurals.values())
        return plurals

    def add_principal(self, *args, **kwargs) -> None:
        """
        Add the main translation or its plural forms and update the metadata counters..
        :param args: is a list of translation components
        :type args: list
        :param kwargs: if no args, is a dictionary of translation components
        :type kwargs: dict
        :return: Nothing (void function)
        :rtype: None
        """
        if args and len(args) == 1 and isinstance(args[0], list):
            translation = args[0]
            if translation[0] != "":
                self.default = translation[0]
                self.metadata[["count", "singular"]] = self.__count_singular__()
            else:
                raise ValueError(
                    f"Singular of translation is required and cannot be None or empty : '{translation[0]}'"
                )
            if len(translation) > 1:
                for index, token in enumerate(translation[1:]):
                    self.default_plurals[index + 1] = token
            self.metadata[["count", "plurals"]] = self.__count_plurals__()
        elif kwargs:
            alt_singular = kwargs.pop("default", None)
            if alt_singular is not None and alt_singular != "":
                self.default = alt_singular
                self.metadata[["count", "singular"]] = self.__count_singular__()
            else:
                raise ValueError(
                    f"Singular of translation is required and cannot be None or empty : '{alt_singular}'"
                )
            plural = kwargs.pop("default_plurals", None)
            if plural is not None:
                if isinstance(plural, dict) and self.__check_plural_forms__(plural):
                    self.default_plurals = plural
                else:
                    raise (ValueError(f"Plural forms is malformed : {plural}"))
            self.metadata[["count", "plurals"]] = self.__count_plurals__()
        else:
            raise (ValueError("No translation specified"))

    def update_principal(self, *args, **kwargs) -> None:
        """
        Update segments of a translation
        :param args: list of translation component
        :param kwargs: dictionary of translation components
        :return: nothing (void function)
        """
        if args and len(args) == 1 and isinstance(args[0], list):
            translation = args[0]
            if translation[0] is not None and translation[0] != "":
                self.default = translation[0]

            if len(translation) > 1:
                for index, text in enumerate(translation[1:]):
                    if text is not None and text != "":
                        self.default_plurals[index + 1] = text
        elif kwargs:
            pop_text = kwargs.pop("default", None)
            if pop_text is not None and pop_text != "":
                self.default = pop_text

            pop_plurals = kwargs.pop("default_plurals", None)
            if pop_plurals is not None:
                if isinstance(pop_plurals, dict) and self.__check_plural_forms__(
                    pop_plurals
                ):
                    self.default_plurals = pop_plurals
                elif isinstance(pop_plurals, list):
                    d_pop_plural = {}
                    for index, text in enumerate(pop_plurals):
                        d_pop_plural[index + 1] = text
                    self.default_plurals = d_pop_plural
                else:
                    raise (
                        ValueError(
                            f"plural translation context is malformed : {pop_plurals}"
                        )
                    )
        else:
            raise (ValueError("No updates specified"))

    def remove_principal(self) -> None:
        """
        Removes the main translation from message and update metadata
        :return: nothing (void function)
        :rtype: None
        """
        self.default = ""
        self.default_plurals = {}
        self.metadata[["count", "singular"]] = self.__count_singular__()
        self.metadata[["count", "plurals"]] = self.__count_plurals__()

    def _remove_default_segment(self):
        """
        Protected function to empties self.default.

        :return: nothing (void function)
        :rtype: None
        """
        self.default = ""
        self.metadata[["count", "singular"]] = self.__count_singular__()

    def _remove_default_plurals_segment(self, index: int) -> None:
        """
        Protected function to empties self.default_plurals.
        :param index: the location index (token) of the plural to be removed
        :type index: int
        :return: nothing (void function)
        :rtype: None
        :raises IndexError: if the token is out of range
        """
        if 0 < index <= len(self.default_plurals):
            del self.default_plurals[index]

            reshaped_dict: dict[int, str] = {}
            for idx, key in enumerate(sorted(self.default_plurals.keys()), start=1):
                reshaped_dict[idx] = self.default_plurals[key]
            self.default_plurals = reshaped_dict

            self.metadata[["count", "plurals"]] = self.__count_plurals__()
        else:
            raise IndexError(
                f"The location ({index}) of the plural to be remove is out of range"
            )

    @property
    def principal(self) -> list[str]:
        """
        The components of the main or default translation (principal) as a list of sentences.

        :return: a list of sentences
        :rtype: list[str]
        """
        return self.get_principal()

    @principal.setter
    def principal(self, value: list[str]) -> None:
        """
        Adds the principal of the translation.

        :param value: a list of sentences constitutive of the default translation
        :type value: list[str]
        :return: nothing (void function)
        :rtype: None
        """
        self.add_principal(value)

    # Managing variant

    def get_variant(self, option: int) -> list[str]:
        """
        Get the alternative translation and its plural forms for a specific location index.

        Args:
            option (int): The location index of the alternative translation.

        Returns:
            list[str]: A list containing the alternative translation and all its plural forms.

        Raises:
            IndexError: If the specified location index doesn't exist.
        """
        alternatives = []
        try:
            # Add the main alternative translation
            alternatives.append(self.options[option])

            # Add plural forms if they exist
            if option in self.options_plurals:
                alternatives.extend(self.options_plurals[option].values())

            return alternatives
        except KeyError:
            raise IndexError(f"Alternative translation at index {option} not found")

    def get_variant_plurals(self, option: int = 0) -> list[str]:
        """
        Get the alternative translation's plural forms.
        :param option: Option number of the alternative translation.
        :return: the list of plural forms.
        :rtype: list[str]
        """
        if option > len(self.options_plurals) or option <= 0:
            raise IndexError(
                f"Alternative translation at index {option} is out of range"
            )

        return list(self.options_plurals[option].values())

    def add_variant(self, *args, **kwargs) -> None:
        """
        Add an optional (alternative) translation and its plural forms and update the metadata counters.

        :param args:
        :param kwargs:
        :return:
        """
        option = self.metadata[["count", "singular"]] + 1

        if option == 1:
            raise ValueError(
                "Cannot add an alternative translation, there presently is no translation"
            )

        # Settings option index correctly and extracting
        option -= 1

        if args and len(args) == 1 and isinstance(args[0], list):
            # Managing alternate translation in args
            translation = args[0]
            if translation[0] is not None and translation[0] != "":
                self.options[option] = translation[0]
                self.metadata[["count", "singular"]] = self.__count_singular__()
            else:
                raise ValueError(
                    f"Singular of a variant is required and cannot be None or empty : '{translation[0]}'"
                )
            # Managing alternate plurals in args
            if len(translation) > 1:
                for index, text in enumerate(translation[1:]):
                    self.options_plurals[[option, index + 1]] = text
            else:
                self.options_plurals.update({option: {}})

            self.metadata[["count", "plurals"]] = self.__count_plurals__()
        elif kwargs:
            # Managing alternate translation in kwargs (obliviate if args is not None)
            alt_singular = kwargs.pop("options", None)
            if alt_singular is not None and alt_singular != "":
                self.options[option] = alt_singular
                self.metadata[["count", "singular"]] = self.__count_singular__()
            else:
                raise ValueError(
                    f"Singular of a variant is required and cannot be None or empty : '{alt_singular}'"
                )
            # Managing alternate plurals
            alt_plural = kwargs.pop("options_plurals", None)
            if alt_plural is not None:
                if isinstance(alt_plural, dict) and _check_index_dict(alt_plural):
                    self.options_plurals.update({option: alt_plural})
                elif isinstance(alt_plural, list):
                    d_alt_plural = {}
                    for index, text in enumerate(alt_plural):
                        d_alt_plural[index + 1] = text
                    self.options_plurals.update({option: d_alt_plural})
                else:
                    raise (
                        ValueError(
                            f"Plural of this variant is malformed : {alt_plural}"
                        )
                    )
            else:
                self.options_plurals.update({option: {}})
            self.metadata[["count", "plurals"]] = self.__count_plurals__()
        else:
            raise (ValueError("No variant translation is specified"))

    def update_variant(self, option: int = 0, *args, **kwargs) -> None:
        """
        Update alternative translation
        :param option: index of alternative translation
        :type option: int
        :param args: list of alternative translation components
        :type args: list
        :param kwargs: dictionary of alternative translation components
        :type kwargs: dictionary
        :return: nothing (void function)
        """
        if option == 0:
            self.update_principal(*args, **kwargs)
        elif option > len(self.options) or option <= 0:
            raise (IndexError(f"Option '{option}' out of range"))
        elif args and len(args) == 1 and isinstance(args[0], list):
            translation = args[0]
            if translation[0] is not None and translation[0] != "":
                self.options[option] = translation[0]

            if len(translation) > 1:
                for index, text in enumerate(translation[1:]):
                    if text is not None and text != "":
                        self.options_plurals[[option, index + 1]] = text
        elif kwargs:
            pop_text = kwargs.pop("options", None)
            if pop_text is not None and pop_text != "":
                self.options[option] = pop_text

            pop_plurals = kwargs.pop("options_plurals", None)
            if pop_plurals is not None:
                if isinstance(pop_plurals, dict) and _check_index_dict(pop_plurals):
                    self.options_plurals.update({option: pop_plurals})
                elif isinstance(pop_plurals, list):
                    d_pop_plural = {}
                    for index, text in enumerate(pop_plurals):
                        d_pop_plural[index + 1] = text
                    self.options_plurals.update({option: d_pop_plural})
                else:
                    raise (
                        ValueError(
                            f"Plural translation context is malformed : {pop_plurals}"
                        )
                    )
        else:
            raise (ValueError("No updates specified"))

    # managing segments in translations

    def get_main_segment(self, index: int = 0) -> str:
        """
        Private function to get token in the main translation
        :param index: segment's location in the main translation
        :type index: int
        :return: the corresponding segment located at the token location
        :rtype: str
        """
        __translation = self.get_principal()
        if len(__translation) > index >= 0:
            return __translation[index]
        else:
            raise (IndexError(f"Segment location '{index}' is out of range"))

    def get_variant_segment(self, option: int = 1, index: int = 0) -> str:
        """
        Private function to get token in the variant translation
        :param option: segment's option in the variant translation
        :type option: int
        :param index: segment's location in the variant option
        :type index: int
        :return: the corresponding segment located at the token location of the variant option
        """
        try:
            __translation = self.get_variant(option)

            if len(__translation) > index >= 0:
                return __translation[index]
            else:
                raise (
                    IndexError(
                        f"Segment location '{index}' of variant option '{option}' is out of range"
                    )
                )
        except IndexError as e:
            raise (e)

    def get_segment(self, **kwargs) -> str:
        """
        Get the message string from the message.

        Args:
            kwargs (dict): contains mandatory keys to access each kind of segment in main and variant translation.
                these keys are such as target (default, variant, plurals) and positions (option and token)
        Returns:
            str: The content of the message.

        Raises:
            KeyError: If a mandatory key is missing
            IndexError: If a mandatory key is out of range
        """

        # parameter processing
        source = kwargs.pop("source", None)
        token = kwargs.pop("token", 0)
        option = kwargs.pop("option", 1)

        if source not in ["main", "variant"]:
            raise KeyError(
                f"The source '{source}' is not defined : ['main', 'variant']"
            )

        if source == "main":
            return self.get_main_segment(token)
        else:
            return self.get_variant_segment(option=option, index=token)

    def add_main_segment(self, segment: str, index: int = 0) -> None:
        """
        Add a plural form to the message. This function is securing text adding by not allowing emptied texts. If you
        need to add en empty string use the _add_default_segement method.

        Args:
            index (int): location of segment in the main translation, if token = 0 change self.default is is None
            segment (str): The text for the plural form.

        Raises:
            ValueError: If the index is less than or equal to 0.
        """
        if index == 0:
            if segment != "":
                self.default = segment
            else:
                raise ValueError(
                    f"Singular of translation is required and cannot be None or empty : '{segment}'"
                )
        elif 0 < index <= len(self.default_plurals) + 1:
            self.default_plurals[index] = segment
        else:
            raise ValueError(f"Plural form index ({index}) is not in a valid range")

    def _add_default_segment(self, segment: str) -> None:
        """
        Protected method to add a default text to the message. This function is simply present for homogeneity since
        self.default = segment will work.

        :param segment: the text to add
        :return: nothing (void function)
        """
        self.default = segment

    def _add_default_plurals_segment(self, segment: str) -> None:
        """
        Protected method to add an item in the default plural form to the message.
        :param segment:
        :return:
        """

        self.default_plurals[len(self.default_plurals) + 1] = segment

    def add_variant_segment(
        self, segment: str, option: int = 1, token: int = 0
    ) -> None:
        """
        Add an alternative translation to the message.

        Args:
            token (int): The index of the alternative translation.
            segment (str): The alternative translation text.
            option (int): The option of the alternative translation.

        Raises:
            ValueError: If the index is less than or equal to 0.
        """
        if 0 < option <= len(self.options) + 1:
            if token == 0:
                self.options[option] = segment
            elif 0 < token <= len(self.options_plurals) + 1:
                self.options_plurals[[option, token]] = segment
            else:
                raise IndexError(
                    f"Segment index ({token}) in options ({option}) is not in a valid range"
                )
        else:
            raise IndexError(f"Option index ({option}) is not in a valid range")

    def _add_options_segment(self, segment: str) -> None:
        """
        Protected function to add an alternative translation corresponding of the next option index of the message .

        :param segment: The alternative translation text.
        :return:
        """

        self.options[len(self.options) + 1] = segment

    def _add_options_plurals_segment(self, segment: str, option: int) -> None:
        """
        Add a plural form to an alternative translation.

        Args:
            segment (str): The alternative translation text.
            option (int): The index of the alternative translation.
        Raises:
            ValueError: If alt_index or plural_index is less than or equal to 0.
            KeyError: If the alternative translation at alt_index doesn't exist.
        """

        if 0 < option <= len(self.options) + 1:
            if option == len(self.options) + 1:
                # Adding a new range of option, token is 1
                __token = 1
            else:
                # Adding a new segment in an existing option
                if self.options_plurals.get(option) is None:
                    # Plurals does not exist
                    __token = 1
                else:
                    __token = len(self.options_plurals[option]) + 1
            self.options_plurals[[option, __token]] = segment
        else:
            raise IndexError(f"Option index ({option}) is not in a valid range")

    def update_main_segment(self, segment: str, index: int = 0) -> None:
        """
        Update an existing element (singular or one of the plurals) of the main translation of the message.

        :param segment: the text to add
        :type segment: str
        :param index: the location in the main translation list of the element to be updated.
        :type index: int
        :return: nothing (void method)
        :raises IndexError: If token is out of range.
        :raises ValueError: If the segment is already stored in message at the requested locations or if it is emtpy.
        """
        if segment != "":
            if 0 == index:
                if self.default != segment:
                    self.default = segment
                else:
                    raise ValueError(
                        f"The text value ('{segment}') is already stored as default singular translation : '{self.default}'"
                    )
            else:
                self._assert_valid_default_plural_token(index)
                if self.default_plurals.get(index) != segment:
                    self.default_plurals[index] = segment
                else:
                    raise ValueError(
                        f"The text value ('{segment}') is already stored as default plural index ({index}) : '{self.default_plurals[index]}'"
                    )
        else:
            raise ValueError("Empty text cannot be added")

    def _update_default_segment(self, segment: str) -> None:
        """
        Protected method to update the default singular translation of the message. This function is simply present
        for homogeneity since self.default = segment will work.

        :param segment: the text to update
        :return: nothing (void method)
        """
        self.default = segment

    def _update_default_plurals_segment(self, segment: str, index: int) -> None:
        """
        Protected method to update the default plural translation of the message.

        :param segment: the text to update
        :param index: the location in the main translation list of the element to be updated.
        :return: nothing (void method)
        :raise IndexError: If token is out of range.
        """
        self._assert_valid_default_plural_token(index)
        self.default_plurals[index] = segment

    def update_variant_segment(
        self, segment: str, option: int = 1, index: int = 0
    ) -> None:
        """
        Update an existing element (singular or one of the plurals) of (option) the variant translation of the message.
        :param segment: the text to update
        :param option: the index of the variant translation to update.
        :param index: the index of the element to be updated in the variant translation.
        :return: nothing (void method)
        :raises IndexError: If option or token is out of range.
        :raises ValueError: If the segment is already stored in message at the requested locations or if it is emtpy.
        """
        if segment != "":
            self._assert_valid_option(option)
            if index == 0:
                self.options[option] = segment
            else:
                self._assert_valid_token_in_option(option, index)
                self.options_plurals[[option, index]] = segment
        else:
            raise ValueError("Empty text cannot be added")

    def _update_options_segment(self, segment: str, option: int) -> None:
        """
        Protected method to update one of the (option) variant translation singular of the message.
        :param segment:
        :param option:
        :return: nothing (void method)
        :raises IndexError: If option is out of range.
        """
        self._assert_valid_option(option)
        self.options[option] = segment

    def _update_options_plurals_segment(
        self, segment: str, option: int, index: int
    ) -> None:
        """
        Protected function to update one of the (option) variant plural (token) translation singular of the message.
        :param segment: the text to update
        :param option: the variant index
        :param index: the index of the element to be updated in the variant plural.
        :return: nothing (void method)
        :raises IndexError: If option or toaken is out of range.
        """
        self._assert_valid_option(option)
        self._assert_valid_token_in_option(option, index)
        self.options_plurals[[option, index]] = segment

    def remove_variant(self, option: int) -> None:
        """
        Removes the option variant of translation and keeps indices coherent.

        This method ensures that after removal, both self.options and
        self.options_plurals have contiguous indices starting from 1 so that
        validation checks (__check_alternatives__ and __check_alternative_plural_forms__)
        remain true. For example, if option 2 is removed and there were 4 options,
        then former option 3 becomes 2 and former option 4 becomes 3.

        :param option: the index of the variant translation to remove.
        :type option: int
        :return: nothing (void method)
        :rtype: None
        :raises IndexError: If option is out of range.
        """
        # Validate option exists
        self._assert_valid_option(option)
        previous_length = len(self.options)

        # 1) Remove the selected option and its plurals if present
        del self.options[option]
        if option in self.options_plurals.keys():
            del self.options_plurals[option]

        # 2) Reindex self.options to keep keys contiguous starting from 1
        if option < previous_length:
            # Preserve insertion order by iterating values in key order
            reshaped_dict: dict[int, str] = {}
            for idx, key in enumerate(sorted(self.options.keys()), start=1):
                reshaped_dict[idx] = self.options[key]
            self.options = reshaped_dict

            old_plurals = self.options_plurals
            new_plurals = StrictNestedDictionary()
            for key in sorted(old_plurals.keys()):
                # Shift down indices greater than removed option
                new_key = key if key < option else key - 1
                # Ensure we skip any potential non-positive key (defensive)
                if new_key > 0:
                    # Copy the inner dict as is (inner indices remain coherent)
                    inner = (
                        dict(old_plurals[key])
                        if isinstance(old_plurals[key], dict)
                        else old_plurals[key]
                    )
                    new_plurals.update({new_key: inner})
            self.options_plurals = new_plurals

        # 4) Refresh metadata counters
        self._refresh_counts()

    def _remove_options_segment(self, option: int) -> None:
        """
        Protected method to remove the option variant translation of the message.
        :param option: the index of the variant translation to remove.
        :type option: int
        :return: nothing (void method)
        :rtype: None
        :raises IndexError: If option is out of range.
        """
        self._assert_valid_option(option)
        previous_length = len(self.options)
        del self.options[option]

        if option < previous_length:
            # Preserve insertion order by iterating values in key order
            reshaped_dict: dict[int, str] = {}
            for idx, key in enumerate(sorted(self.options.keys()), start=1):
                reshaped_dict[idx] = self.options[key]
            self.options = reshaped_dict

        self._refresh_counts(singular=True)

    def _remove_options_plurals_segment(
        self, option: int, index: int | None = None
    ) -> None:
        """
        Protected method to remove one of the plural (token) of one of the variant (option) translation of the message.
        :param option: the index of the variant translation to be reached.
        :param index: the index of the plural translation to be removed.
        :return: nothing (void method)
        :rtype: None
        :raises IndexError: If option or token is out of range.
        """
        self._assert_valid_option(option)
        if index is None:
            self._remove_options_segment(option)
        elif self.options_plurals.paths().__contains__([option, index]):
            del self.options_plurals[[option, index]]
            reshaped_dict: dict[int, str] = {}
            for idx, key in enumerate(
                sorted(self.options_plurals[option].keys()), start=1
            ):
                reshaped_dict[idx] = self.options_plurals[[option, key]]
            self.options_plurals.update({option: reshaped_dict})
            self._refresh_counts(plurals=True)
        else:
            raise IndexError(f"The plural path [{option}, {index}] is out of range")

    @property
    def variants(self) -> list[list[str]]:
        """
        The list of variants in the repository.
        :return:
        """
        variants = []
        for index in range(1, len(self.options) + 1):
            variants.append(self.get_variant(index))
        return variants

    @variants.setter
    def variants(self, variants: list[list[str]]) -> None:
        """
        The list of variants in the repository.
        :param variants:
        :return:
        """
        for index, variant in enumerate(variants):
            self.update_variant(index + 1, variant)

    # Managing metadata

    def get_metadata(self, key: list[str] | str | None = None) -> dict[str, Any] | Any:
        """
        Get metadata from the message.

        Args:
            key (list[str] or str, optional): The specific metadata key to retrieve.
                If None, returns all metadata. Defaults to None.

        Returns:
            dict[str, Any] | Any: The requested metadata. If key is None, returns the entire
                metadata dictionary. If key is provided, returns the value for that key.

        Raises:
            KeyError: If the specified key doesn't exist in the metadata.
        """
        if key is None:
            return self.metadata

        if (isinstance(key, str) and key in self.metadata) or (
            isinstance(key, list) and key in self.metadata.paths()
        ):
            return self.metadata[key]

        raise KeyError(f"Metadata '{key}' is not a key or path")

    def add_location(self, line: int, file: str) -> None:
        """
        Add a source location where the message is used.

        Args:
            line (int): The line number in the file where the translation is used.
            file (str): The file path where the translation is used.
        """
        self.metadata["location"].append((file, line))

    def add_language(self, lang: str) -> None:
        """
        Set the language of the message.

        Args:
            lang (str): An IETF language tag.
        """
        self.metadata["language"] = normalize_language_tag(lang)

    def add_comment(self, mode: Literal["auto", "user"], comment: str) -> None:
        """
        Add an author's comment to the message.

        Args:
            mode (Literal["auto", "user"], optional): The mode of the comment. Defaults to "auto".
            comment (str): The author's comment to add.
        """
        if len(comment) == 0:
            raise ValueError("Unable to add empty comment")
        key = mode + "_comments"
        self.metadata[key].append(comment)

    def add_metadata(self, *args: tuple[list[str], Any], **kwargs) -> None:
        """
        Set metadata for the message.

        Args:
            args (tuple[list[str], Any]): The list of keys and value to pass to the metadata.
            kwargs (dict[str, Any]): The kwargs parameters to pass to the metadata.

        Raises:
            ValueError: If key_or_dict is malformed and value is None.
        """

        if not self.__check_metadata__(self.metadata):
            self.metadata = _build_empty_metadata()

        if args:
            for path, value in args:
                if (
                    isinstance(path, str) and self.metadata.paths().__contains__([path])
                ) or (
                    isinstance(path, list) and self.metadata.paths().__contains__(path)
                ):
                    self.metadata[path] = value
                else:
                    raise KeyError(
                        f"The path '{path}' is not a present key in the metadata dictionary"
                    )
        if kwargs:
            for key, value in kwargs.items():

                if isinstance(value, set):
                    raise TypeError(
                        f"{type(value)} type of {value} is not compatible metadata"
                    )

                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        path = [key, sub_key]
                        if not self.metadata.paths().__contains__(path):
                            raise KeyError(
                                f"The path '{path}' is not a present key in the metadata dictionary"
                            )
                        else:
                            self.metadata[path] = sub_value
                elif isinstance(key, str) and self.metadata.is_key(key):
                    self.metadata[key] = value
                else:
                    raise KeyError(
                        f"The key '{key}' is not a present key in the metadata dictionary"
                    )

    def update_metadata(self, *args: tuple[list[str], Any], **kwargs) -> None:
        """
        Update the message's metadata with new values.

        Args:
            args (Tuple[list[str], Any): is a list of (paths, value) pairs is a StrictNestedDictionary
            kwargs :
        """

        if args:
            for path, value in args:
                if (
                    isinstance(path, str) and self.metadata.paths().__contains__([path])
                ) or (
                    isinstance(path, list) and self.metadata.paths().__contains__(path)
                ):
                    if self.metadata[path] == value:
                        raise ValueError(
                            f"The value ({value}) is already stored in the path '{path}'"
                        )
                    else:
                        self.metadata[path] = value
                else:
                    raise KeyError(
                        f"The path '{path}' is not a present key in the metadata dictionary"
                    )
        if kwargs:
            for key, value in kwargs.items():
                if isinstance(value, set):
                    raise TypeError(
                        f"{type(value)} of {value} is not compatible metadata"
                    )

                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        path = [key, sub_key]
                        if not self.metadata.paths().__contains__(path):
                            raise KeyError(
                                f"The path '{path}' is not a present key in the metadata dictionary"
                            )
                        elif self.metadata[path] == sub_value:
                            raise ValueError(
                                f"The value ({sub_value}) is already stored in the path '{path}'"
                            )
                        else:
                            self.metadata[path] = sub_value
                elif isinstance(key, str) and self.metadata.is_key(key):
                    if self.metadata[key] == value:
                        raise ValueError(
                            f"The value ({value}) is already stored in the path '[{key}]'"
                        )
                    else:
                        self.metadata[key] = value
                else:
                    raise KeyError(
                        f"The key '{key}' is not a present key in the metadata dictionary"
                    )

    def remove_metadata(self, key: str | list[str] | None = None) -> None:
        """
        Delete metadata from the message.

        Args:
            key (str | None, optional): The specific metadata key to delete.
                If None, clears all metadata.

        Raises:
            KeyError: If the specified key doesn't exist in the metadata.
        """

        ref_meta = _build_empty_metadata()

        if key is None:
            self.metadata = ref_meta
        elif isinstance(key, list) and key not in self.metadata.paths():
            raise KeyError(
                f"path '{key}' is not a present key in the metadata dictionary"
            )
        elif isinstance(key, str) and key not in self.metadata.keys():
            raise KeyError(f"Metadata key '{key}' not found")
        else:
            self.metadata[key] = ref_meta[key]

    def switch(self, source: int, destination: int) -> None:
        """
        Switch the position of two translations (singular and their plural forms).

        - Index 0 refers to the default translation.
        - Positive indices (1..len(options)) refer to variant options.

        This swaps both the singular text and the associated plural forms between
        the two specified positions.

        :param source: Index of the source translation (0 for default).
        :param destination: Index of the destination translation (0 for default).
        :raises IndexError: If indices are equal or out of range.
        :return: None
        """
        # Disallow swapping the same index
        if source == destination:
            raise IndexError(
                f"source ({source}) and destination ({destination}) must be different"
            )

        # Validate indices
        if source != 0:
            self._assert_valid_option(source)
        if destination != 0:
            self._assert_valid_option(destination)

        # Helper to get singular and plurals for an index
        def get_pair(index: int) -> tuple[str, dict[int, str]]:
            if index == 0:
                return self.default, dict(self.default_plurals)
            # index > 0
            singular = self.options[index]
            plurals = (
                dict(self.options_plurals[index])
                if index in self.options_plurals.keys()
                else {}
            )
            return singular, plurals

        # Helper to set singular and plurals for an index
        def set_pair(index: int, singular: str, plurals: dict[int, str]) -> None:
            if index == 0:
                self.default = singular
                self.default_plurals = dict(plurals)
            else:
                self.options[index] = singular
                # Ensure we set the plural mapping (even if empty) for coherence
                self.options_plurals.update({index: dict(plurals)})

        # Fetch pairs
        src_s, src_p = get_pair(source)
        dst_s, dst_p = get_pair(destination)

        # Swap them
        set_pair(source, dst_s, dst_p)
        set_pair(destination, src_s, src_p)

        # Refresh counts metadata (singular count unchanged, plural list ordering may change)
        self._refresh_counts()

    def toggle(self, direction: str = "natural") -> None:
        """
        Rotate all translations (default and variants) together with their plural forms.

        - "natural": 0 -> 1, 1 -> 2, ..., n -> 0
        - "reverse": 0 -> n, 1 -> 0, 2 -> 1, ...

        Index 0 refers to the default translation; indices 1..n are the variant options.
        The rotation preserves option ordering integrity (contiguous indices starting at 1)
        and moves corresponding plural forms along with each singular.

        :param direction: Either "natural" (default) or "reverse".
        :raises ValueError: If direction is invalid.
        :return: None
        """
        if direction not in {"natural", "reverse"}:
            raise ValueError("direction must be either 'natural' or 'reverse'")

        n = len(self.options)
        # Nothing to rotate if no variants exist
        if n == 0:
            return

        # Helper to fetch a pair (singular, plurals) for index
        def get_pair(index: int) -> tuple[str, dict[int, str]]:
            if index == 0:
                return self.default, dict(self.default_plurals)
            singular = self.options[index]
            plurals = (
                dict(self.options_plurals[index])
                if index in self.options_plurals.keys()
                else {}
            )
            return singular, plurals

        # Build the current ordered list of (singular, plurals)
        pairs: list[tuple[str, dict[int, str]]] = [get_pair(0)] + [
            get_pair(i) for i in range(1, n + 1)
        ]

        # Apply rotation
        if direction == "reverse":
            rotated = pairs[1:] + pairs[:1]
        else:  # reverse
            rotated = [pairs[-1]] + pairs[:-1]

        # Assign back: new default and options
        new_default_s, new_default_p = rotated[0]
        self.default = new_default_s
        self.default_plurals = dict(new_default_p)

        new_options: dict[int, str] = {}
        new_plurals = StrictNestedDictionary()
        for idx in range(1, n + 1):
            s, p = rotated[idx]
            new_options[idx] = s
            # Ensure each option has a mapping (possibly empty) for coherence
            new_plurals.update({idx: dict(p)})

        self.options = new_options
        self.options_plurals = new_plurals

        # Refresh metadata counts (structure unchanged, indices may carry different texts)
        self._refresh_counts()

    def format(self, option: int = 0, token: int = 0, **kwargs: object) -> str:
        """
        Format the message with the provided variables.

        Args:
            option (int, optional): The alternative index to use. Defaults to 0.
            token (int, optional): The plural form index to use. Defaults to 0.
            **kwargs: Variables to use for formatting.

        Returns:
            str: The formatted message.
        """
        # Determine which text to format based on alternative and plural_index
        if option > 0 and option in self.options:
            if (
                token > 0
                and option in self.options_plurals
                and token in self.options_plurals[option]
            ):
                text = self.options_plurals[option][token]
            else:
                text = self.options[option]
        elif token > 0 and token in self.default_plurals:
            text = self.default_plurals[token]
        else:
            text = self.default

        # Format the text using the provided variables
        try:
            return text.format(**kwargs)
        except KeyError as e:
            missing_var = str(e).strip("'")
            raise KeyError(f"Missing variable '{missing_var}' for message '{self.id}'")
        except Exception as e:
            raise ValueError(f"Error formatting message '{self.id}': {str(e)}")

    def get_format_variables(self, option: int = 0) -> list[list[str]]:
        """
        This function returns the list of named variables in singular and plurals text to format. By default if option is
        equal to zero the default translation will be explored.

        :param option: the  index of option text to explore
        :type option: int
        :return: a tuple of list of variables
        :rtype: list[list[str]]
        :raises IndexError: If option is out of range.
        :raises ValueError: If no variables extracted is out of range.
        """

        if option != 0:
            self._assert_valid_option(option)
            translations = self.get_variant(option)
        else:
            translations = self.get_principal()

        extraction = []
        for t in translations:
            extraction.append(extract_variables(t))

        return extraction

    @property
    def has_variants(self) -> bool:
        """
        Indique s'il existe des variantes (options) pour cette traduction.
        Retourne True si au moins une variante (options) ou des pluriels de variantes (options_plurals) existent.
        """
        try:
            return (isinstance(self.options, dict) and len(self.options) > 0) or (
                isinstance(self.options_plurals, (dict, StrictNestedDictionary))
                and len(self.options_plurals) > 0
            )
        except Exception:
            return False

    @property
    def has_plurals(self) -> bool:
        """
        Indique s'il existe des formes plurielles pour cette traduction.
        Retourne True si des pluriels par défaut (default_plurals) existent ou si
        au moins une variante possède des pluriels (options_plurals).
        """
        try:
            default_has = (
                isinstance(self.default_plurals, dict) and len(self.default_plurals) > 0
            )
            variant_has = (
                isinstance(self.options_plurals, (dict, StrictNestedDictionary))
                and len(self.options_plurals) > 0
            )
            return default_has or variant_has
        except Exception:
            return False

    def to_i18n_tools_format(self) -> dict[str, Any]:
        """
        Convert the Message to i18n_tools format.

        Returns:
            dict[str, Any]: The message in i18n_tools format.
        """
        return message_to_i18n_tools_format(self)

    @classmethod
    def from_i18n_tools(
        cls, message_id: str, i18n_tools_entry: dict[str, Any]
    ) -> "Message":
        """
        Create a Message instance from an i18n_tools format entry.

        Args:
            message_id (str): The message ID.
            i18n_tools_entry (dict[str, Any]): The i18n_tools format entry.

        Returns:
            Message: A new Message instance.
        """
        # Convert i18n_tools format to unified format
        entry = i18n_tools_format_to_message_dict(i18n_tools_entry)

        return cls(
            id=message_id,
            default=entry.get("default", ""),
            default_plurals=entry.get("default_plurals", None),
            options=entry.get("options", None),
            options_plurals=entry.get("options_plurals", None),
            context=entry.get("context", ""),
            metadata=entry.get("metadata"),
        )

    @override
    def __str__(self) -> str:
        """
        Return the string representation of the message.

        Returns:
            str: The message translation.
        """
        return self.default

    @override
    def __repr__(self) -> str:
        """
        Return the representation of the message.

        Returns:
            str: The message representation.
        """
        return f"Message(id='{self.id}', translation='{self.default}')"

    # Equality based on exact properties
    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Message):
            return NotImplemented

        # Normalize potentially nested dictionaries for comparison
        def to_plain(d: object) -> object:
            if isinstance(d, StrictNestedDictionary):
                return d.to_dict() if hasattr(d, "to_dict") else dict(d)
            return d

        return (
            self.id == other.id
            and self.default == other.default
            and self.context == other.context
            and to_plain(self.options) == to_plain(other.options)
            and to_plain(self.default_plurals) == to_plain(other.default_plurals)
            and to_plain(self.options_plurals) == to_plain(other.options_plurals)
            and to_plain(self.metadata) == to_plain(other.metadata)
        )

    def equals(self, other: object) -> bool:
        """
        Vérifie si deux messages sont égaux en comparant exactement toutes leurs propriétés.
        Retourne True si et seulement si toutes les propriétés sont identiques.
        """
        try:
            return bool(self == other)
        except Exception:
            return False

    @property
    def translations_set(self) -> set[Any]:
        """
        Construit un ensemble de toutes les chaînes de traduction présentes dans ce message,
        en agrégeant le texte principal, ses pluriels, ainsi que toutes les variantes et leurs pluriels.
        L'objectif est de permettre une comparaison d'équivalence indépendante du rangement en
        « main » (default/default_plurals) ou « variant » (options/options_plurals).
        """
        texts = set()
        # Default
        if isinstance(self.default, str) and self.default:
            texts.add(self.default)
        # Default plurals
        dp = self.default_plurals
        if isinstance(dp, StrictNestedDictionary):
            dp = dp.to_dict()
        if isinstance(dp, dict):
            for v in dp.values():
                if isinstance(v, str) and v:
                    texts.add(v)
        # Options (variants)
        opts = self.options
        if isinstance(opts, StrictNestedDictionary):
            opts = opts.to_dict()
        if isinstance(opts, dict):
            for v in opts.values():
                if isinstance(v, str) and v:
                    texts.add(v)
        # Options plurals
        op = self.options_plurals
        if isinstance(op, StrictNestedDictionary):
            op = op.to_dict()
        if isinstance(op, dict):
            for inner in op.values():
                if isinstance(inner, StrictNestedDictionary):
                    inner = inner.to_dict()
                if isinstance(inner, dict):
                    for v in inner.values():
                        if isinstance(v, str) and v:
                            texts.add(v)
        return texts

    def is_similar(self, other: object) -> bool:
        """
        Deux messages sont « semblables » s'ils possèdent le même ensemble de traductions,
        indépendamment de l'endroit où elles sont rangées (principal vs variantes).
        Cette comparaison ignore id, context, metadata et l'organisation entre default/options.
        """
        if not isinstance(other, Message):
            return False
        try:
            return self.translations_set == other.translations_set
        except Exception:
            return False

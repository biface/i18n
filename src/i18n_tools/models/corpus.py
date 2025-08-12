"""
Corpus module
=============


"""

import re
from gettext import translation
from typing import Any, Dict, List, Optional, Union

from ndict_tools import StrictNestedDictionary

from i18n_tools import __version__
from i18n_tools.converter import (
    i18n_tools_format_to_message_dict,
    i18n_tools_to_unified_format,
    message_to_i18n_tools_format,
    unified_format_to_i18n_tools,
)
from i18n_tools.locale import normalize_language_tag


def _check_index_dict(dictionary: Dict[int, str]) -> bool:
    """
    Validate that dictionary keys are within the range [1, len(dictionary)].

    Args:
        dictionary (Dict[int, str]): The dictionary to validate.

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
            "version": __version__,
            "language": "",
            "location": [],
            "flags": ["python-format"],
            "comments": "",
            "count": {
                "singular": 0,
                "plurals": [],
            },
        },
        default_setup={"indent": 2},
    )


def extract_variables(text: str) -> List[str]:
    """
    Extract variable names from a formatted string.

    Args:
        text (str): The formatted string.

    Returns:
        List[str]: List of variable names.
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
        options (Dict[int, str]): A collection of alternative translations that can be used in different contexts or scenarios, allowing for flexibility in message presentation based on specific needs.
        default_plurals (Dict[int, str]): A set of translations that account for different pluralization rules, accommodating languages with multiple plural forms.
        options_plurals (Dict[int, Dict[int, str]]): Plural forms associated with alternative translations, providing comprehensive support for various linguistic pluralization requirements.
        context (str): Additional information that clarifies the usage context of the message, helping to disambiguate messages with similar or identical text. It is maintained for compatibility with other format.
        metadata (StrictNestedDictionary): The metadata attribute of the Message class contains detailed information about the translation, aiding in its management and usage. The structure of the metadata is as follows:

            - version (str): Indicates the version of the metadata structure, allowing for future changes in format while maintaining backward compatibility.
            - language (str): Is the IETF Language Tag code used in the message. It is built with language code library.
            - location (List[Tuple[int, str]]): A list of source file locations where the message is used, including the file path and line number. This helps in tracking the usage of the message within the codebase.
            - flags (List[str]): A set of indicators that provide additional information about the message, such as whether it is fuzzy or uses a specific format like Python-format.
            - comments (str): Notes or comments from translators, offering insights or additional context about the message.
            - count (Dict[str, Any]): Counting translation of standard and alternatives.

                - singular (int): The number of times the singular form of the message is used, helping in understanding the frequency and importance of the message.
                - plurals (List[int]): A list of counts for the different plural forms of the message, providing information on the usage of each plural form.
    """

    def __check_plural_forms__(self, value: Optional[Dict[int, str]] = None) -> bool:
        """
        Check if the plural_forms attribute or the provided value has the correct data structure.

        Args:
            value (Optional[Dict[int, str]], optional): The value to check. If None, checks self.plural_forms. Defaults to None.

        Returns:
            bool: True if the structure is valid, False otherwise.
        """
        # Determine which value to check
        data_to_check = value if value is not None else self.default_plurals

        return _check_index_dict(data_to_check)

    def __check_alternatives__(self, value: Optional[Dict[int, str]] = None) -> bool:
        """
        Check if the alternatives attribute or the provided value has the correct data structure.

        Args:
            value (Optional[Dict[int, str]], optional): The value to check. If None, checks self.alternatives. Defaults to None.

        Returns:
            bool: True if the structure is valid, False otherwise.
        """
        # Determine which value to check
        data_to_check = value if value is not None else self.options

        # Check that all keys are integers and all values are strings
        return _check_index_dict(data_to_check)

    def __check_alternative_plural_forms__(
        self, value: Optional[Dict[int, Dict[int, str]]] = None
    ) -> bool:
        """
        Check if the alternative_plural_forms attribute or the provided value has the correct data structure.

        Args:
            value (Optional[Dict[int, Dict[int, str]]], optional): The value to check. If None, checks self.alternative_plural_forms. Defaults to None.

        Returns:
            bool: True if the structure is valid, False otherwise.
        """

        # Determine which value to check
        data_to_check = value if value is not None else self.options_plurals
        __check = _check_index_dict(data_to_check)

        # Check that all keys are integers and all values are dictionaries
        if __check:
            for key, val in data_to_check.items():
                __check = _check_index_dict(val)

        return __check

    def __check_metadata__(self, value: Dict[str, Any]) -> bool:
        """
        Check if the metadata attribute or the provided value has the correct data structure.

        Args:
            value (Optional[Dict[str, Any]], optional): The value to check. If None, checks self.metadata. Defaults to None.

        Returns:
            bool: True if the structure is valid, False otherwise.
        """
        __check = True

        if isinstance(value, StrictNestedDictionary):
            paths = value.dict_paths()
        else:
            paths = StrictNestedDictionary(value).dict_paths()

        for path in paths:
            if not path in self.metadata.dict_paths():
                __check = False

        return __check

    def __count_singular__(self) -> int:
        """
        Get the count of singulars in translation and alternatives.

        Returns:
            int: The count of presently stored singulars.
        """
        count = 0
        if len(self.default) > 0:
            count += 1 + len(self.options)

        return count

    def __count_plurals__(self) -> List[int]:
        """
        Get the list of plurals for each singular or alternative singular.

        Returns:
            List[int]: The list of count of plurals for each singular.
        """
        counts = [len(self.default_plurals)]
        for index in range(1, len(self.options) + 1):
            if index in self.options_plurals.keys():
                counts.append(len(self.options_plurals[index]))
            else:
                counts.append(0)

        return counts

    def __init__(
        self,
        id: str,
        default: str = "",
        options: Optional[Dict[int, str]] = None,
        default_plurals: Optional[Dict[int, str]] = None,
        options_plurals: Optional[Dict[int, Dict[int, str]]] = None,
        context: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize a new Message instance.

        Args:
            id (str): The unique identifier for the message.
            default (str, optional): The main translation text. Defaults to "".
            options (Dict[int, str], optional): Alternative translations. Defaults to None.
            default_plurals (Dict[int, str], optional): Plural forms of the main translation. Defaults to None.
            options_plurals (Dict[int, Dict[int, str]], optional): Plural forms for alternative translations. Defaults to None.
            context (str, optional): Context information for the translation. Defaults to "".
            metadata (Dict[str, Any], optional): Metadata about the translation. Defaults to None.
        """
        self.id = id
        self.default = default
        self.options = {}
        self.default_plurals = {}
        self.options_plurals = StrictNestedDictionary()
        self.context = context
        self.metadata = _build_empty_metadata()

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
            self.add_metadata(metadata)

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
                Supported keys: "translation" (str), "options" (Dict[int, str]),
                "default_plurals" (Dict[int, str]), "options_plurals" (Dict[int, Dict[int, str]]).

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
                Supported keys: "translation" (str), "options" (Dict[int, str]),
                "default_plurals" (Dict[int, str]), "options_plurals" (Dict[int, Dict[int, str]]).

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
                    setattr(self, attr_name, value)
                else:
                    raise ValueError(f"The '{attr_name}' value is malformed")

    # TODO delete message

    def remove_message(self) -> None:
        pass

    # Managing main

    def get_main(self) -> List[str]:
        """
        Get the main translation and its plural forms.

        Returns:
            List[str]: A formatted list containing the main translation and all plural forms.
        """
        translations = [self.default]
        if self.default_plurals:
            translations.extend(self.default_plurals.values())
        return translations

    def get_main_plurals(self) -> List[str]:
        """
        Get the main translation's plural forms.

        Returns:
            List[str]: The list of plural forms.
        """
        plurals = []
        if self.default_plurals:
            plurals.extend(self.default_plurals.values())
        return plurals

    def add_main(self, *args, **kwargs) -> None:
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
            singular_token = kwargs.pop("default", None)
            if singular_token is not None and singular_token != "":
                self.default = singular_token
                self.metadata[["count", "singular"]] = self.__count_singular__()
            else:
                raise ValueError(
                    f"Singular of translation is required and cannot be None or empty : '{singular_token}'"
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

    def update_main(self, *args, **kwargs) -> None:
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
                for index, token in enumerate(translation[1:]):
                    if token is not None and token != "":
                        self.default_plurals[index + 1] = token
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
                    for index, token in enumerate(pop_plurals):
                        d_pop_plural[index + 1] = token
                    self.default_plurals = d_pop_plural
                else:
                    raise (
                        ValueError(
                            f"plural translation context is malformed : {pop_plurals}"
                        )
                    )
        else:
            raise (ValueError("No updates specified"))

    # TODO delete main translation

    def remove_main(self):
        pass

    # Managing variant

    def get_variant(self, option: int) -> List[str]:
        """
        Get the alternative translation and its plural forms for a specific location index.

        Args:
            option (int): The location index of the alternative translation.

        Returns:
            List[str]: A list containing the alternative translation and all its plural forms.

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

    def get_variant_plurals(self, option: int = 0) -> List[str]:
        """
        Get the alternative translation's plural forms.
        :param option: Option number of the alternative translation.
        :return: the list of plural forms.
        :rtype: List[str]
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
                for index, token in enumerate(translation[1:]):
                    self.options_plurals[[option, index + 1]] = token
            else:
                self.options_plurals.update({option: {}})

            self.metadata[["count", "plurals"]] = self.__count_plurals__()
        elif kwargs:
            # Managing alternate translation in kwargs (obliviate if args is not None)
            singular_token = kwargs.pop("options", None)
            if singular_token is not None and singular_token != "":
                self.options[option] = singular_token
                self.metadata[["count", "singular"]] = self.__count_singular__()
            else:
                raise ValueError(
                    f"Singular of a variant is required and cannot be None or empty : '{singular_token}'"
                )
            # Managing alternate plurals
            alt_plural = kwargs.pop("options_plurals", None)
            if alt_plural is not None:
                if isinstance(alt_plural, dict) and _check_index_dict(alt_plural):
                    self.options_plurals.update({option: alt_plural})
                elif isinstance(alt_plural, list):
                    d_alt_plural = {}
                    for index, token in enumerate(alt_plural):
                        d_alt_plural[index + 1] = token
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
            self.update_main(*args, **kwargs)
        elif option > len(self.options) or option <= 0:
            raise (IndexError(f"Option '{option}' out of range"))
        elif args and len(args) == 1 and isinstance(args[0], list):
            translation = args[0]
            if translation[0] is not None and translation[0] != "":
                self.options[option] = translation[0]

            if len(translation) > 1:
                for index, token in enumerate(translation[1:]):
                    if token is not None and token != "":
                        self.options_plurals[[option, index + 1]] = token
        elif kwargs:
            print("kwargs :", kwargs)
            pop_text = kwargs.pop("options", None)
            if pop_text is not None and pop_text != "":
                self.options[option] = pop_text

            pop_plurals = kwargs.pop("options_plurals", None)
            if pop_plurals is not None:
                if isinstance(pop_plurals, dict) and _check_index_dict(pop_plurals):
                    print("Alternatives plural :", pop_plurals)
                    self.options_plurals.update({option: pop_plurals})
                elif isinstance(pop_plurals, list):
                    d_pop_plural = {}
                    for index, token in enumerate(pop_plurals):
                        d_pop_plural[index + 1] = token
                    self.options_plurals.update({option: d_pop_plural})
                else:
                    raise (
                        ValueError(
                            f"Plural translation context is malformed : {pop_plurals}"
                        )
                    )
        else:
            raise (ValueError("No updates specified"))

    # TODO delete variant

    def remove_variant(self):
        pass

    # managing segments in translations

    def get_main_segment(self, token: int = 0) -> str:
        """
        Private function to get token in the main translation
        :param token: segment's location in the main translation
        :type token: int
        :return: the corresponding segment located at the token location
        :rtype: str
        """
        __translation = self.get_main()
        print(len(__translation), "/", token)
        if len(__translation) > token >= 0:
            return __translation[token]
        else:
            raise (IndexError(f"Segment location '{token}' is out of range"))

    def get_variant_segment(self, option: int = 1, token: int = 0) -> str:
        """
        Private function to get token in the variant translation
        :param option: segment's option in the variant translation
        :type option: int
        :param token: segment's location in the variant option
        :type token: int
        :return: the corresponding segment located at the token location of the variant option
        """
        try:
            __translation = self.get_variant(option)

            if len(__translation) > token >= 0:
                return __translation[token]
            else:
                raise (
                    IndexError(
                        f"Segment location '{token}' of variant option '{option}' is out of range"
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
            return self.get_variant_segment(option=option, token=token)

    def add_main_segment(self, segment: str, token: int = 0) -> None:
        """
        Add a plural form to the message.

        Args:
            token (int): location of segment in the main translation, if token = 0 change self.default is is None
            segment (str): The text for the plural form.

        Raises:
            ValueError: If the index is less than or equal to 0.
        """
        if token == 0:
            if segment != "":
                self.default = segment
            else:
                raise ValueError(
                    f"Singular of translation is required and cannot be None or empty : '{segment}'"
                )
        elif 0 < token <= len(self.default_plurals) + 1:
            self.default_plurals[token] = segment
        else:
            raise ValueError(f"Plural form index ({token}) is not in a valid range")

    def _add_default_plurals_segment(self, segment: str) -> None:
        """
        Protected method to add an item in the default plural form to the message.
        :param segment:
        :return:
        """
        if segment != "":
            self.default_plurals[len(self.default_plurals) +1] = segment
        else:
            raise ValueError("Empty plural cannot be added")

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
        if segment != "":
            self.options[len(self.options) + 1] = segment
        else:
            raise ValueError("Option segment to be added cannot be empty")

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

    # TODO update_component

    def update_main_segment(self):
        pass

    # TODO update_plural_component

    def _update_default_plurals(self):
        pass

    def update_variant_segment(self):
        pass

    # TODO update_alternative_component

    def _update_options_segment(self, segment: str) -> None:
        pass

    # TODO update_alternative_plural_component

    def _update_options_plurals_segment(self, segment: str, option: int) -> None:
        pass


    def update_plural_form(self, index: int, translation: str) -> None:
        """
        Update a plural form translation.

        Args:
            index (int): The plural form index.
            translation (str): The updated translation text for the plural form.

        Raises:
            KeyError: If the plural form index does not exist.
        """
        if index not in self.default_plurals.keys():
            raise KeyError(f"Plural form index {index} not found")
        else:
            self.default_plurals[index] = translation

    def update_alternative_plural_form(
        self, alt_index: int, plural_index: int, translation: str
    ) -> None:
        """
        Update a plural form for a specific alternative translation.

        Args:
            alt_index (int): The alternative translation index.
            plural_index (int): The plural form index.
            translation (str): The updated translation text for the plural form.

        Raises:
            KeyError: If the alternative or plural form index does not exist.
        """
        if alt_index not in self.options_plurals[plural_index].keys():
            raise KeyError(f"Alternative translation at index {alt_index} not found")
        elif plural_index not in self.options_plurals[alt_index].keys():
            raise KeyError(f"Alternative translation at index {plural_index} not found")
        else:
            self.options_plurals[plural_index][plural_index] = translation

    # TODO delete_component

    def remove_main_segment(self):
        pass

    # TODO delete_plural_component

    def _remove_default_plurals_segment(self):
        pass

    # TODO delete_alternative_component

    def remove_variant_segment(self):
        pass

    def _remove_options_segment(self):
        pass

    # TODO delete_alternative_plural_component

    def _remove_options_plurals_segment(self):
        pass


    def del_translation(self) -> None:
        """
        Delete the base translation from the message.
        """
        self.default = ""

    def del_alternatives(self) -> None:
        """
        Delete all alternative translations from the message.
        """
        self.options = {}

    def del_plural_form(self, index: int = None) -> None:
        """
        Delete plural form translations.

        Args:
            index (int, optional): If provided, deletes only the specified plural form; otherwise deletes all.

        Raises:
            KeyError: If the specified index is out of range.
        """
        if index is None:
            self.default_plurals = {}
        elif index > 0 or index <= len(self.default_plurals):
            self.default_plurals[index] = ""
        else:
            raise KeyError(f"Alternative translation at index {index} is out of range")

    def del_alternative_plural_form(self, index: int = None) -> None:
        """
        Delete plural forms associated with alternative translations.

        Args:
            index (int, optional): If provided, deletes only the plural forms for the specified alternative; otherwise deletes all.

        Raises:
            KeyError: If the specified index is out of range.
        """
        if index is None:
            self.options_plurals = {}
        elif index > 0 or index <= len(self.options_plurals):
            self.options_plurals[index] = {}
        else:
            raise KeyError(f"Alternative translation at index {index} is out of range")

    # Switching and toggling translations


    # Managing metadata

    def get_metadata(
        self, key: Optional[Union[List[str], str]] = None
    ) -> Union[Dict[str, Any], Any]:
        """
        Get metadata from the message.

        Args:
            key (List[str] or str, optional): The specific metadata key to retrieve.
                If None, returns all metadata. Defaults to None.

        Returns:
            Union[Dict[str, Any], Any]: The requested metadata. If key is None, returns the entire
                metadata dictionary. If key is provided, returns the value for that key.

        Raises:
            KeyError: If the specified key doesn't exist in the metadata.
        """
        if key is None:
            return self.metadata

        if (isinstance(key, str) and key in self.metadata) or (
            isinstance(key, list) and key in self.metadata.dict_paths()
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

    def add_comment(self, comment: str) -> None:
        """
        Add an author's comment to the message.

        Args:
            comment (str): The author's comment to add.
        """
        self.metadata["comment"] = comment

    def add_metadata(
        self, key_or_dict: Union[str, List[str], Dict[str, Any]], value: Any = None
    ) -> None:
        """
        Set metadata for the message.

        Args:
            key_or_dict (Union[str, Dict[str, Any]]): Either a specific key to set or a dictionary
                of metadata to replace the current metadata.
            value (Any, optional): The value to set for the key. Required if key_or_dict is a string.
                Ignored if key_or_dict is a dictionary. Defaults to None.

        Raises:
            ValueError: If key_or_dict is malformed and value is None.
        """

        self.metadata = _build_empty_metadata()

        if isinstance(key_or_dict, dict):
            __dict = StrictNestedDictionary(key_or_dict)
            for path in self.metadata.dict_paths():
                if path not in __dict.dict_paths():
                    raise ValueError(
                        f"The path {path} is not a present key in the metadata dictionary"
                    )
            self.metadata.update(__dict)
        elif value is None:
            raise ValueError(
                f"Value of '{key_or_dict}' cannot be None when setting a specific metadata key"
            )
        elif (
            isinstance(key_or_dict, list)
            and key_or_dict not in self.metadata.dict_paths()
        ):
            raise ValueError(
                f"The path {key_or_dict} is not a present key in the metadata dictionary"
            )
        elif isinstance(key_or_dict, str) and not self.metadata.is_key(key_or_dict):
            raise ValueError(
                f"The key '{key_or_dict}' is not a present key in the metadata dictionary"
            )
        else:
            self.metadata[key_or_dict] = value

    def update_metadata(self, metadata: Dict[str, Any]) -> None:
        """
        Update the message's metadata with new values.

        Args:
            metadata (Dict[str, Any]): Dictionary of metadata to merge with the current metadata.
        """
        if self.__check_metadata__(metadata):
            self.metadata.update(metadata)

    def del_metadata(self, key: Optional[str] = None) -> None:
        """
        Delete metadata from the message.

        Args:
            key (Optional[str], optional): The specific metadata key to delete.
                If None, clears all metadata.

        Raises:
            KeyError: If the specified key doesn't exist in the metadata.
        """
        if key is None:
            self.metadata.clear()
        elif key in self.metadata:
            del self.metadata[key]
        else:
            raise KeyError(f"Metadata key '{key}' not found")

    def to_i18n_tools_format(self) -> Dict[str, Any]:
        """
        Convert the Message to i18n_tools format.

        Returns:
            Dict[str, Any]: The message in i18n_tools format.
        """
        return message_to_i18n_tools_format(self)

    def format(self, option: int = 0, token: int = 0, **kwargs) -> str:
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

    @classmethod
    def from_i18n_tools(
        cls, message_id: str, i18n_tools_entry: Dict[str, Any]
    ) -> "Message":
        """
        Create a Message instance from an i18n_tools format entry.

        Args:
            message_id (str): The message ID.
            i18n_tools_entry (Dict[str, Any]): The i18n_tools format entry.

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
            metadata=entry.get("metadata", None),
        )

    def __str__(self) -> str:
        """
        Return the string representation of the message.

        Returns:
            str: The message translation.
        """
        return self.default

    def __repr__(self) -> str:
        """
        Return the representation of the message.

        Returns:
            str: The message representation.
        """
        return f"Message(id='{self.id}', translation='{self.default}')"


class Book:
    """
    A class for handling book of internationalization messages using the i18n_tools format.

    This class manages internationalization messages in a single domain and language.

    Attributes:
        messages (StrictNestedDictionary): A dictionary of messages in this book.
    """

    def __init__(self):
        pass


class Corpus:
    """
    A class for handling corpora as a collection of books in a single domain.

    This class manages multiple books of internationalization messages within a single domain.

    Attributes:
        repository (StrictNestedDictionary): The repository containing all messages.
        messages (Dict[str, Message]): A dictionary of messages in this corpus.
    """

    def __init__(
        self,
        repository: Optional[StrictNestedDictionary] = None,
        messages: Optional[List[Message]] = None,
    ):
        """
        Initialize a new Corpus instance.

        Args:
            repository (Optional[StrictNestedDictionary], optional): The repository containing translations. Defaults to None.
            messages (Optional[List[Message]], optional): List of messages to add to the corpus. Defaults to None.
        """
        self.repository = (
            repository if repository is not None else StrictNestedDictionary()
        )
        if messages is not None:
            for message in messages:
                self.messages[message.id] = message

    def add_repository(self, repository: StrictNestedDictionary) -> None:
        """
        Add a repository to the corpus.

        Args:
            repository (StrictNestedDictionary): The repository to add to the corpus.
        """
        self.repository = repository

    def add_message(self, message: Message) -> None:
        """
        Add a message to the corpus.

        Args:
            message (Message): The message to add to the corpus.
        """
        self.messages[message.id] = message


class Encyclopaedia:
    """
    A class for handling libraries as a collection of Corpus objects.

    This class manages multiple Corpus objects, providing a comprehensive collection
    of internationalization messages across different domains.

    Attributes:
        corpora (Dict[str, Corpus]): A dictionary of Corpus objects in this encyclopaedia.
    """

    pass

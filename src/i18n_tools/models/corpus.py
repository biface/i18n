"""
Corpus module
=============


"""

import re
from typing import Any, Dict, List, Optional, Union

from ndict_tools import StrictNestedDictionary

from i18n_tools import __version__
from i18n_tools.converter import (
    i18n_tools_to_unified_format,
    unified_format_to_i18n_tools,
    message_to_i18n_tools_format,
    i18n_tools_format_to_message_dict,
)

from i18n_tools.locale import normalize_language_tag


def _check_index_dict(dictionary: Dict[int, str]) -> bool:
    """
    This function verify that the keys of the given dictionary are less of equal to its length

    args:
        dictionary(Dict[int, str]): dictionary to check

    return:
        (bool): true if keys are less or equal to its length and false otherwise

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

    Attributes:
        message_id (str): A unique identifier assigned to each message, ensuring that messages can be easily referenced and managed within the translation system.
        translation (str): The primary text of the message, serving as the default translation when no specific alternatives or plural forms are required.
        alternatives (Dict[int, str]): A collection of alternative translations that can be used in different contexts or scenarios, allowing for flexibility in message presentation based on specific needs.
        plural_forms (Dict[int, str]): A set of translations that account for different pluralization rules, accommodating languages with multiple plural forms.
        alternative_plural_forms (Dict[int, Dict[int, str]]): Plural forms associated with alternative translations, providing comprehensive support for various linguistic pluralization requirements.
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
        data_to_check = value if value is not None else self.plural_forms

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
        data_to_check = value if value is not None else self.alternatives

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
        data_to_check = value if value is not None else self.alternative_plural_forms
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
        if len(self.translation) > 0:
            count += 1 + len(self.alternatives)

        return count

    def __count_plurals__(self) -> List[int]:
        """
        Get the list of plurals for each singular or alternative singular.

        Returns:
            List[int]: The list of count of plurals for each singular.
        """
        counts = [len(self.plural_forms)]
        for index in range(1, len(self.alternatives) + 1):
            if index in self.alternative_plural_forms.keys():
                counts.append(len(self.alternative_plural_forms[index]))
            else:
                counts.append(0)

        return counts

    def __init__(
        self,
        message_id: str,
        translation: str = "",
        alternatives: Optional[Dict[int, str]] = None,
        plural_forms: Optional[Dict[int, str]] = None,
        alternative_plural_forms: Optional[Dict[int, Dict[int, str]]] = None,
        context: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize a new Message instance.

        Args:
            message_id (str): The unique identifier for the message.
            translation (str, optional): The main translation text. Defaults to "".
            alternatives (Dict[int, str], optional): Alternative translations. Defaults to None.
            plural_forms (Dict[int, str], optional): Plural forms of the main translation. Defaults to None.
            alternative_plural_forms (Dict[int, Dict[int, str]], optional): Plural forms for alternative translations. Defaults to None.
            context (str, optional): Context information for the translation. Defaults to "".
            metadata (Dict[str, Any], optional): Metadata about the translation. Defaults to None.
        """
        self.message_id = message_id
        self.translation = translation
        self.alternatives = {}
        self.plural_forms = {}
        self.alternative_plural_forms = {}
        self.context = context
        self.metadata = _build_empty_metadata()

        # Process standard attributes with a parameterized loop
        for attr_name, attr_value, check_method in [
            ("alternatives", alternatives, self.__check_alternatives__),
            ("plural_forms", plural_forms, self.__check_plural_forms__),
            (
                "alternative_plural_forms",
                (
                    StrictNestedDictionary(alternative_plural_forms)
                    if alternative_plural_forms is not None
                    and len(alternative_plural_forms) > 0
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

        # Special handling for metadata due to its additional checks
        if metadata is not None:
            if metadata.keys() != self.metadata.keys():
                raise KeyError(
                    f"The metadata dictionary is malformed : {metadata.keys()} are not standard."
                )
            elif metadata["count"].keys() != self.metadata["count"].keys():
                raise KeyError(
                    f"The count dictionary is malformed : {metadata['count'].keys()} are not standard"
                )
            elif self.__check_metadata__(metadata):
                self.metadata.update(metadata)
            else:
                raise ValueError(
                    f"The metadata dictionary is malformed : {metadata.keys()} are not standard."
                )

        # Update counters in metadata

        self.metadata[["count", "singular"]] = self.__count_singular__()
        self.metadata[["count", "plurals"]] = self.__count_plurals__()

    def get_id(self) -> str:
        """
        Get the unique identifier for the message.

        Returns:
            str: The message identifier.
        """
        return self.message_id

    def get_translation(self) -> List[str]:
        """
        Get the main translation and its plural forms.

        Returns:
            List[str]: A formatted list containing the main translation and all plural forms.
        """
        translations = [self.translation]
        if self.plural_forms:
            translations.extend(self.plural_forms.values())
        return translations

    def get_message(self) -> str:
        """
        Get the message string from the message.

        Returns:
            str: The content of the message.
        """
        return self.get_translation()[0]

    def get_plural(self) -> List[str]:
        """
        Get the main translation's plural forms.
        :return: The list of plural forms.
        :rtype: List[int]
        """
        plurals = []
        if self.plural_forms:
            plurals.extend(self.plural_forms.values())
        return plurals

    def get_plural_form(self, loc: int) -> str:
        """
        Get the requested plural form registered in messages.

        Args:
            loc (int): The index of the requested plural.

        Returns:
            str: The requested plural form.

        Raises:
            IndexError: If the location index doesn't exist.
        """
        if loc > len(self.plural_forms) or loc <= 0:
            raise IndexError(f"The location {loc} index is out of range")
        else:
            return self.plural_forms[loc]

    def get_alternative(self, loc: int) -> List[str]:
        """
        Get the alternative translation and its plural forms for a specific location index.

        Args:
            loc (int): The location index of the alternative translation.

        Returns:
            List[str]: A list containing the alternative translation and all its plural forms.

        Raises:
            IndexError: If the specified location index doesn't exist.
        """
        alternatives = []
        try:
            # Add the main alternative translation
            alternatives.append(self.alternatives[loc])

            # Add plural forms if they exist
            if loc in self.alternative_plural_forms:
                alternatives.extend(self.alternative_plural_forms[loc].values())

            return alternatives
        except KeyError:
            raise IndexError(f"Alternative translation at index {loc} not found")

    def get_alternative_plural_form(self, loc: int, index: int) -> str:
        """
        Get the requested alternative plural form registered in messages.

        Args:
            loc (int): The index of the requested plural.
            index (int): The index of the alternative plural form.

        Returns:
            str: The requested plural form.

        Raises:
            IndexError: If the location index or alternative index is out of range.
        """
        if loc > len(self.alternative_plural_forms) or loc <= 0:
            raise IndexError(f"The alternative message index ({loc}) is out of range")
        elif index > len(self.alternative_plural_forms[loc]) or index <= 0:
            raise IndexError(
                f"The plural index ({index}) of alternative message ({loc}) is out of range"
            )
        else:
            return self.alternative_plural_forms[loc][index]

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

    def get_alternative_message(self, loc: int) -> str:
        """
        Get the alternative message from the message.

        Args:
            loc (int): The location (index plus one) of the alternative translation.

        Returns:
            str: The content of the alternative message at the specified location.

        Raises:
            IndexError: If the specified location doesn't exist.
        """
        return self.get_alternative(loc)[0]

    def add_translation(self, **kwargs) -> None:
        """
        Add a translation to the message.

        Args:
            kwargs (dict): Keyword arguments related to instance attribute to be added to the message.

        Returns:

            None: instance is updated with parameters

        Raises:
            ValueError: If the keyword "translation" is missing, or translation is empty
            TypeError: If the keyword for dict attributes are evaluated with a different type
            KeyError: If the index of dict value are not compatible with target expectations
        """
        __translation = kwargs.pop("translation", None)

        if __translation is None:
            raise ValueError("At least one translation is required")
        else:
            self.translation = __translation

            # Process attributes with a parameterized loop using validation methods
            for attr_name, check_method in [
                ("alternatives", self.__check_alternatives__),
                ("plural_forms", self.__check_plural_forms__),
                ("alternative_plural_forms", self.__check_alternative_plural_forms__),
            ]:
                value = kwargs.pop(attr_name, None)
                if value is not None:
                    if check_method(value):
                        setattr(self, attr_name, value)
                    else:
                        raise ValueError(f"The {attr_name} value is malformed")

    def add_plural_form(self, index: int, translation: str) -> None:
        """
        Add a plural form to the message.

        Args:
            index (int): The index of the plural form.
            translation (str): The translation text for the plural form.

        Raises:
            ValueError: If the index is less than or equal to 0.
        """
        if index <= 0 or index > len(self.plural_forms) + 1:
            raise ValueError(f"Plural form index ({index}) is not in a valid range")
        self.plural_forms[index] = translation

    def add_alternative(self, index: int, translation: str) -> None:
        """
        Add an alternative translation to the message.

        Args:
            index (int): The index of the alternative translation.
            translation (str): The alternative translation text.

        Raises:
            ValueError: If the index is less than or equal to 0.
        """
        if index <= 0 or index > len(self.alternatives) + 1:
            raise ValueError(f"Alternative index ({index}) is not in a valid range")
        self.alternatives[index] = translation

    def add_alternative_plural_form(
        self, alt_index: int, plural_index: int, translation: str
    ) -> None:
        """
        Add a plural form to an alternative translation.

        Args:
            alt_index (int): The index of the alternative translation.
            plural_index (int): The index of the plural form.
            translation (str): The translation text for the plural form.

        Raises:
            ValueError: If alt_index or plural_index is less than or equal to 0.
            KeyError: If the alternative translation at alt_index doesn't exist.
        """
        if alt_index <= 0 or alt_index > len(self.alternatives) + 1:
            raise ValueError(f"Alternative index ({alt_index}) in not in a valid range")
        if plural_index <= 0 or plural_index > len(self.plural_forms) + 1:
            raise ValueError(
                f"Plural form index ({plural_index}) is not in a valid range"
            )

        if alt_index not in self.alternatives:
            raise KeyError(f"Alternative translation at index ({alt_index}) not found")

        if alt_index not in self.alternative_plural_forms:
            self.alternative_plural_forms[alt_index] = {}

        self.alternative_plural_forms[alt_index][plural_index] = translation

    def add_location(self, index: int, file: str) -> None:
        """
        Add a location to the message.
        :param index: line in the file where the translation should be written.
        :param file: file where the translation should be written.
        :return:
        """
        self.metadata["location"].append((file, index))

    def add_language(self, lang: str) -> None:
        """
        Add a language to the message.
        :param lang: an IETF language code.
        :type lang: str
        :return: nothing
        """
        self.metadata["language"] = normalize_language_tag(lang)

    def add_comment(self, comment: str) -> None:
        """
        Add an author's comment to the message.
        :param comment: an author's comment to add to the message.
        :type comment: str
        :return: nothing
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
            ValueError: If key_or_dict is a string and value is None.
        """

        self.metadata = _build_empty_metadata()

        if isinstance(key_or_dict, dict):
            __dict = StrictNestedDictionary(key_or_dict)
            for key in self.metadata.dict_paths():
                if key not in __dict.dict_paths():
                    raise ValueError(
                        f"The key {key} is not a present key in the metadata dictionary"
                    )
            self.metadata.update(__dict)
        else:
            if value is None:
                raise ValueError(
                    "Value cannot be None when setting a specific metadata key"
                )
            self.metadata[key_or_dict] = value

    def update_translation(self, translation: str) -> None:
        """
        Update the translation.
        :param translation: translation text to be updated.
        :return:
        """
        self.translation = translation

    def update_plural_form(self, index: int, translation: str) -> None:
        """
        Update the plural form.
        :param index: the index of the plural form.
        :param translation: the translation text for the plural form.
        :return:
        """
        if index not in self.plural_forms.keys():
            raise KeyError(f"Plural form index {index} not found")
        else:
            self.plural_forms[index] = translation

    def update_alternative(self, index: int, alternative: str) -> None:
        """
        Update the alternative translation.
        :param index: the index of the alternative translation.
        :param alternative: the alternative translation text.
        :return:
        """
        if index not in self.alternatives.keys():
            raise KeyError(f"Alternative translation at index {index} not found")
        else:
            self.alternatives[index] = alternative

    def update_alternative_plural_form(
        self, alt_index: int, plural_index: int, translation: str
    ) -> None:
        """
        Update the alternative plural form.
        :param alt_index: the index of the alternative translation.
        :param plural_index: the index of the plural form.
        :param translation: the translation text for the plural form.
        :return:
        """
        if alt_index not in self.alternative_plural_forms[plural_index].keys():
            raise KeyError(f"Alternative translation at index {alt_index} not found")
        elif plural_index not in self.alternative_plural_forms[alt_index].keys():
            raise KeyError(f"Alternative translation at index {plural_index} not found")
        else:
            self.alternative_plural_forms[plural_index][plural_index] = translation

    def update_metadata(self, metadata: Dict[str, Any]) -> None:
        """
        Update the message's metadata with new values.

        Args:
            metadata (Dict[str, Any]): Dictionary of metadata to merge with the current metadata.
        """
        if self.__check_metadata__(metadata):
            self.metadata.update(metadata)

    def del_translation(self) -> None:
        """
        Delete the translation from the message.
        :return:
        """
        self.translation = ""

    def del_alternatives(self) -> None:
        """
        Delete the alternative translation from the message.
        :return:
        """
        self.alternatives = {}

    def del_plural_form(self, index: int = None) -> None:
        """
        Delete the plural form translation from the message.
        :param index: if not None, the index of the plural form to delete.
        :return:
        """
        if index is None:
            self.plural_forms = {}
        elif index > 0 or index <= len(self.plural_forms):
            self.plural_forms[index] = ""
        else:
            raise KeyError(f"Alternative translation at index {index} is out of range")

    def del_alternative_plural_form(self, index: int = None) -> None:
        """
        Delete the plural form translation from the message.
        :param index: if not None, the index of the plural form to delete.
        :return:
        """
        if index is None:
            self.alternative_plural_forms = {}
        elif index > 0 or index <= len(self.alternative_plural_forms):
            self.alternative_plural_forms[index] = {}
        else:
            raise KeyError(f"Alternative translation at index {index} is out of range")

    def del_metadata(self, key: Optional[str] = None) -> None:
        """
        Delete metadata from the message.

        Args:
            key (Optional[str], optional): The specific metadata key to delete.
                If None, clears all metadata. Defaults to None.

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

    def format(self, alternative: int = 0, plural_index: int = 0, **kwargs) -> str:
        """
        Format the message with the provided variables.

        Args:
            alternative (int, optional): The alternative index to use. Defaults to 0.
            plural_index (int, optional): The plural form index to use. Defaults to 0.
            **kwargs: Variables to use for formatting.

        Returns:
            str: The formatted message.
        """
        # Determine which text to format based on alternative and plural_index
        if alternative > 0 and alternative in self.alternatives:
            if (
                plural_index > 0
                and alternative in self.alternative_plural_forms
                and plural_index in self.alternative_plural_forms[alternative]
            ):
                text = self.alternative_plural_forms[alternative][plural_index]
            else:
                text = self.alternatives[alternative]
        elif plural_index > 0 and plural_index in self.plural_forms:
            text = self.plural_forms[plural_index]
        else:
            text = self.translation

        # Format the text using the provided variables
        try:
            return text.format(**kwargs)
        except KeyError as e:
            missing_var = str(e).strip("'")
            raise KeyError(
                f"Missing variable '{missing_var}' for message '{self.message_id}'"
            )
        except Exception as e:
            raise ValueError(f"Error formatting message '{self.message_id}': {str(e)}")

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
            message_id=message_id,
            translation=entry.get("translation", ""),
            plural_forms=entry.get("plural_forms", None),
            alternatives=entry.get("alternatives", None),
            alternative_plural_forms=entry.get("alternative_plural_forms", None),
            context=entry.get("context", ""),
            metadata=entry.get("metadata", None),
        )

    def __str__(self) -> str:
        """
        Return the string representation of the message.

        Returns:
            str: The message translation.
        """
        return self.translation

    def __repr__(self) -> str:
        """
        Return the representation of the message.

        Returns:
            str: The message representation.
        """
        return f"Message(id='{self.message_id}', translation='{self.translation}')"


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
                self.messages[message.message_id] = message

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
        self.messages[message.message_id] = message


class Encyclopaedia:
    """
    A class for handling libraries as a collection of Corpus objects.

    This class manages multiple Corpus objects, providing a comprehensive collection
    of internationalization messages across different domains.

    Attributes:
        corpora (Dict[str, Corpus]): A dictionary of Corpus objects in this encyclopaedia.
    """

    pass

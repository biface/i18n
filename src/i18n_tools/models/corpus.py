"""
Corpus module
=============


"""
import re

from ndict_tools import StrictNestedDictionary
from typing import List, Optional, Dict, Any, Union

from i18n_tools.converter import i18n_tools_to_unified_format, unified_format_to_i18n_tools
from i18n_tools.loaders import fetch_dictionary, dump_dictionary

class Message:
    """
    A class for handling internationalization messages using the i18n_tools specifications.

    This class provides functionality to create, store, and format messages for
    internationalization purposes. It uses the native i18n_tools format for storing
    messages and supports formatting using f-strings with variables.

    Attributes:
        message_id (str): The unique identifier for the message.
        translation (str): The main translation text.
        alternatives (Dict[int, str]): Alternative translations.
        plural_forms (Dict[int, str]): Plural forms of the main translation.
        alternative_plural_forms (Dict[int, Dict[int, str]]): Plural forms for alternative translations.
        context (str): Context information for the translation.
        metadata (Dict[str, Any]): Metadata about the translation.
    """

    def __init__(
        self,
        message_id: str,
        translation: str = "",
        alternatives: Optional[Dict[int, str]] = None,
        plural_forms: Optional[Dict[int, str]] = None,
        alternative_plural_forms: Optional[Dict[int, Dict[int, str]]] = None,
        context: str = "",
        metadata: Optional[Dict[str, Any]] = None
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
        self.alternatives = alternatives or {}
        self.plural_forms = plural_forms or {}
        self.alternative_plural_forms = alternative_plural_forms or {}
        self.context = context
        self.metadata = metadata or {}

    def get_translation(self) -> List[str]:
        """
        Get the main translation and its plural forms.

        Returns:
            List[str]: A list containing the main translation and all plural forms.
        """
        translations = [self.translation]
        if self.plural_forms:
            translations.extend(self.plural_forms.values())
        return translations

    def get_alternative(self, loc: int) -> List[str]:
        """
        Get the alternative translation and its plural forms for a specific location index.

        Args:
            loc (int): The location index of the alternative translation.

        Returns:
            List[str]: A list containing the alternative translation and all its plural forms.

        Raises:
            KeyError: If the specified location index doesn't exist.
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
            raise KeyError(f"Alternative translation at index {loc} not found")

    @classmethod
    def from_unified_format(cls, message_id: str, unified_entry: Dict[str, Any]) -> 'Message':
        """
        Create a Message instance from a unified format entry.

        Args:
            message_id (str): The message ID.
            unified_entry (Dict[str, Any]): The unified format entry.

        Returns:
            Message: A new Message instance.
        """
        # Convert string keys to integer keys for alternatives and plural forms
        alternatives = {}
        for k, v in unified_entry.get("alternatives", {}).items():
            alternatives[int(k)] = v

        plural_forms = {}
        for k, v in unified_entry.get("plural_forms", {}).items():
            plural_forms[int(k)] = v

        alternative_plural_forms = {}
        for alt_idx_str, alt_plural_dict in unified_entry.get("alternative_plural_forms", {}).items():
            alt_idx = int(alt_idx_str)
            alternative_plural_forms[alt_idx] = {}
            for plural_idx_str, plural_form in alt_plural_dict.items():
                alternative_plural_forms[alt_idx][int(plural_idx_str)] = plural_form

        return cls(
            message_id=message_id,
            translation=unified_entry.get("translation", ""),
            alternatives=alternatives,
            plural_forms=plural_forms,
            alternative_plural_forms=alternative_plural_forms,
            context=unified_entry.get("context", ""),
            metadata=unified_entry.get("metadata", {})
        )

    @classmethod
    def from_i18n_tools_format(cls, message_id: str, i18n_tools_entry: Dict[str, Any]) -> 'Message':
        """
        Create a Message instance from an i18n_tools format entry.

        Args:
            message_id (str): The message ID.
            i18n_tools_entry (Dict[str, Any]): The i18n_tools format entry.

        Returns:
            Message: A new Message instance.
        """
        # Convert i18n_tools format to unified format
        unified_data = i18n_tools_to_unified_format({message_id: i18n_tools_entry})
        if message_id in unified_data:
            return cls.from_unified_format(message_id, unified_data[message_id])
        return cls(message_id=message_id)

    @classmethod
    def from_repository(
        cls,
        repository: Dict[str, Any],
        module: str,
        domain: str,
        lang: str,
        message_id: str
    ) -> 'Message':
        """
        Create a Message instance from a repository.

        Args:
            repository (Dict[str, Any]): The repository containing translations.
            module (str): The module name.
            domain (str): The domain name.
            lang (str): The language code.
            message_id (str): The message ID to find.

        Returns:
            Message: A new Message instance.

        Raises:
            KeyError: If the message ID is not found.
        """
        try:
            translations = fetch_dictionary(repository, module, domain, lang)
            if message_id in translations:
                return cls.from_i18n_tools_format(message_id, translations[message_id])
            raise KeyError(f"{message_id} not found in {module}/{domain} in {lang}")
        except Exception as e:
            raise e

    def to_unified_format(self) -> Dict[str, Any]:
        """
        Convert the Message to unified format.

        Returns:
            Dict[str, Any]: The message in unified format.
        """
        # Convert integer keys to string keys for alternatives and plural forms
        alternatives = {}
        for k, v in self.alternatives.items():
            alternatives[str(k)] = v

        plural_forms = {}
        for k, v in self.plural_forms.items():
            plural_forms[str(k)] = v

        alternative_plural_forms = {}
        for alt_idx, alt_plural_dict in self.alternative_plural_forms.items():
            alternative_plural_forms[str(alt_idx)] = {}
            for plural_idx, plural_form in alt_plural_dict.items():
                alternative_plural_forms[str(alt_idx)][str(plural_idx)] = plural_form

        return {
            "translation": self.translation,
            "alternatives": alternatives,
            "plural_forms": plural_forms,
            "alternative_plural_forms": alternative_plural_forms,
            "context": self.context,
            "metadata": self.metadata
        }

    def to_i18n_tools_format(self) -> Dict[str, Any]:
        """
        Convert the Message to i18n_tools format.

        Returns:
            Dict[str, Any]: The message in i18n_tools format.
        """
        unified_data = {self.message_id: self.to_unified_format()}
        i18n_tools_data = unified_format_to_i18n_tools(unified_data)
        return i18n_tools_data[self.message_id] if self.message_id in i18n_tools_data else {}

    def save_to_repository(
        self,
        repository: Dict[str, Any],
        module: str,
        domain: str,
        lang: str
    ) -> None:
        """
        Save the message to a repository.

        Args:
            repository (Dict[str, Any]): The repository to save to.
            module (str): The module name.
            domain (str): The domain name.
            lang (str): The language code.
        """
        try:
            translations = fetch_dictionary(repository, module, domain, lang)
            translations[self.message_id] = self.to_i18n_tools_format()
            dump_dictionary(repository, translations, module, domain, lang)
        except Exception as e:
            raise e

    def _extract_variables(self, text: str) -> List[str]:
        """
        Extract variable names from a formatted string.

        Args:
            text (str): The formatted string.

        Returns:
            List[str]: List of variable names.
        """
        # Find all {variable} patterns in the string
        pattern = r'\{([^{}]+)\}'
        return re.findall(pattern, text)

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
            if plural_index > 0 and alternative in self.alternative_plural_forms and plural_index in self.alternative_plural_forms[alternative]:
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
            raise KeyError(f"Missing variable '{missing_var}' for message '{self.message_id}'")
        except Exception as e:
            raise ValueError(f"Error formatting message '{self.message_id}': {str(e)}")

    def __str__(self) -> str:
        """
        Return the string representation of the message.

        Returns:
            str: The message translation.
        """
        return self.translation

    def add_plural_form(self, index: int, translation: str) -> None:
        """
        Add a plural form to the message.

        Args:
            index (int): The index of the plural form.
            translation (str): The translation text for the plural form.

        Raises:
            ValueError: If the index is less than or equal to 0.
        """
        if index <= 0:
            raise ValueError("Plural form index must be greater than 0")
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
        if index <= 0:
            raise ValueError("Alternative index must be greater than 0")
        self.alternatives[index] = translation

    def add_alternative_plural_form(self, alt_index: int, plural_index: int, translation: str) -> None:
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
        if alt_index <= 0:
            raise ValueError("Alternative index must be greater than 0")
        if plural_index <= 0:
            raise ValueError("Plural form index must be greater than 0")

        if alt_index not in self.alternatives:
            raise KeyError(f"Alternative translation at index {alt_index} not found")

        if alt_index not in self.alternative_plural_forms:
            self.alternative_plural_forms[alt_index] = {}

        self.alternative_plural_forms[alt_index][plural_index] = translation

    def get_metadata(self, key: Optional[str] = None) -> Union[Dict[str, Any], Any]:
        """
        Get metadata from the message.

        Args:
            key (Optional[str], optional): The specific metadata key to retrieve. 
                If None, returns all metadata. Defaults to None.

        Returns:
            Union[Dict[str, Any], Any]: The requested metadata. If key is None, returns the entire
                metadata dictionary. If key is provided, returns the value for that key.

        Raises:
            KeyError: If the specified key doesn't exist in the metadata.
        """
        if key is None:
            return self.metadata

        if key in self.metadata:
            return self.metadata[key]

        raise KeyError(f"Metadata key '{key}' not found")

    def set_metadata(self, key_or_dict: Union[str, Dict[str, Any]], value: Any = None) -> None:
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
        if isinstance(key_or_dict, dict):
            self.metadata = key_or_dict
        else:
            if value is None:
                raise ValueError("Value cannot be None when setting a specific metadata key")
            self.metadata[key_or_dict] = value

    def update_metadata(self, metadata: Dict[str, Any]) -> None:
        """
        Update the message's metadata with new values.

        Args:
            metadata (Dict[str, Any]): Dictionary of metadata to merge with the current metadata.
        """
        self.metadata.update(metadata)

    def delete_metadata(self, key: Optional[str] = None) -> None:
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

    def __repr__(self) -> str:
        """
        Return the representation of the message.

        Returns:
            str: The message representation.
        """
        return f"Message(id='{self.message_id}', translation='{self.translation}')"

class Book:
    """
    A class for handling book of internationalization messages using the i18n_tools format in a single domain and language.
    """
    messages = StrictNestedDictionary()
    pass

class Corpus:
    """
    A class for handling corpora as a collection of books in a single domain.
    """


    def __init__(self, repository: Optional[StrictNestedDictionary] = None, messages: Optional[List[Message]] = None):
        self.repository = repository if repository is not None else StrictNestedDictionary()
        if messages is not None:
            for message in messages:
                self.messages[message.message_id] = message

    def add_repository(self, repository: StrictNestedDictionary) -> None:
        """
        Add a repository to the corpus.
        """
        self.repository = repository

    def add_message(self, message: Message) -> None:
        """
        Add a message to the corpus.
        """
        self.messages[message.message_id] = message


class Encyclopaedia:
    """
    A class for handling libraries as a collection of Corpus.
    """
    pass

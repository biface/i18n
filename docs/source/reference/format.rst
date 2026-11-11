Proprietary Translation Format
===============================
The proprietary translation format used by `i18n-tools` is designed to handle translations efficiently across multiple languages. Key characteristics include:

- **Uniform Language Handling**: All languages are treated equally for translation purposes.
- **Consistent Identifiers**: The translation identifier is not tied to any specific language but must remain consistent across all translations.
- **Message Alternatives**: The base structure supports multiple message alternatives, including dynamic elements that can be interpreted using f-strings.

Atomic Cell Entity
------------------

The base structure is a JSON dictionary with the following format:

.. code-block:: json

    {
        "id": {
            "messages": [
                ["main_msg", "alt_1_msg", "alt_2_msg_with'{variable}'_inside"],
                ["plural_1_of_main_msg", "plural_1_of_alt_1_msg", "plural_1_of_alt_2_msg_with'{variable}'_inside"],
                ["plural_2_of_main_msg", "plural_2_of_alt_1_msg", "plural_2_of_alt_2_msg_with'{variable}'_inside"],
                ["plural_3_of_main_msg", "plural_3_of_alt_1_msg", "plural_3_of_alt_2_msg_without_variable_inside"]
            ],
            "metadata": {
                "singular_count": 3,
                "plural_counts": [3, 3, 3],
                "locations": [
                    ["path/to/source/file1.py", 123],
                    ["path/to/source/file2.py", 456]
                ],
                "flags": [
                    "fuzzy",
                    "python-format"
                ],
                "comments": "Translator comments or notes about the message"
            }
        }
    }

Message Strings
^^^^^^^^^^^^^^^

The data structure is a list of lists organized as follows:

- The first list contains the singular forms, where the first item (index 0) is the singular form found in the ``msg_str`` of i18n, and the other indices represent alternative messages.

- Subsequent lists contain plural forms, as many as needed to express the nuances required for the information.

Constraints apply to the dimensions of the lists:

- Plural lists must have the same number of items as the singular list, even if the item within the plurals is an empty string.

- For each list of plurals, the above constraint applies.

Cell Attached Metadata
^^^^^^^^^^^^^^^^^^^^^^

The metadata for each message follows the structure used by the Babel library in Python, which includes:

- **locations**: A list of source code locations where the message is used. Each location is represented as a list containing the file path and the line number.
- **flags**: A list of flags providing additional information about the message, such as whether it is "fuzzy" or uses "python-format".
- **comments**: Translator comments or notes about the message, providing context or special instructions.

Additionally, specific metadata for message strings can be included:

- **singular_count**: The number of singular message alternatives, including the main message.
- **plural_counts**: A list indicating the number of plural forms for each plural list.

Example of Specific Metadata
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: json

    {
        "metadata": {
            "singular_count": 3,
            "plural_counts": [3, 3, 3],
            "locations": [
                    ["path/to/source/file1.py", 123],
                    ["path/to/source/file2.py", 456]
                ],
            "flags": [
                    "fuzzy",
                    "python-format"
                ],
            "comments": "Translator comments or notes about the message"
        }
    }

Translation Dictionary Structure
--------------------------------

In the context of the organization, a dictionary represents a translation domain in a specific language. It consists of:

- **Message Entries**: Each entry is identified by a unique ID (e.g., ``id_1``, ``id_2``) and contains message strings along with their associated metadata. This includes singular and plural forms, as well as specific metadata like locations, flags, and comments.

- **Global Metadata**: Metadata that applies to the entire translation domain, providing contextual information and global declarations from translators, ensuring consistency and clarity.

**Example of Translation Dictionary**

Here is an example of how a translation dictionary is structured:

.. code-block:: json

    {
        "id_1": {
            "messages": [
                ["main_msg", "alt_1_msg", "alt_2_msg_with'{variable}'_inside"],
                ["plural_1_of_main_msg", "plural_1_of_alt_1_msg", "plural_1_of_alt_2_msg_with'{variable}'_inside"],
                ["plural_2_of_main_msg", "plural_2_of_alt_1_msg", "plural_2_of_alt_2_msg_with'{variable}'_inside"],
                ["plural_3_of_main_msg", "plural_3_of_alt_1_msg", "plural_3_of_alt_2_msg_without_variable_inside"]
            ],
            "metadata": {
                "locations": [
                    ["path/to/source/file1.py", 123],
                    ["path/to/source/file2.py", 456]
                ],
                "flags": [
                    "fuzzy",
                    "python-format"
                ],
                "comments": "Translator comments or notes about the message",
                "singular_count": 3,
                "plural_counts": [3, 3, 3],
            }
        },
        "id_2": {
            "messages": [
                ["another_main_msg", "another_alt_1_msg"],
                ["another_plural_1_of_main_msg", "another_plural_1_of_alt_1_msg"],
                ["another_plural_2_of_main_msg", "another_plural_2_of_alt_1_msg"]
            ],
            "metadata": {
                "locations": [
                    ["path/to/source/file3.py", 789]
                ],
                "flags": [
                    "python-format"
                ],
                "comments": "Additional translator comments or notes about the message",
                "singular_count": 2,
                "plural_counts": [2, 2],
            }
        },
        "metadata": {
            "project_id_version": "i18n-tools 1.0",
            "report_msgid_bugs_to": "bugs@example.com",
            "pot_creation_date": "2023-10-01 12:00+0100",
            "language_team": "French Team <french-team@example.com>",
            "statistics": {
                "total_words": 5678,
                "total_messages": 1234
            },
            "header_comment": "Global declarations or notes from translators about the translation domain"
        }
    }

In this example:

- **Message IDs**: Each message ID (e.g., ``id_1``, ``id_2``) contains message strings and their associated metadata, including singular and plural forms, as well as specific metadata like locations, flags, and comments.

- **Global Metadata**: The dictionary includes global metadata that applies to the entire translation domain, providing contextual information and global declarations from translators.

Global Metadata for Translation Domains
---------------------------------------

In addition to message-specific metadata, each translation domain includes global metadata that applies to the entire domain. This metadata provides contextual information and global declarations from translators, ensuring consistency and clarity.

Translation Repository Organization
===================================

**Introduction**

This document outlines the organization of a translation repository following a structured format for directories and files. This structure ensures that translation files are managed efficiently and consistently across different languages, modules, and packages. It is intended for developers, translators, and project managers to understand and follow the established conventions.

Repository Structure
--------------------

The translation repository is organized into the following directory structure:

.. code-block:: text

    <root>/
    ├── <repository>/
    │   ├── <module_1>/
    │   │   ├── locales/
    │   │   │   ├── domain-alpha_name_aggregated.json
    │   │   │   ├── templates/
    │   │   │   │   ├── domain-alpha_name.json
    │   │   │   │   └── domain-alpha_name.pot
    │   │   │   ├── <language_code>/
    │   │   │   │   └── LC_MESSAGES/
    │   │   │   │       ├── domain-alpha_name.po
    │   │   │   │       ├── domain-alpha_name.mo
    │   │   │   │       └── domain-alpha_name.json
    │   │   │   └── ...
    │   │   └── _i18n_tools/
    │   │       └── backup/
    │   │           └── domain-alpha_name.json.gzip
    │   ├── <module_2>/
    │   │   ├── locales/
    │   │   │   ├── domain-beta_name_aggregated.json
    │   │   │   ├── domain-iota_name_aggregated.json
    │   │   │   ├── templates/
    │   │   │   │   ├── domain-beta_name.json
    │   │   │   │   ├── domain-iota_name.json
    │   │   │   │   └── domain-beta_name.pot
    │   │   │   │   └── domain-iota_name.pot
    │   │   │   ├── <language_code>/
    │   │   │   │   └── LC_MESSAGES/
    │   │   │   │       ├── domain-beta_name.po
    │   │   │   │       ├── domain-beta_name.mo
    │   │   │   │       ├── domain-beta_name.json
    │   │   │   │       ├── domain-iota_name.po
    │   │   │   │       ├── domain-iota_name.mo
    │   │   │   │       └── domain-iota_name.json
    │   │   │   └── ...
    │   │   └── _i18n_tools/
    │   │       └── backup/
    │   │           ├── domain-beta_name.json.gzip
    │   │           └── domain-iota_name.json.gzip
    │   ├── <module_3>/
    │   │   ├── locales/
    │   │   │   ├── domain-gamma_name_aggregated.json
    │   │   │   ├── templates/
    │   │   │   │   ├── domain-gamma_name.json
    │   │   │   │   └── domain-gamma_name.pot
    │   │   │   ├── <language_code>/
    │   │   │   │   └── LC_MESSAGES/
    │   │   │   │       ├── domain-gamma_name.po
    │   │   │   │       ├── domain-gamma_name.mo
    │   │   │   │       └── domain-gamma_name.json
    │   │   │   └── ...
    │   │   ├── _i18n_tools/
    │   │   │   └── backup/
    │   │   │       └── domain-gamma_name.json.gzip
    │   │   ├── package_1/
    │   │   │   ├── locales/
    │   │   │   │   ├── domain-delta_name_aggregated.json
    │   │   │   │   ├── domain-iota_name_aggregated.json
    │   │   │   │   ├── templates/
    │   │   │   │   │   ├── domain-delta_name.json
    │   │   │   │   │   ├── domain-iota_name.json
    │   │   │   │   │   └── domain-delta_name.pot
    │   │   │   │   │   └── domain-iota_name.pot
    │   │   │   │   ├── <language_code>/
    │   │   │   │   │   └── LC_MESSAGES/
    │   │   │   │   │       ├── domain-delta_name.po
    │   │   │   │   │       ├── domain-delta_name.mo
    │   │   │   │   │       ├── domain-delta_name.json
    │   │   │   │   │       ├── domain-iota_name.po
    │   │   │   │   │       ├── domain-iota_name.mo
    │   │   │   │   │       └── domain-iota_name.json
    │   │   │   │   └── ...
    │   │   │   └── _i18n_tools/
    │   │   │       └── backup/
    │   │   │           ├── domain-delta_name.json.gzip
    │   │   │           └── domain-iota_name.json.gzip
    │   │   ├── package_2/
    │   │   │   ├── locales/
    │   │   │   │   ├── domain-epsilon_name_aggregated.json
    │   │   │   │   ├── templates/
    │   │   │   │   │   ├── domain-epsilon_name.json
    │   │   │   │   │   └── domain-epsilon_name.pot
    │   │   │   │   ├── <language_code>/
    │   │   │   │   │   └── LC_MESSAGES/
    │   │   │   │   │       ├── domain-epsilon_name.po
    │   │   │   │   │       ├── domain-epsilon_name.mo
    │   │   │   │   │       └── domain-epsilon_name.json
    │   │   │   │   └── ...
    │   │   │   └── _i18n_tools/
    │   │   │       └── backup/
    │   │   │           └── domain-epsilon_name.json.gzip
    │   ├── _i18n_tools/
    │   │   ├── <settings file>
    │   │   ├── backup/
    │   │   │   └── repository_backup.tar.gzip
    │   │   └── ...
    │   └── ...
    └── ...

Key Directories and Files
^^^^^^^^^^^^^^^^^^^^^^^^^

1. **<root>/**: The root directory for the translation repository, specified by the ``root`` path in the configuration. It serves as the base directory for all translation-related files.

2. **<repository>/**: The main repository directory, specified by the ``repository`` path. It contains subdirectories for each module, which include locales, language-specific translations, and metadata.

3. **<module_1>, <module_2>, .../**: Directories for each module, specified in the ``modules`` list in the configuration. Each module directory contains a ``locales`` directory and an ``_i18n_tools`` directory for metadata.

4. **<module_3>/package_1, <module_3>/package_2, .../**: Subdirectories within a module that represent different packages. Each package directory contains its own ``locales`` directory and an ``_i18n_tools`` directory for metadata.

5. **locales/** (:doc:`I18N_TOOLS_LOCALE <api/constant>`) : This directory, within each module or package directory, contains the ``templates`` directory and language-specific subdirectories.

6. **domain..._name_aggregated.json**: A JSON file at the base of each ``locales`` directory that aggregates metadata for the domain across all language codes. The "_aggregated" suffix helps differentiate it from other metadata files.

7. **templates/** (:doc:`I18N_TOOLS_TEMPLATE <api/constant>`): This directory contains the Portable Object Template (POT) files and JSON metadata files that serve as templates for translations. Each module or package has its own POT file named ``<domain-name>.pot`` and a corresponding JSON metadata file named ``<domain-name>.json``.

8. **<language_code>/**: A directory for each language supported by the application within the ``locales`` directory. The language code follows the `IETF language tag <https://en.wikipedia.org/wiki/IETF_language_tag>`_ format (e.g., ``fr`` for French, ``de`` for German).

9. **LC_MESSAGES/**: A subdirectory within each language directory that contains the actual translation files. This directory name is a convention used by gettext.

10. **<domain-name>.po, <domain-name>.mo, <domain-name>.json**: The Portable Object (PO) files, Machine Object (MO) files, and JSON metadata files contain the translations for a specific domain in a particular language. These files are named after the domain they correspond to (e.g., ``<domain-name>.po`` for the PO file).

11. **_i18n_tools/**: This directory, at the same level as ``locales``, contains metadata related to the translation dictionaries. It includes a ``backup`` directory for storing backup copies of metadata files.

12. **backup/**: The backup directory, located within the ``_i18n_tools`` directory. It is used to store backup copies of metadata files in a compressed format (e.g., ``<domain-name>.json.gzip``).

13. **<settings file>**: The settings file, specified by the ``settings`` path (default is ``i18n_tools.yaml``). It contains configuration details for the translation process.

14. **backup/**: The backup directory, located within the ``I18N_TOOLS_CONFIG`` directory. It contains an archive (``repository_backup.tar.gzip``) of the repository data, serving as a backup in case of data loss.

Benefits
^^^^^^^^

- **Consistency**: Ensures a consistent structure across different languages, modules, and packages.
- **Scalability**: Facilitates the addition of new languages, modules, and packages.
- **Maintainability**: Simplifies the process of updating and merging translations.

This structure adheres to the GNU gettext standards, promoting a streamlined and efficient translation process.

Proprietary Translation Format
------------------------------

The proprietary translation format used by `i18n-tools` is designed to handle translations efficiently across multiple languages. Key characteristics include:

- **Uniform Language Handling**: All languages are treated equally for translation purposes.
- **Consistent Identifiers**: The translation identifier is not tied to any specific language but must remain consistent across all translations.
- **Message Alternatives**: The base structure supports multiple message alternatives, including dynamic elements that can be interpreted using f-strings.

Atomic Cell Entity
^^^^^^^^^^^^^^^^^^

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
"""""""""""""""

The data structure is a list of lists organized as follows:

- The first list contains the singular forms, where the first item (index 0) is the singular form found in the ``msg_str`` of i18n, and the other indices represent alternative messages.

- Subsequent lists contain plural forms, as many as needed to express the nuances required for the information.

Constraints apply to the dimensions of the lists:

- Plural lists must have the same number of items as the singular list, even if the item within the plurals is an empty string.

- For each list of plurals, the above constraint applies.

Cell Attached Metadata
""""""""""""""""""""""

The metadata for each message follows the structure used by the Babel library in Python, which includes:

- **locations**: A list of source code locations where the message is used. Each location is represented as a list containing the file path and the line number.
- **flags**: A list of flags providing additional information about the message, such as whether it is "fuzzy" or uses "python-format".
- **comments**: Translator comments or notes about the message, providing context or special instructions.

Additionally, specific metadata for message strings can be included:

- **singular_count**: The number of singular message alternatives, including the main message.
- **plural_counts**: A list indicating the number of plural forms for each plural list.

Example of Specific Metadata
""""""""""""""""""""""""""""

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
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In addition to message-specific metadata, each translation domain includes global metadata that applies to the entire domain. This metadata provides contextual information and global declarations from translators, ensuring consistency and clarity.

The global metadata for a translation domain includes the following key elements:

1. **Project Identification**:
   - **project_id_version**: The identifier and version of the project, helping to track changes and updates across different versions.

2. **Reporting and Communication**:
   - **report_msgid_bugs_to**: The email address or URL where issues or bugs related to the translation should be reported.

3. **Creation Details**:
   - **pot_creation_date**: The date when the POT (Portable Object Template) file was created, indicating the initiation of the translation process.

4. **Team Information**:
   - **language_team**: The team responsible for the translation, including contact information for coordination and feedback.

5. **Statistics**:
   - **total_words**: The total number of words in the translation domain, providing an overview of the translation scope.
   - **total_messages**: The total number of messages, both translated and untranslated, within the domain.

6. **Global Declarations**:
   - **header_comment**: Global declarations or notes from translators about the translation domain. This field is used to provide contextual information, general instructions, or important remarks that apply to the entire domain.

Conversion of Alternative Messages
----------------------------------

To integrate alternative messages from the proprietary `i18n-tools` format into classic translation formats like Babel and i18next, an extended ID convention can be used. This approach ensures clarity and compatibility with existing tools.

Extended ID Convention in GNU i18n Standard
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The extended ID convention involves appending a numerical suffix to the base message ID to represent alternative messages and their plural forms. Here's how it works:

1. **Main Message**:
   - Use the base ID (e.g., ``id``) for the main message.
   - Example:

     .. code-block:: po

         msgid "id"
         msgstr "main_msg"

2. **Alternative Messages**:
   - Use extended IDs (e.g., ``id_001``, ``id_002``) for alternative messages.
   - Example:

     .. code-block:: po

         msgid "id_001"
         msgstr "alt_1_msg"

         msgid "id_002"
         msgstr "alt_2_msg_with'{variable}'_inside"

3. **Plural Forms**:
   - Use a ``_plural`` suffix for plural forms of the main message and its alternatives.
   - Example:

     .. code-block:: po

         msgid "id_plural"
         msgid_plural "plural_1_of_main_msg"
         msgstr[0] "plural_2_of_main_msg"
         msgstr[1] "plural_3_of_main_msg"

         msgid "id_001_plural"
         msgid_plural "plural_1_of_alt_1_msg"
         msgstr[0] "plural_2_of_alt_1_msg"
         msgstr[1] "plural_3_of_alt_1_msg"

Extended ID Convention for i18next Format
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The extended ID convention involves appending a numerical suffix to the base message ID to represent alternative messages and their plural forms. Here's how it works:

1. **Main Message**:
   - Use the base ID (e.g., ``id``) for the main message.
   - Example:

     .. code-block:: json

        {
            "key1": "value1",
            "key2": "value2",
            "key3_plural": "plural value",
            "key3": "singular value",
            "nested": {
                "key": "nested value"
            }
        }

2. **Alternative Messages**:
   - Use extended IDs (e.g., ``id_001``, ``id_002``) for alternative messages.
   - Example:

     .. code-block:: json

         {
           "id_001": "alt_1_msg",
           "id_002": "alt_2_msg_with'{variable}'_inside"
         }

3. **Plural Forms**:
   - Use a ``_plural`` suffix for plural forms of the main message and its alternatives.
   - Example:

     .. code-block:: json

         {
           "id_plural": {
             "one": "plural_1_of_main_msg",
             "other": "plural_2_of_main_msg"
           },
           "id_001_plural": {
             "one": "plural_1_of_alt_1_msg",
             "other": "plural_2_of_alt_1_msg"
           }
         }

Benefits
^^^^^^^^

- **Clarity**: This convention clearly distinguishes between main messages, alternatives, and their plural forms.
- **Compatibility**: It is compatible with the ``.po`` format used by Babel and the i18next format, allowing seamless integration with existing i18next setups.
- **Automation**: Scripts can be created to automate the conversion process, ensuring consistency across translations.

By following this extended ID convention, you can efficiently manage alternative messages and their plural forms in a format that is both clear and compatible with the i18next framework.
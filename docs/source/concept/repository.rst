Repository Structure
=====================

This document outlines the organization of a translation repository following a structured format for directories and files. This structure ensures that translation files are managed efficiently and consistently across different languages, modules, and packages.


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
-------------------------

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
--------

- **Consistency**: Ensures a consistent structure across different languages, modules, and packages.
- **Scalability**: Facilitates the addition of new languages, modules, and packages.
- **Maintainability**: Simplifies the process of updating and merging translations.

This structure adheres to the GNU gettext standards, promoting a streamlined and efficient translation process.

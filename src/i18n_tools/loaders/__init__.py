"""
Module description and specifications
=====================================

The `loaders` module provides essential file handling operations for the
i18n-tools package. It is designed to manage the loading, saving, and
manipulation of various file formats used in internationalization (i18n)
projects.

**Key Features:**
    - Load and save configuration files in JSON, YAML, and TOML formats.
    - Handle specific `.json`, `.po`, `.pot`, and `.mo` files for translation projects, including
      reading and writing operations.
    - Create and manage compressed archives (tar.gz and gzip) for module
      directories.
    - Ensure safe file extraction paths to prevent directory traversal attacks.
    - Provide utility functions for common file operations such as creating
      directories and checking file existence.

**Translation Repository Structure:**

The `NestedDictionary` structure is used to represent the translation repository,
providing a hierarchical organization of configuration details, paths, domains,
languages, translators, and authors. This structure is essential for managing
internationalization (i18n) projects efficiently.

**Structure Overview:**

- **details**: Contains metadata about the configuration, including:
  - `name`: The name of the configuration.
  - `description`: A brief description of the configuration.

- **paths**: Defines important directory paths used in the i18n project:
  - `root`: The root directory of the project.
  - `repository`: The directory where localization files are stored, typically `locales`.
  - `config`: The directory containing configuration files for i18n tools.
  - `settings`: The settings file name, which can be in `.yaml`, `.json`, or `.toml` format.
  - `backup` : The directory containing compressed archives of repository
  - `modules`: A list of modules involved in the i18n process.

- **domains**: A dictionary to store different translation domains.

- **languages**: Manages language settings:
  - `source`: The source language of the project.
  - `hierarchy`: Defines the hierarchy of languages for fallback purposes.
  - `fallback`: The fallback language to use when translations are missing.

- **translators**: Stores information about translators contributing to the project.

- **authors**: Stores information about the authors of the i18n configuration.

**Organization of Translation Files:**

The translation repository is organized with specific file types to manage translations:

- **.json**: JSON files are used to store configuration settings and sometimes translation strings in a structured format.
- **.po**: Portable Object files contain translations in a human-readable format, often used for editing translations.
- **.mo**: Machine Object files are compiled versions of `.po` files, optimized for fast access by applications.
- **.pot**: Portable Object Template files serve as templates for `.po` files, containing all translatable strings extracted from the source code.

**Directory Structure:**

The `templates` directory within the repository contains these translation files. The structure typically looks like this:

- `locales/`

  - `<language_code>/`

    - `LC_MESSAGES/`

      - `<domain>`.json
      - `<domain>.po`
      - `<domain>.mo`

  - `templates/`

    - `<domain>.pot`

This structure ensures that translations are organized by language and domain, making it easier to manage and update translations for different parts of the application.
"""

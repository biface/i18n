Models Module
=============

The **Models** module defines the core data structures and business logic for **i18n-tools**. It is divided into the following submodules:

- **Repository**: Describes the translation repository structure, based on `StrictNestedDictionary`.
- **Message**: One identifier's translations and metadata, in one language.
- **Book**: The messages of one domain in one language, and the ``FallbackBook`` proxy.
- **Corpus**: The books of one domain across languages.
- **Encyclopaedia**: The corpora of a repository, keyed by module and domain.

.. toctree::
   :maxdepth: 1

   repository
   message
   book
   corpus
   encyclopaedia

Introduction to i18n-tools
==========================

**i18n-tools** is a Python library designed to simplify and extend the management of translation files for applications requiring complex internationalization logic. It introduces a proprietary translation format that addresses specific needs not fully covered by traditional formats like **i18n gettext** or **i18next**.

Purpose
-------

The primary goal of **i18n-tools** is to provide a flexible and powerful way to handle translations, especially in contexts where:

- Messages need to adapt dynamically based on **contextual conditions** (e.g., automata behavior, threshold-based plurals).
- The same components (e.g., alphabets, grammars) produce **different errors or help messages** depending on the system's state.
- Language-independent identifiers are required to ensure consistency across multiple languages.


Key Features
------------

1. **Context-Aware Messages**
   Messages can include **alternatives** to address specific conditions or provide detailed explanations for errors.

2. **Extended Plural Support**
   Unlike traditional plural forms, **i18n-tools** allows plurals to be defined based on **thresholds or data criteria**, enabling more precise and adaptable translations.

3. **No Source Language Dependency**
   The format does not rely on a "source language," though it retains compatibility with this concept to bridge with other formats.

4. **Interoperability**
   While the proprietary format is the core focus, **i18n-tools** aims to maintain equivalence with **i18n gettext** and **i18next** for seamless integration into existing workflows.

Target Audience
---------------

This library is intended for:

- **Developers** building applications with complex internationalization needs (e.g. rule-based systems).
- **Localization teams** requiring fine-grained control over message variations.

Roadmap
-------

- **Version 1.0**: Focus on the proprietary format and core functionality.
- **Version 1.5**: Add support for converting translations to/from **i18next**.
- **Version 2.0**: Introduce **Babel-based** export to classic **i18n gettext** format.

Why Use i18n-tools?
-------------------

If your application requires **dynamic, context-sensitive messages** or **non-standard plural rules**, **i18n-tools** provides the flexibility and control needed to deliver a polished user experience across languages.

For more details, see the :doc:`Overview <index>` or dive into the :doc:`Getting Started <install>` guide.

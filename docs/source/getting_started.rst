Getting Started with i18n-tools
===============================

This guide will help you install **i18n-tools** and run your first translation workflow.

---

Prerequisites
-------------

Before installing **i18n-tools**, ensure you have the following:
- **Python 3.9+** installed on your system.
- **pip** (Python package manager) for installation.

.. note::
   i18n-tools has been tested on several versions of Python but is currently being developed with version **3.10**.

---

Installation
------------

You can install **i18n-tools** using pip:

.. code-block:: bash

   pip install i18n-tools

.. note::
   If you encounter permission issues, try using ``pip install --user i18n-tools`` or a virtual environment.

---

Quick Start
-----------

.. warning::
   This is not presently available !

1. **Initialize a Translation Repository**
   Use the CLI to create a new translation repository:

   .. code-block:: bash

      i18n-tools init --name my_project

   This will generate a directory structure for your translations.

2. **Add a Translation Message**
   Add a message to your repository using the CLI:

   .. code-block:: bash

      i18n-tools add --id welcome_message --text "Welcome to my application!"

3. **Generate Translations**
   Export translations to a supported format (e.g., JSON for i18next):

   .. code-block:: bash

      i18n-tools export --format i18next --output translations.json

---

Next Steps
----------

- Explore the :doc:`Core Concepts <concept/index>` to understand the proprietary format.
- Check out the :doc:`API Reference <api/index>` for programmatic usage.

.. todo::
   Once a CLI/GUI exists (targeted v1.0.0+, DD-30) and the advanced
   configuration guide is written, re-add links to them here.

---

Troubleshooting
----------------

- **Installation Issues**: Ensure your Python environment is correctly set up.
- **Command Not Found**: Verify that the ``i18n-tools`` executable is in your system's PATH.

For more help, open an issue on the project repository.

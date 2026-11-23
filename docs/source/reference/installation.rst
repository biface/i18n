Installation
============

The package is published on PyPI as **pyi18t-tools**.

Prerequisites
-------------

- **Python 3.11** or later. The package is tested on Python 3.11 to 3.14.
- **pip**, or another installer that reads PyPI.

Installation
------------

.. code-block:: bash

   pip install pyi18t-tools

This installs everything needed to load, format and save ``.i18t``
files: the model (``Message``, ``Book``, ``Corpus``, ``Encyclopaedia``),
``formatter.publish()``, and the command line (``validate``, ``info``,
``sync``, ``repl``) with a ``.yaml`` or ``.json`` settings file.

The management of authors and translators (the author and translator
methods of ``Config`` and ``Repository``, the check of a translator API
URL) and a ``.toml`` settings file also need the ``api`` extra:

.. code-block:: bash

   pip install "pyi18t-tools[api]"

Calling one of these methods without the extra raises
``ModuleNotFoundError``, whose message says what needs the extra and
gives this command.

The package is imported as ``i18n_tools``, and its command line is
``i18n-tools``.

.. note::
   Install the package in a virtual environment rather than in the
   Python of the system.

Troubleshooting
---------------

- **Command not found**: check that the ``i18n-tools`` executable, in the
  ``bin`` (or ``Scripts``) directory of the environment, is in your
  ``PATH``.
- **ModuleNotFoundError: ... requires the 'api' extra**: install the
  ``api`` extra.

For more help, open an issue on the
`project repository <https://github.com/biface/i18n/issues>`_.

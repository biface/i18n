Overview
========

i18n-tools is a library of tools for manipulating a specific translation format that extends the logic of internationalization while preserving, as much as possible, the bridges with classic formats like i18n gettext and i18next.

The main features of the i18n-tools format are:

 * There is no source language and translations from that language, although we retain this notion of a source to build the models necessary for other formats.
 * A message can have alternatives that provide a way to have a generic message on a topic of information or to explain an error with specific conditions.
 * A message can have multiple plurals, even if the language standard considers only a limited number. This allows adapting responses based on thresholded measurements.
 * Messages are identified by language-independent identifiers that serve as the same reference point for all translation languages.


.. toctree::
    :numbered: 3
    :maxdepth: 3
    :caption: Documentation content:
    :name: maintoc

    install
    org
    api

Indices and references
======================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

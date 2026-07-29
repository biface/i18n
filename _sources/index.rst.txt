Overview
========

i18n-tools is a library of tools for manipulating a specific translation format that extends the logic of internationalization while preserving, as much as possible, the bridges with classic formats like i18n gettext and i18next.

The main features of the i18n-tools format are:

 * There is no source language and translations from that language, although we retain this notion of a source to build the models necessary for other formats.
 * A message can have alternatives that provide a way to have a generic message on a topic of information or to explain an error with specific conditions.
 * A message can have multiple plurals, even if the language standard considers only a limited number. This allows adapting responses based on thresholded measurements.
 * Messages are identified by language-independent identifiers that serve as the same reference point for all translation languages.

Why a New Format?
-----------------

During the design of a module to manage automata, I needed to organize help and error messages to assist users and explain errors. An automaton is built from multiple components, but the behavior of these components changes depending on the type of automaton. For example, a finite state machine (FSM) uses the same components as a pushdown automaton (PDA) or a linear bounded automaton (LBA), but manipulating components like the alphabet or grammar does not produce the same errors or require the same usage explanations.

After several attempts using the standard i18n approach, I decided to create a translation format that would better suit my needs. This format also provides additional options, such as using plurals based on thresholds or data criteria. This is how I started working on **i18n-tools**.

.. note::
   While developing this format, I aimed to maintain equivalence with existing formats, at least with i18n and i18next, to ensure compatibility and ease of integration.

.. warning::
   - **Version 1.0** focuses on the proprietary format only.
   - **Version 1.5** will implement conversions to/from the i18next format.
   - **Version 2.0** will add support for exporting to the classic i18n gettext format using the Babel library.


.. toctree::
    :numbered: 3
    :maxdepth: 2
    :caption: Documentation content:
    :name: maintoc

    introduction
    getting_started
    concept/index
    api/index
    indices
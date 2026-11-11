Fallback
========

A requested text may be missing in two ways: the language has no
message under the identifier, or the message has no text in the
requested cell. Two independent fallbacks answer these cases. The
language fallback chooses a whole message; the column fallback then
chooses a text inside that message.


Language fallback
-----------------

A language is resolved through a chain of languages, from the most
specific to the least specific:

1. the requested language;
2. its family, for instance ``fr`` for ``fr-CH``, and the regional
   variants declared under it in the repository hierarchy;
3. the terminal fallback of the repository, often the language from
   which new translations are written, with its own declared variants.

A language appears once in the chain, at its first place.
``fallback.resolve()`` computes the chain from the repository settings.

``Corpus.get_book()`` turns the chain into a ``FallbackBook``, keeping
the languages loaded in the corpus. When no repository is given, it
builds the chain from the loaded languages alone: the requested
language, its family, the other languages of that family, then every
other loaded language.

The fallback works **at message level**: ``FallbackBook.get_message()``
walks the chain and the first book that holds the identifier answers
with its whole message. Texts of different languages are never mixed
inside one message. When no book of the chain holds the identifier,
``MessageNotFoundError`` is raised.

Drafts take part in the chain: a translation in progress is trusted to
answer, so a partly translated language still serves the texts it has.

In the example below, the hierarchy declares ``fr-FR`` under ``fr`` and
the terminal fallback is ``en``. A request in ``fr-CH`` walks the chain
``fr-CH``, ``fr``, ``fr-FR``, ``en``; ``fr-FR`` is the first language that
holds the identifier, so its message answers and ``en`` is not consulted.

.. mermaid::

    flowchart LR
        request(["files.missing<br/>requested in fr-CH"])
        frCH["fr-CH<br/>does not hold it"]
        fr["fr<br/>does not hold it"]
        frFR["fr-FR<br/>holds it"]
        en["en<br/>not consulted"]
        answer[["message of fr-FR<br/>all its declensions and segments"]]
        request --> frCH --> fr --> frFR
        frFR -.-> en
        frFR ==> answer
        classDef miss stroke-dasharray: 5 5
        classDef hit stroke-width: 3px
        classDef idle opacity: 0.5
        class frCH,fr miss
        class frFR,answer hit
        class en idle


Column fallback
---------------

Inside the message chosen by the language fallback, a cell
``(variant, segment)`` may be empty. Its text is found in four steps:

1. the cell itself, ``(variant, segment)``;
2. the principal in the same segment, ``(0, segment)``;
3. the same variant in the singular, ``(variant, 0)``;
4. the principal singular, ``(0, 0)``.

The first non-empty text is used. The principal singular is the last
resort: ``mark_complete()`` refuses a message whose principal singular is
empty.

.. mermaid::

    flowchart TD
        cell["(variant, segment)"]
        same_segment["(0, segment)<br/>principal, same segment"]
        singular["(variant, 0)<br/>same variant, singular"]
        principal["(0, 0)<br/>principal singular"]
        text(["text used"])
        cell -- empty --> same_segment
        same_segment -- empty --> singular
        singular -- empty --> principal
        cell -- text --> text
        same_segment -- text --> text
        singular -- text --> text
        principal --> text

With the message below, the cell ``(1, 1)`` is empty: its text comes
from step 2, ``(0, 1)``, and reads "{n} files are missing.".

.. list-table::
   :header-rows: 1
   :stub-columns: 1
   :widths: 20 40 40

   * -
     - variant 0 (principal)
     - variant 1
   * - segment 0
     - ``File {name} is missing.``
     - ``File {name} is missing from {repository}.``
   * - segment 1
     - ``{n} files are missing.``
     - *(empty)*

``formatter.publish()`` applies the column fallback before it substitutes
the placeholders. The cross-language check of rule 2 reads cells the
same way (see :doc:`integrity`).


Two fallbacks, one order
------------------------

The two fallbacks are independent and apply in a fixed order: first the
language fallback chooses the message, then the column fallback chooses
the text inside it.

.. mermaid::

    flowchart LR
        request(["identifier<br/>language<br/>(variant, segment)"])
        language["language fallback<br/>FallbackBook.get_message()"]
        message[["message"]]
        column["column fallback"]
        text(["text"])
        publish["placeholders substituted<br/>publish()"]
        request --> language --> message --> column --> text --> publish

A cell left empty in the ``fr-CH`` message is therefore filled from
another cell of that message, never from ``fr-FR``.

Integrity and Consistency
=========================

A translation is written over time, by several people, in several
languages. Two questions follow: when is a message finished, and how do
we notice that a finished message has lost a text, or no longer matches
the same message in another language? This page explains the answers:
a completion status, content counters recorded at chosen moments, two
consistency rules, and checks at three levels.

The file-level rules are specified in :doc:`/reference/format`.


Draft and complete
------------------

Every message has a status. A new message is a **draft**: its texts and
its structure may change freely. When a translation is finished, the
message is marked **complete**.

.. list-table::
   :header-rows: 1
   :widths: 24 24 52

   * - Transition
     - Method
     - Condition
   * - draft → complete
     - ``Message.mark_complete()``
     - The principal singular is not empty, and every declension has the
       same number of segments (rule 1, below). Otherwise
       ``MessageError`` is raised and the status does not change.
   * - complete → draft
     - ``Message.reopen()``
     - None. The recorded counters are kept.

A complete message is **locked**: every change to its texts or its
structure (principal, alternatives, segments, ``switch()``,
``toggle()``)
raises ``MessageError``. Its context, locations, flags, comments and
other metadata stay editable, since they take no part in the integrity
checks. To change a text, reopen the message, edit it, then mark it
complete again.

.. code-block:: python

    from i18n_tools.models import Message

    message = Message(
        "files.missing",
        "File {name} is missing.",
        plurals=["{n} files are missing."],
        alternatives=[["File {name} is missing from {repository}.", ""]],
    )
    message.status            # "draft"
    message.mark_complete()
    message.remove_variant(1) # MessageError: the message is complete
    message.reopen()
    message.remove_variant(1) # accepted: the message is a draft again


Content counters
----------------

The content counters of a message describe the shape of its content:
the number of declensions (the principal and its alternatives), the
number of segments of each, the placeholder names of each text, and a
fill mask telling which texts are filled. They are a ``ContentCounters``
value, stored in the entry of the message as ``count`` and ``fill_mask``
(see :doc:`/reference/format`).

A message holds two sets of counters:

- the **observed** counters, computed from the content each time they
  are read (``Message.observed``);
- the **recorded** counters, taken at the last validation point and
  kept apart from the content (``Message.recorded``), or read from the
  file the message was loaded from. A message never validated has none.

Observed counters always agree with the content, so they cannot reveal
that a text was lost. Recorded counters can: they remember the content
as it was when it was last declared sound.

The recorded counters change only at a **validation point**:

- ``Message.mark_complete()`` records the counters of the content it
  declares final;
- saving a book records the counters of each draft, once the file is
  written (``Message.record()``, which a complete message refuses).

Loading a file sets the recorded counters from the file. No other
operation changes them.


Divergence
^^^^^^^^^^

A message **diverges** when its recorded counters differ from its
observed ones (``Message.has_divergence``). A complete message without
recorded counters cannot be verified and is treated as diverging. The
difference names the texts lost or added, by ``(declension, segment)``:
``text (1, 0) lost``.

What a divergence means depends on the status:

.. list-table::
   :header-rows: 1
   :widths: 28 36 36

   * -
     - draft
     - complete
   * - Meaning
     - Expected: the translation is in progress.
     - An integrity defect: a finished text changed.
   * - Loading the file
     - Accepted silently.
     - The message is **broken**: its file was changed outside the
       package, or data were lost. It is read as a draft, with a warning
       when its book is complete and an information when its book is a
       draft.
   * - ``Book.check()``
     - Information.
     - Error.
   * - Saving the book
     - Accepted; the draft's counters are recorded again.
     - Refused with ``MessageError`` before anything is written, so that
       a loss never replaces the last sound state.

For instance, a complete message whose alternative singular was emptied
by hand, in a book where every message is complete, gives on inspection:

.. code-block:: text

    warning  -  files.missing: complete message broken (the content differs
    from the record: text (1, 0) lost; tokens of text (1, 0): recorded
    [name, repository], observed []): read as draft, and its Book with it

A divergence on a complete message is resolved by accepting the current
content explicitly: ``reopen()``, then ``mark_complete()``, which records
it as the new reference.


Consistency rules
-----------------

Rule 1: within a message
^^^^^^^^^^^^^^^^^^^^^^^^

Every declension of a message has as many segments as the principal.
An absent text is the empty string, or a text made only of whitespace; it
is resolved at formatting time by the column fallback (see
:doc:`fallback`). Within one message, two texts may use different
placeholders: an alternative may name what the principal does not.

A draft may break rule 1 while it is edited; the file then holds empty
strings where a declension is shorter. ``mark_complete()`` refuses a
message that breaks it, and the lock keeps it true for every complete
message.

Rule 2: across languages
^^^^^^^^^^^^^^^^^^^^^^^^

The number of segments is a property of the message, not of the
language: plural segments follow thresholds chosen by the application,
not the grammar of each language. So the same identifier must have the
same shape in every language of a domain:

- the same number of declensions and of segments;
- at each address ``(declension, segment)``, the same set of placeholder
  names. The order of the placeholders, their repetitions and their
  format specifications do not matter: ``{n:d}`` and ``{n}`` are the same
  placeholder.

The text at an address is read after the column fallback, as it would be
published. In the example below, the French alternative 1 is empty and
falls back to the principal, which does not name ``{repository}``:

.. code-block:: text

    en-US  (1, 0)  "File {name} is missing from {repository}."
    fr-FR  (1, 0)  ""  ->  "Le fichier {name} est absent."

    error  -  files.missing: tokens of cell (variant 1, segment 0) differ
    across languages: en-US ['name', 'repository'], fr-FR ['name']

Rule 2 applies only between complete messages: completion is what
declares the obligation. Drafts are left out. Since the language
fallback answers with whole messages (see :doc:`fallback`), comparing
the messages that the books of the domain hold under the same identifier
is enough.


Levels of checks
----------------

Each level checks what it can see. All of them report **findings**:
a severity (error, warning or information), the place (a message
identifier, or ``root`` for the file itself), a message and, where it
applies, the language.

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Level
     - What is checked
   * - File inspection
     - One ``.i18t`` file against the format: entries, metadata types,
       language and domain, texts, status and counters (see
       :doc:`/reference/format`). ``loader.inspect_book_file()`` lists
       the findings without loading. Loading a book stops on an error
       and issues each warning as an ``I18nToolsWarning``.
   * - ``Book.check()``
     - The messages of one book in memory: an empty principal singular,
       a divergence. Information for a draft, error for a complete
       message.
   * - ``Corpus.check()``
     - The books of one domain across languages: rule 2 between complete
       messages.
   * - ``core.inspect_corpus()``
     - A module and domain of a repository: for each configured
       language, a missing directory or file, then the file inspection;
       then rule 2 on the files that load.

The ``i18n-tools validate`` command runs the file inspection on one
file, or ``core.inspect_corpus()`` on a module and domain, prints every
finding and exits with an error status when one of them is an error.
See :doc:`/reference/cli` and :doc:`/guides/cli`.

.. todo::

   - Decide which level checks what (subsidiarity), and the severity of
     a complete message that diverges at each level.
   - Audit before ``mark_complete()``: locations outside the content,
     rule 1 on hand-built complete messages.

The .i18t Format
================

A ``.i18t`` file holds the messages of one domain in one language: it is
the file of a Book. This page is the normative specification of its
content, format version **1.0.0**, so that a file can be read and written
without the Python package. Format 1.0.0 does not change before release
0.40.0; after that, a new version of the format can only add keys, never
remove a key or change its meaning.

The key words MUST, MUST NOT, SHOULD, SHOULD NOT and MAY are to be read as
described in :rfc:`2119`. A rule on the content of a file uses MUST when a
reader treats its violation as an error, SHOULD when it gives a warning
(see `Reading a file`_). A rule on writers says what a conforming writer
produces; a reader may still accept a file that does not follow it.

For the ideas behind statuses and counters, see
:doc:`/concept/integrity`; for the place of a file in a repository, see
:doc:`/concept/repository`.


File name and encoding
----------------------

A Book file is named ``<domain>.json.i18t`` or ``<domain>.yaml.i18t``.
The middle suffix gives the encoding; both encodings are normative and
carry the same content. No other name is a Book name: a reader MUST
refuse ``<domain>.i18t`` (no encoding), ``<domain>.yml.i18t`` and any
other suffix, with an error that states the two expected names. A file
has one name only.

The file is encoded in UTF-8. Its content MUST parse as JSON or YAML, as
its name says, and MUST be a mapping.

A writer writes the keys in the order of this page: ``metadata`` first,
then the message entries in the order the Book holds them, and the keys
of each mapping in the order of its table. A YAML writer keeps this order
(it does not sort the keys) and writes non-ASCII characters as they are.
The indentation is not part of the format.

All the content is described on the JSON data model (mappings with string
keys, lists, strings, integers, booleans, ``null``); a YAML file uses
the same model.


JSON Schema
-----------

The structure of a file, as a conforming writer produces it, is published
as a JSON Schema (draft 2020-12):

- identifier and address:
  ``https://pyi18t-tools.readthedocs.io/en/stable/schemas/i18t-1.0.0.schema.json``;
- in the Python package: ``i18n_tools/schemas/i18t-1.0.0.schema.json``.

The schema is strict: every key a writer writes is required, and no other
key is allowed. It describes what a writer produces, not everything a
reader accepts: the tolerances of `Reading a file`_ are not in it. It
does not express the rules that relate several values: the equal number of
segments in every declension, the counters against the content, the
language and the domain against the place of the file. These rules are
given in the sections below.

The complete schema is at the end of this page (`The schema`_).


Top-level structure
-------------------

The top-level mapping holds three kinds of keys:

``metadata``
    The metadata of the Book (see `Root metadata`_). Required.

``.i18n_tools``
    Reserved for later use. A reader ignores it; a writer MUST NOT write
    it.

any other key
    A message entry (see `Message entries`_). The key is the identifier
    of the message.

An identifier is a string chosen by the developer, readable
(``error.network.timeout``) or opaque (``Q100200020``), and independent of
the language: the same identifier designates the same message in every
language of the domain. ``metadata`` and ``.i18n_tools`` therefore cannot
be identifiers.


Root metadata
-------------

.. list-table::
   :header-rows: 1
   :widths: 20 22 58

   * - Key
     - Type
     - Meaning
   * - ``format_version``
     - string, semantic version
     - Version of the format the file follows. See `Versions`_.
   * - ``version``
     - string, semantic version
     - Version of the translation held by the Book. See `Versions`_.
   * - ``language``
     - string
     - Language tag of the Book. See `Language and domain`_.
   * - ``domain``
     - string
     - Domain of the Book. See `Language and domain`_.
   * - ``gettext``
     - mapping
     - Header fields shared with gettext. See `gettext fields`_.
   * - ``rules``
     - mapping
     - Plural rules of the Book. See `Rules`_.
   * - ``count``
     - mapping
     - Integrity counters of the Book. See `Book counters`_.
   * - ``statistics``
     - mapping
     - Statistics of the Book. See `Book statistics`_.


Versions
^^^^^^^^

``format_version`` and ``version`` are semantic versions in their strict
form, ``MAJOR.MINOR.PATCH``: three integers without leading zeros, with
neither pre-release nor build part (``1.0.0``, ``0.0.1``; not ``1.0``,
``01.0.0`` or ``0.0.1-rc.1``).

``format_version``
    A writer of this specification writes ``"1.0.0"``. A reader MUST
    refuse a file without ``format_version``, with a value that is not a
    strict semantic version, or with a ``MAJOR`` it does not know. For
    this specification, the only known ``MAJOR`` is ``1``.

``version``
    The version of the translation, carried by the Book only: a message
    entry has no version. A new Book starts at ``"0.0.1"``. A reader
    reads an absent ``version`` as ``"0.0.1"``; a value that is not a
    strict semantic version is an error.


Language and domain
^^^^^^^^^^^^^^^^^^^

``language`` is a language tag; ``domain`` is the domain name of the
file. A writer writes the language and the domain under which the Book is
held, normalised (``fr-FR``). They let a file read alone, or a Book taken
from an archive, say what it holds.

When the reader knows the expected language and domain from the place of
the file (``<language>/LC_MESSAGES/<domain>.<encoding>.i18t``), it
compares them, after normalisation of the language tags: ``fr-fr`` read
from a ``fr-FR`` directory is accepted, ``fr-CA`` is an error, and so is
a domain other than the name of the file.


gettext fields
^^^^^^^^^^^^^^

The ``gettext`` mapping groups the header fields used by gettext, and by
the Python package itself. Every value is a string; ``""`` means that the
value is not known. No placeholder value is written.

.. list-table::
   :header-rows: 1
   :widths: 26 74

   * - Key
     - Meaning
   * - ``project_id_version``
     - Project name and version (``Project-Id-Version``).
   * - ``report_msgid_bugs_to``
     - Address for reports on the messages (``Report-Msgid-Bugs-To``).
   * - ``pot_creation_date``
     - Creation date of the messages (``POT-Creation-Date``).
   * - ``po_revision_date``
     - Date of the last write of the file (``PO-Revision-Date``).
   * - ``last_translator``
     - Last translator (``Last-Translator``).
   * - ``language_team``
     - Team in charge of the language (``Language-Team``).
   * - ``header_comment``
     - Comment about the whole file.

A writer writes the seven keys, and updates ``po_revision_date`` at each
write of the file. The form of the values, the dates included, is not
specified by format 1.0.0: it is set with the conversion to gettext. Until
then, a reader does not check the ``gettext`` mapping: it keeps its values
unchanged, and reads an absent mapping or an absent key as ``""``.

``Plural-Forms`` and ``Content-Type`` are not stored: they follow from the
language and from the UTF-8 encoding.


Rules
^^^^^

``rules`` holds the plural rules of the Book. An entry has its own
``rules`` (see `Entry metadata`_), which override those of the Book key by
key: a key absent from the entry is taken from the Book. A writer writes
``rules``, as ``{}`` when there is none; a reader reads an absent
``rules`` as ``{}``.

The content of ``rules`` is not specified by format 1.0.0. A reader of
this specification keeps it, and writes it back, unchanged.


Book counters
^^^^^^^^^^^^^

``count`` records the shape of the Book, from its entries. Every value is
an integer of at least 0. The counters of an entry are described in
`Recorded counters`_.

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Key
     - Value
   * - ``messages``
     - Number of entries.
   * - ``draft``
     - Number of entries whose status is ``draft``.
   * - ``complete``
     - Number of entries whose status is ``complete``.
   * - ``declensions``
     - Sum of the ``declensions`` counters of the entries.
   * - ``alternatives``
     - Sum of the ``alternatives`` counters of the entries.
   * - ``singulars``
     - Sum of the ``singulars`` counters of the entries.
   * - ``plurals``
     - Sum of the ``plurals`` counters of the entries.
   * - ``segments``
     - Number of texts: sum over the entries of ``segments.principal`` and
       of every ``segments.alternatives`` value.
   * - ``filled``
     - Number of ``true`` values in the fill masks of the entries.
   * - ``empty``
     - Number of ``false`` values in the fill masks of the entries.

A writer computes ``count`` at each write. A reader checks:

1. ``messages`` equals the number of entries;
2. ``draft + complete == messages``;
3. ``declensions``, ``alternatives``, ``singulars`` and ``plurals`` are
   the sums over the entries;
4. ``segments`` is the sum of the segments of the entries;
5. ``filled + empty == segments``, and ``filled`` is the number of
   ``true`` values in the fill masks;
6. ``singulars == declensions``.

A difference SHOULD NOT occur: it is a warning.


Book statistics
^^^^^^^^^^^^^^^

``statistics`` describes the Book. A writer computes it at each write; a
reader does not compare it with the content.

.. list-table::
   :header-rows: 1
   :widths: 30 20 50

   * - Key
     - Type
     - Value
   * - ``words``
     - integer
     - Sum of the ``words`` statistics of the entries.
   * - ``characters``
     - integer
     - Sum of the ``characters`` statistics of the entries.
   * - ``messages_with_alternatives``
     - integer
     - Number of entries with at least one alternative.
   * - ``messages_with_plurals``
     - integer
     - Number of entries whose principal has more than one segment.
   * - ``messages_with_rules``
     - integer
     - Number of entries whose ``rules`` is not empty.
   * - ``locations``
     - integer
     - Number of locations over every entry.
   * - ``flags``
     - mapping of string to integer
     - For each flag, the number of entries that carry it.
   * - ``tokens``
     - list of strings
     - The distinct token names of the Book, sorted.


Message entries
---------------

An entry is a mapping with two keys, both required:

``messages``
    The content of the message (see `Content`_).

``metadata``
    The metadata of the message (see `Entry metadata`_).

The content of the entry ``files.missing``, whose metadata is shown in
`Recorded counters`_ and in the `Complete example`_:

.. code-block:: json

    "messages": {
        "principal": ["File {name} is missing.", "{n} files are missing."],
        "alternatives": [["File {name} is missing from {repository}.", ""]]
    }


Content
^^^^^^^

The content has two axes: the **declensions** (the wordings of the
message) and the **segments** (its singular and plural forms).

``principal``
    Declension 0, the principal: a list of at least one string.

``alternatives``
    The alternatives: a list, possibly empty, of lists of strings.
    Declension ``k`` (``k`` of at least 1) is ``alternatives[k - 1]``.

In each declension, segment 0 is the singular and segments 1 and above are
the plurals. Their number is free: it is not bound to the plural
categories of the language.

Every alternative MUST have as many segments as the principal. A text
missing in a declension is written ``""``; a declension never stops
short.

On the entry above:

.. list-table::
   :header-rows: 1
   :widths: 22 26 52

   * - Address
     - Path
     - Text
   * - ``(0, 0)``
     - ``principal[0]``
     - ``File {name} is missing.``
   * - ``(0, 1)``
     - ``principal[1]``
     - ``{n} files are missing.``
   * - ``(1, 0)``
     - ``alternatives[0][0]``
     - ``File {name} is missing from {repository}.``
   * - ``(1, 1)``
     - ``alternatives[0][1]``
     - ``""`` (absent)

The meaning of the texts is in `Interpreting the content`_.


Entry metadata
^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 18 24 18 40

   * - Key
     - Type
     - Absent on read
     - Meaning
   * - ``context``
     - string
     - ``""``
     - Context that distinguishes messages with the same text (gettext
       ``msgctxt``). ``""`` when there is none.
   * - ``locations``
     - list of locations
     - ``[]``
     - Places in source code that use the message. See `Locations`_.
   * - ``flags``
     - list of strings
     - ``[]``
     - Flags such as ``python-format``.
   * - ``user_comments``
     - list of strings
     - ``[]``
     - Comments written by translators.
   * - ``auto_comments``
     - list of strings
     - ``[]``
     - Comments extracted from source code.
   * - ``status``
     - ``"draft"`` or ``"complete"``
     - ``"draft"``
     - See `Status`_.
   * - ``rules``
     - mapping
     - ``{}``
     - Plural rules of the message, over those of the Book. See `Rules`_.
   * - ``count``
     - mapping
     - no record
     - Recorded counters. See `Recorded counters`_.
   * - ``fill_mask``
     - mapping
     - no record
     - Recorded fill state. See `Recorded counters`_.
   * - ``statistics``
     - mapping
     - not computed
     - ``words`` and ``characters`` of the message. See
       `Entry statistics`_.

A writer writes every key of the table. A reader reads an absent key as
the value of the third column.


Locations
^^^^^^^^^

A location is a mapping with four keys, all present:

``file``
    The source file, a non-empty string.

``line``
    The line, an integer of at least 1.

``declension``, ``segment``
    The text that the source code asks for at that place: an integer of
    at least 0, or ``null`` when the coordinate is not fixed there.

.. code-block:: json

    "locations": [
        {"file": "src/app/sync.py", "line": 42, "declension": null, "segment": null},
        {"file": "src/app/sync.py", "line": 57, "declension": 1, "segment": 0}
    ]

A coordinate SHOULD designate a text of the message: a declension or a
segment beyond the content is a warning.


Status
^^^^^^

``draft``
    The message is being translated. Its content may change.

``complete``
    The translation is finished and checked. Its content does not change
    until the message is reopened.

A reader reads a value other than ``"draft"`` or ``"complete"`` as
``draft``, with a warning. An entry without ``status`` is read as
``draft``, without a warning; this tolerance is deprecated.


Recorded counters
^^^^^^^^^^^^^^^^^

``count`` and ``fill_mask`` record the shape and the fill state of the
content at a validation point: when the message is marked complete, and,
for a draft, at each write. They form one record. Comparing the record
with the content shows the texts lost or added since: a **divergence**.

``count``:

.. list-table::
   :header-rows: 1
   :widths: 18 30 52

   * - Key
     - Type
     - Value
   * - ``declensions``
     - integer, at least 1
     - Number of declensions, the principal included.
   * - ``alternatives``
     - integer, at least 0
     - Number of alternatives.
   * - ``singulars``
     - integer, at least 1
     - Number of singulars: one per declension.
   * - ``plurals``
     - integer, at least 0
     - Number of plural segments over every declension.
   * - ``segments``
     - mapping
     - ``principal``: the number of segments of the principal;
       ``alternatives``: the list of the numbers of segments of each
       alternative.
   * - ``tokens``
     - mapping
     - The token names of each text, in the shape of the content:
       ``principal`` is a list with one list of names per segment,
       ``alternatives`` a list with one such list per alternative. The
       names of one text are distinct and sorted.

``fill_mask`` has the shape of the content: ``principal`` is a list of
booleans, ``alternatives`` a list of lists of booleans. A value is
``true`` when the text at that address is filled (see
`Interpreting the content`_).

On the entry of `Message entries`_:

.. code-block:: json

    "count": {
        "declensions": 2,
        "alternatives": 1,
        "singulars": 2,
        "plurals": 2,
        "segments": {"principal": 2, "alternatives": [2]},
        "tokens": {
            "principal": [["name"], ["n"]],
            "alternatives": [[["name", "repository"], []]]
        }
    },
    "fill_mask": {"principal": [true, true], "alternatives": [[true, false]]}

A record is **well formed** when:

1. ``singulars == declensions == 1 + alternatives``;
2. ``segments.alternatives`` has ``alternatives`` values;
3. each ``segments.alternatives[k]`` equals ``segments.principal``;
4. ``plurals == (segments.principal - 1) + Σ segments.alternatives -
   alternatives``;
5. ``tokens`` and ``fill_mask`` have the shape given by ``segments``.

What a reader reports depends on the status:

.. list-table::
   :header-rows: 1
   :widths: 46 27 27

   * - Case
     - ``complete``
     - ``draft``
   * - Record not well formed
     - error
     - warning; the record is ignored
   * - Record absent (``count`` or ``fill_mask`` missing)
     - warning
     - accepted
   * - Record that differs from the content (divergence)
     - warning, naming the texts lost or added
     - information
   * - Principal singular not filled
     - warning
     - information

A ``complete`` message that gives one of these warnings has lost its
guarantee: a reader loads it, and it SHOULD NOT be written back as
``complete``.


Entry statistics
^^^^^^^^^^^^^^^^

``statistics`` describes the content of the message, over every text of
every declension:

``words``
    The number of words, a word being a run of characters without
    whitespace (Python ``len(text.split())``).

``characters``
    The number of characters, counted as Unicode code points
    (Python ``len(text)``).

Tokens count as they are written. On the entry of `Message entries`_:
``words`` is ``4 + 4 + 6 + 0 = 14`` and ``characters`` is
``23 + 22 + 41 + 0 = 86``. A writer computes ``statistics`` at each
write; a reader does not compare it with the content.


Interpreting the content
------------------------

These rules belong to the format: every program that reads the texts of a
file gives them this meaning.

Address
    A text is addressed by ``(declension, segment)``, in this order.

Absent text
    A text is **absent** when it is ``""`` or made only of whitespace
    (``" "``, ``"\n"``); otherwise it is **filled**. An absent text is not
    a translation: its ``fill_mask`` value is ``false``.

Tokens
    A text uses the replacement fields of Python's ``str.format``. A
    token is a field with a name (``{name}``, ``{n:d}``); its name is the
    field name, without conversion or format specification: ``{n:d}``
    and ``{n}`` are the same token ``n``. Doubled braces (``{{``, ``}}``)
    are literal braces, not tokens. Values are passed by name: a
    positional field (``{}``, ``{0}``) SHOULD NOT be used, and is a
    warning.

Column fallback
    When the text requested at ``(d, s)`` is absent, a program takes the
    first filled text of ``(d, s)``, ``(0, s)``, ``(d, 0)``, ``(0, 0)``.
    An address outside the message is an error, not a fallback.

Segment of a number
    A program chooses the segment of a number through the plural rules of
    the entry and of the Book (see `Rules`_). How a number selects a
    segment is not specified by format 1.0.0.

The fallback between the languages of a domain is not part of a file: see
:doc:`/concept/fallback`.


Reading a file
--------------

A reader classifies what it finds in three severities:

error
    The file breaks a MUST rule. A reader MUST NOT load it.

warning
    The file breaks a SHOULD rule, or carries a status or counters that
    cannot be trusted. A reader loads the file and SHOULD report the
    warning.

information
    The file is valid; the finding describes it, for instance a draft
    whose content changed since its counters were recorded. A reader MAY
    report it.

.. list-table::
   :header-rows: 1
   :widths: 64 36

   * - Finding
     - Severity
   * - Name other than ``<domain>.json.i18t`` or ``<domain>.yaml.i18t``
     - error
   * - Content that does not parse, or that is not a mapping
     - error
   * - ``metadata`` absent or not a mapping
     - error
   * - ``format_version`` absent, not a strict semantic version, or of an
       unknown ``MAJOR``
     - error
   * - ``language`` or ``domain`` absent
     - error
   * - ``version`` not a strict semantic version
     - error
   * - ``version`` absent
     - read as ``"0.0.1"``
   * - ``language`` or ``domain`` other than the place of the file
     - error
   * - Entry that is not a mapping, without ``messages`` or without
       ``metadata``
     - error
   * - ``principal`` absent or empty, ``alternatives`` absent
     - error
   * - Alternative whose number of segments differs from the principal's
     - error
   * - Known key whose value does not have its type, ``gettext`` excepted
     - error
   * - ``count`` absent at the root, or Book counters that differ from
       the entries
     - warning; recomputed at the next write
   * - ``statistics`` absent at the root
     - none; recomputed at the next write
   * - ``gettext`` absent, a key of it absent, or any value of it
     - none; an absent value is read as ``""``, the others are kept
   * - Unknown key at the root or in the root metadata
     - warning; the key is kept and written back
   * - Unknown key in an entry or in its metadata
     - warning; the key is ignored
   * - Location beyond the content
     - warning
   * - Positional token
     - warning
   * - Invalid ``status``
     - warning; read as ``draft``
   * - Recorded counters of an entry
     - see `Recorded counters`_
   * - ``.i18n_tools``
     - ignored

These checks concern one file. Checks that compare the same message
across the languages of a domain are described in
:doc:`/concept/integrity`.


Complete example
----------------

A file ``errors.json.i18t`` for the language ``en-US``: one complete
message with two declensions of two segments, and one draft message with
three segments and no alternative.

.. literalinclude:: ../../../tests/mock/format/1.0.0/valid/errors.json.i18t
   :language: json

The same file in YAML, ``errors.yaml.i18t``:

.. literalinclude:: ../../../tests/mock/format/1.0.0/valid/errors.yaml.i18t
   :language: yaml

An empty Book, here ``messages.json.i18t`` for ``fr-FR``, is a root with
its complete metadata and no entry; ``{}`` is not a Book:

.. literalinclude:: ../../../tests/mock/format/1.0.0/valid/messages.json.i18t
   :language: json


The schema
----------

.. literalinclude:: ../../../src/i18n_tools/schemas/i18t-1.0.0.schema.json
   :language: json

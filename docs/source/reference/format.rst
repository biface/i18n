The .i18t Format
================

A ``.i18t`` file holds the messages of one domain in one language. This
page specifies its content so that it can be read and written without the
Python package. It describes the format as this release reads and writes
it; the format is frozen at version 1.0.0 and may still change until then.

The key words MUST, MUST NOT, SHOULD and MAY are to be read as described
in :rfc:`2119`. A rule on the content of a file uses MUST when a reader
treats its violation as an error, SHOULD when it gives a warning (see
`Reading a file`_). A rule on writers says what a conforming writer
produces; a reader may still accept a file that does not follow it.

For the ideas behind statuses and counters, see
:doc:`/concept/integrity`; for the place of a file in a repository, see
:doc:`/concept/repository`.

.. todo::

   Still to specify before the format is frozen:

   - meaning of the entry ``version`` field and how a reader handles a
     newer one;
   - formatting semantics that belong to the format contract: column
     fallback, plural row resolution, placeholder syntax;
   - purpose of the reserved ``.i18n_tools`` key;
   - JSON Schema: decide, then publish it and test it against the
     fixtures.


File name and encoding
----------------------

A file is named ``<domain>.<encoding>.i18t``, where ``<encoding>`` is
``json`` or ``yaml``. Both encodings are normative and carry the same
content.

A reader decides the encoding from the name: a name ending in
``.yaml.i18t`` is YAML, any other name is JSON.

The content MUST be a mapping. A content that cannot be parsed, or that
is not a mapping, is an error.


Top-level structure
-------------------

The top-level mapping holds three kinds of keys:

``metadata``
    The root metadata of the file (see `Root metadata`_). Optional for a
    reader; a writer writes it.

``.i18n_tools``
    Reserved. A reader ignores it.

any other key
    A message entry. The key is the message identifier.

An identifier is a string that does not depend on the language: the same
identifier designates the same message in every language of the domain.
``metadata`` and ``.i18n_tools`` therefore cannot be used as
identifiers.


Message entries
---------------

An entry is a mapping with two keys:

``messages``
    The message matrix. Required: an entry without it is an error.

``metadata``
    The entry metadata (see `Entry metadata`_). Optional for a reader,
    where an absent value reads as an empty mapping. If present, it MUST
    be a mapping.


The message matrix
^^^^^^^^^^^^^^^^^^

The matrix is a list of rows; each row is a list of strings.

- Each **column** is a declension. Column 0 holds the principal, columns
  1 and above hold the variants of the message. A text is addressed as
  ``(variant, segment)``, variant 0 being the principal.
- Each **row** is a segment. Row 0 is the singular, rows 1 and above are
  plural segments. Their number is free: it is not bound to the plural
  categories of the language.
- The empty string marks an absent text. It is resolved at formatting
  time by the column fallback (see :doc:`/concept/fallback`).

The matrix MUST be a rectangle: at least one row, every row of the same
length, and that length at least 1. Every cell MUST be a string.

.. code-block:: json

    [
        ["File {name} is missing.", "File {name} is missing from {repository}."],
        ["{n} files are missing.", ""]
    ]

This matrix has two declensions and two segments. The plural segment has
no text for variant 1.


Legacy flat form
^^^^^^^^^^^^^^^^

An entry MAY be the matrix alone, without the ``messages`` and
``metadata`` keys. This form comes from earlier releases. A reader
accepts it, with empty entry metadata; a writer MUST NOT produce it.


Entry metadata
--------------

.. list-table::
   :header-rows: 1
   :widths: 18 22 60

   * - Key
     - Type
     - Meaning
   * - ``version``
     - string
     - Version of the writer of the entry.
   * - ``language``
     - string
     - Language tag of the message. See `Languages and domain`_.
   * - ``context``
     - string
     - Context that distinguishes messages with the same text (gettext
       ``msgctxt``). Empty when there is none.
   * - ``locations``
     - list of locations
     - Places in source code that use the message. See `Locations`_.
   * - ``flags``
     - list of strings
     - Flags such as ``python-format`` or ``fuzzy``.
   * - ``user_comments``
     - list of strings
     - Comments written by translators.
   * - ``auto_comments``
     - list of strings
     - Comments extracted from source code.
   * - ``status``
     - ``"draft"`` or ``"complete"``
     - See `Status`_.
   * - ``singular_count``
     - integer, at least 1
     - Number of declensions (columns). See `Content counters`_.
   * - ``segment_count``
     - integer, at least 1
     - Number of segments (rows). See `Content counters`_.
   * - ``fill_mask``
     - list of lists of booleans
     - Which texts are filled. See `Content counters`_.
   * - ``plural_counts``
     - any
     - Earlier counter, replaced by ``segment_count`` and ``fill_mask``.
       Read and ignored; a writer MUST NOT produce it.

Every key is optional for a reader. A value of a known key that does not
have its type is an error. An unknown key SHOULD NOT be present: it is a
warning, and the reader ignores it.

A writer writes every key of the table except ``plural_counts``.


Locations
^^^^^^^^^

A location is one of:

- ``[file, line]``: the source code at that place uses the whole message;
- ``[file, line, variant, segment]``: the source code asks for that text
  of the message. A coordinate MAY be ``null`` when it is not fixed at
  that place.

``file`` MUST be a non-empty string, ``line`` an integer of at least 1,
and each coordinate ``null`` or an integer of at least 0. A writer uses
the two-item form when both coordinates are ``null``.

.. code-block:: json

    "locations": [
        ["src/app/sync.py", 42],
        ["src/app/sync.py", 57, 1, 0]
    ]


Status
^^^^^^

``draft``
    The message is being translated. Its content may change.

``complete``
    The translation is finished and checked. Its content is not expected
    to change until it is reopened.

A writer MUST write ``status``. A reader reads any value other than
``"draft"`` or ``"complete"`` as ``draft``, with a warning. An entry
without ``status`` is read as ``draft`` without a warning; this tolerance
keeps older files readable and is deprecated.


Content counters
^^^^^^^^^^^^^^^^

The counters record the shape and the fill state of the matrix:

- ``singular_count``: the number of columns;
- ``segment_count``: the number of rows;
- ``fill_mask``: a rectangle of ``segment_count`` rows and
  ``singular_count`` columns, in matrix orientation:
  ``fill_mask[segment][variant]`` is ``true`` when that text is not
  empty.

The three keys form one record: it is present only when all three are.

For a ``complete`` entry, the record holds the counters taken when the
message was marked complete. For a ``draft`` entry, it holds the counters
of the content at the time of writing. Comparing the record with the
matrix shows texts lost or added since: this is the divergence of the
message.

.. code-block:: json

    "singular_count": 2,
    "segment_count": 2,
    "fill_mask": [[true, true], [true, false]]

What a reader reports depends on the status:

.. list-table::
   :header-rows: 1
   :widths: 46 27 27

   * - Case
     - ``complete``
     - ``draft``
   * - Malformed record: a counter that is not an integer of at least 1,
       a mask that is not a rectangle of booleans, a mask whose shape
       disagrees with the counters
     - error, one per defect
     - warning; the record is ignored
   * - Missing record (one of the three keys absent)
     - warning
     - accepted
   * - Record that disagrees with the matrix
     - warning, naming the texts lost or added
     - information


Root metadata
-------------

.. list-table::
   :header-rows: 1
   :widths: 24 22 54

   * - Key
     - Type
     - Meaning
   * - ``language``
     - string
     - Language tag of the file. See `Languages and domain`_.
   * - ``domain``
     - string
     - Domain of the file. See `Languages and domain`_.
   * - ``project_id_version``
     - string
     - Project name and version (gettext ``Project-Id-Version``).
   * - ``report_msgid_bugs_to``
     - string
     - Address for reports on the messages.
   * - ``pot_creation_date``
     - string
     - Creation date of the template.
   * - ``language_team``
     - string
     - Team in charge of the language.
   * - ``header_comment``
     - string
     - Comment about the whole file.
   * - ``statistics``
     - mapping
     - ``total_messages``: the number of entries; ``total_words``: the
       number of whitespace-separated words over every cell of every
       matrix.
   * - ``count``
     - mapping
     - ``messages``: the number of entries. Kept for compatibility with
       earlier files.

Every key is optional for a reader. The root metadata MUST be a mapping,
and a value of a string key MUST be a string. ``statistics`` and
``count`` SHOULD match the content; a difference is a warning. An unknown
key is a warning; the reader keeps it.


Languages and domain
^^^^^^^^^^^^^^^^^^^^

A ``language`` value, at the root or in an entry, MUST be a valid
language tag when it is present and not empty. An absent or empty value
is accepted.

When the reader knows which language the file is expected to hold, for
instance from its place in a repository, it compares each ``language``
value with it:

- a language of another family (``de-DE`` where ``fr-FR`` is expected)
  is an error;
- a different language of the same family (``fr-CA`` where ``fr-FR`` is
  expected) is a warning, which also names the scripts when they differ.

In the same way, a root ``domain`` other than the expected domain is an
error. An absent or empty ``domain`` is accepted.


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
    whose content changed since its counters were written. A reader MAY
    report it.

These checks concern one file. Checks that compare the same message
across the languages of a domain are described in
:doc:`/concept/integrity`.


Complete example
----------------

A file ``errors.json.i18t`` for the language ``en-US``, with one complete
message that has two declensions and two segments, and one draft message
with three segments:

.. code-block:: json

    {
        "metadata": {
            "language": "en-US",
            "domain": "errors",
            "project_id_version": "sync-app 2.1",
            "report_msgid_bugs_to": "i18n@example.org",
            "pot_creation_date": "",
            "language_team": "",
            "header_comment": "",
            "statistics": {"total_words": 30, "total_messages": 2},
            "count": {"messages": 2}
        },
        "files.missing": {
            "messages": [
                ["File {name} is missing.", "File {name} is missing from {repository}."],
                ["{n} files are missing.", ""]
            ],
            "metadata": {
                "version": "0.10.0",
                "language": "en-US",
                "context": "sync report",
                "locations": [
                    ["src/app/sync.py", 42],
                    ["src/app/sync.py", 57, 1, 0]
                ],
                "flags": ["python-format"],
                "user_comments": [],
                "auto_comments": [],
                "status": "complete",
                "singular_count": 2,
                "segment_count": 2,
                "fill_mask": [[true, true], [true, false]]
            }
        },
        "disk.alert": {
            "messages": [
                ["Disk usage is normal."],
                ["Disk usage is high ({percent} %)."],
                ["Disk is almost full ({percent} %)."]
            ],
            "metadata": {
                "version": "0.10.0",
                "language": "en-US",
                "context": "",
                "locations": [],
                "flags": ["python-format"],
                "user_comments": [],
                "auto_comments": [],
                "status": "draft",
                "singular_count": 1,
                "segment_count": 3,
                "fill_mask": [[true], [true], [true]]
            }
        }
    }

The same file in YAML, ``errors.yaml.i18t``:

.. code-block:: yaml

    metadata:
      language: en-US
      domain: errors
      project_id_version: sync-app 2.1
      report_msgid_bugs_to: i18n@example.org
      pot_creation_date: ''
      language_team: ''
      header_comment: ''
      statistics:
        total_messages: 2
        total_words: 30
      count:
        messages: 2
    files.missing:
      messages:
      - - File {name} is missing.
        - File {name} is missing from {repository}.
      - - '{n} files are missing.'
        - ''
      metadata:
        version: 0.10.0
        language: en-US
        context: sync report
        locations:
        - - src/app/sync.py
          - 42
        - - src/app/sync.py
          - 57
          - 1
          - 0
        flags:
        - python-format
        user_comments: []
        auto_comments: []
        status: complete
        singular_count: 2
        segment_count: 2
        fill_mask:
        - - true
          - true
        - - true
          - false
    disk.alert:
      messages:
      - - Disk usage is normal.
      - - Disk usage is high ({percent} %).
      - - Disk is almost full ({percent} %).
      metadata:
        version: 0.10.0
        language: en-US
        context: ''
        locations: []
        flags:
        - python-format
        user_comments: []
        auto_comments: []
        status: draft
        singular_count: 1
        segment_count: 3
        fill_mask:
        - - true
        - - true
        - - true

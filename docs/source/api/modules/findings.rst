Findings
========

The checks of the package do not raise: they return a list of findings,
one per point found. The functions that return findings are:

- :meth:`i18n_tools.models.book.Book.check`: the messages of one book;
- :meth:`i18n_tools.models.corpus.Corpus.check`: the books of one domain
  across languages;
- :func:`i18n_tools.loaders.loader.inspect_book_file`: one ``.i18t``
  file, without loading it;
- :func:`i18n_tools.core.inspect_corpus`: a module and domain of a
  repository, file by file, then as a corpus.

A finding is an immutable value with four fields:

``severity``
    ``"error"``, ``"warning"`` or ``"info"``. What each severity means
    for a file is given in :doc:`/reference/format`; for the model, in
    :doc:`/concept/integrity`.

``where``
    The identifier of the message concerned, or ``"root"`` when the
    finding concerns the file itself.

``message``
    A description of the point, in English.

``language``
    The language the finding concerns, or ``None``. Findings about one
    file of a repository carry the language of that file; findings that
    compare languages carry none.

The class of findings is not exported by the package in this release.

.. todo::

   Replace this page by an autodoc entry once the class is exported.

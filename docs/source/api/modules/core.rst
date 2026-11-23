Core module
===========

.. py:module:: i18n_tools.core

The entry point for the files of a repository. Given a ``Repository``, a
module and a domain, it finds where each language's ``.i18t`` file lives,
then loads, saves and checks books and corpora there. It also
synchronises the directory layout of a repository with its settings.

Paths follow the repository layout described in
:doc:`/concept/repository`.

Books and corpora
-----------------

.. autofunction:: load_book
.. autofunction:: save_book
.. autofunction:: load_corpus
.. autofunction:: save_corpus

Checks
------

.. autofunction:: inspect_corpus

The findings are described in :doc:`findings`.

Repository
----------

.. autofunction:: synchronize

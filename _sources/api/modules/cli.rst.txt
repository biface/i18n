CLI module
==========

.. py:module:: i18n_tools.cli

The ``i18n-tools`` command. Its subcommands, options, output and exit
status are described in :doc:`/reference/cli`; how to use them for
common tasks, in :doc:`/guides/cli`.

A failure of a subcommand is reported as :exc:`CliError`: the command
prints its message and exits with status 1.

.. autoexception:: CliError

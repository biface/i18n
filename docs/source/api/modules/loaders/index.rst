Loaders Module
==============

The **Loaders** module is responsible for loading and managing translation files. It is organized into four modules, in three abstraction layers:

- **Utils**: Low-level file operations.
- **Settings**: Low-level settings-file I/O, at the same level as Utils.
- **Handler**: Intermediate layer for path and file type management.
- **Loader**: High-level mapping between objects and procedures; sole bridge to /models/ (DD-37);
  also handles filesystem archive and aggregation operations (backups, multi-module/domain aggregation).

Utils, Settings and Handler are internal modules: ``loaders._utils``,
``loaders._settings`` and ``loaders._handler``. Each layer imports only the
layer below it: Handler imports Utils and Settings, Settings may import Utils,
and Loader imports Handler only. Every module outside ``loaders/`` imports
``loaders.loader`` only. A test of the suite checks these rules on the source
tree.


.. toctree::
   :maxdepth: 1

   utils
   settings
   handler
   loader


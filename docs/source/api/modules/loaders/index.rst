Loaders Module
==============

The **Loaders** module is responsible for loading and managing translation files. It is organized into four abstraction layers:

- **Utils**: Low-level file operations.
- **Handler**: Intermediate layer for path and file type management.
- **Loader**: High-level mapping between objects and procedures; sole bridge to /models/ (DD-37);
  also handles filesystem archive and aggregation operations (backups, multi-module/domain aggregation).


.. toctree::
   :maxdepth: 1

   utils
   handler
   loader


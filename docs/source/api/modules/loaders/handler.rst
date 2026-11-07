Handler module (internal)
=========================

Intermediate layer for path and file type management. Internal
module: imported by the loader module only.

.. automodule:: i18n_tools.loaders._handler

    .. autofunction:: build_path
    .. autofunction:: build_book_filename
    .. autofunction:: build_translation_lang_files
    .. autofunction:: check_json_integrity
    .. autofunction:: create_catalog
    .. autofunction:: create_dictionary
    .. autofunction:: create_directory
    .. autofunction:: create_template
    .. autofunction:: dump_dictionary
    .. autofunction:: fetch_catalog
    .. autofunction:: fetch_dictionary
    .. autofunction:: fetch_template
    .. autofunction:: file_exists
    .. autofunction:: load_config
    .. autofunction:: remove_catalog
    .. autofunction:: remove_dictionary
    .. autofunction:: remove_template
    .. autofunction:: save_config
    .. autofunction:: update_catalog
    .. autofunction:: update_dictionary

    Low-level operations offered to the loader module:

    .. autofunction:: path_exists
    .. autofunction:: detect_format
    .. autofunction:: load_json
    .. autofunction:: save_json
    .. autofunction:: load_by_format
    .. autofunction:: save_by_format
    .. autofunction:: build_dictionary_path
    .. autofunction:: create_gzip
    .. autofunction:: non_traversal_path
    .. autofunction:: check_module
    .. autofunction:: check_domains

    .. autofunction:: verify_paths_and_modules()
        :no-index:
    .. autofunction:: verify_available_languages()
        :no-index:
    .. autofunction:: _verify_target_module()
        :no-index:
    .. autofunction:: verify_target_domain()
        :no-index:
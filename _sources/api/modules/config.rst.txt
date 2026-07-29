Configuration Module
=====================

.. automodule:: i18n_tools.config

Configuartion class
-------------------

This class is designed as a singleton in order to manage a single instance.

.. autoclass:: Config

    .. automethod:: load
    .. automethod:: save
    .. automethod:: get
    .. automethod:: set
    .. automethod:: get_repository
    .. automethod:: update_repository
    .. automethod:: set_repository
    .. automethod:: add_details
    .. automethod:: update_details
    .. automethod:: add_author
    .. automethod:: get_author
    .. automethod:: remove_author
    .. automethod:: add_translator
    .. automethod:: update_translator
    .. automethod:: get_translator
    .. automethod:: remove_translator
    .. automethod:: list_translators
    .. automethod:: add_module
    .. automethod:: remove_module
    .. automethod:: clean_modules
    .. automethod:: add_domain
    .. automethod:: remove_domain
    .. automethod:: clean_domains
    .. automethod:: switch_to_package_config
    .. automethod:: switch_to_application_config
    .. automethod:: toggle_config
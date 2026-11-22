Book module
===========

.. automodule:: i18n_tools.models.book

   .. autoclass:: BookOptions

   .. autoclass:: Book

      .. autoproperty:: language
      .. autoproperty:: domain
      .. autoproperty:: format_version
      .. autoproperty:: version
      .. automethod:: set_version
      .. automethod:: set_gettext
      .. automethod:: add
      .. automethod:: rename
      .. automethod:: remove
      .. automethod:: load
      .. automethod:: save
      .. automethod:: check
      .. automethod:: get_language
      .. automethod:: add_language
      .. automethod:: update_language
      .. automethod:: remove_language
      .. automethod:: get_domain
      .. automethod:: add_domain
      .. automethod:: update_domain
      .. automethod:: remove_domain
      .. automethod:: get_file_format
      .. automethod:: add_file_format
      .. automethod:: update_file_format
      .. automethod:: remove_file_format
      .. automethod:: set_metadata
      .. automethod:: __set_filename
         :no-index:
      .. automethod:: __iter__
         :no-index:

   .. autoclass:: FallbackBook

      .. automethod:: get_message
      .. autoproperty:: language
      .. autoproperty:: domain

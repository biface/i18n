Corpus module
=============

.. automodule:: i18n_tools.models.corpus

   .. autoclass:: Message

      .. autoproperty:: has_variants
      .. autoproperty:: has_plurals
      .. autoproperty:: translations_set
      .. automethod:: get_id
      .. automethod:: add_message
      .. automethod:: update_message
      .. automethod:: remove_message
      .. automethod:: get_main
      .. automethod:: get_main_plurals
      .. automethod:: add_main
      .. automethod:: update_main
      .. automethod:: remove_main
      .. automethod:: get_variant
      .. automethod:: get_variant_plurals
      .. automethod:: add_variant
      .. automethod:: update_variant
      .. automethod:: remove_variant
      .. automethod:: get_main_segment
      .. automethod:: get_variant_segment
      .. automethod:: get_segment
      .. automethod:: add_main_segment
      .. automethod:: add_variant_segment
      .. automethod:: update_main_segment
      .. automethod:: update_variant_segment
      .. automethod:: get_metadata
      .. automethod:: add_location
      .. automethod:: add_language
      .. automethod:: add_comment
      .. automethod:: add_metadata
      .. automethod:: update_metadata
      .. automethod:: remove_metadata
      .. automethod:: switch
      .. automethod:: toggle
      .. automethod:: format
      .. automethod:: get_format_variables
      .. automethod:: to_i18n_tools_format
      .. automethod:: from_i18n_tools
      .. automethod:: equals
      .. automethod:: is_similar

      .. automethod:: __check_plural_forms__
         :no-index:
      .. automethod:: __check_alternatives__
         :no-index:
      .. automethod:: __check_alternative_plural_forms__
         :no-index:
      .. automethod:: __check_metadata__
         :no-index:
      .. automethod:: __count_singular__
         :no-index:
      .. automethod:: __count_plurals__
         :no-index:
      .. automethod:: _assert_valid_option
         :no-index:
      .. automethod:: _assert_valid_token_in_option
         :no-index:
      .. automethod:: _assert_valid_default_plural_token
         :no-index:
      .. automethod:: _refresh_counts
         :no-index:
      .. automethod:: _remove_default_segment
         :no-index:
      .. automethod:: _remove_default_plurals_segment
         :no-index:
      .. automethod:: _add_default_segment
         :no-index:
      .. automethod:: _add_default_plurals_segment
         :no-index:
      .. automethod:: _add_options_segment
         :no-index:
      .. automethod:: _add_options_plurals_segment
         :no-index:
      .. automethod:: _update_default_segment
         :no-index:
      .. automethod:: _update_default_plurals_segment
         :no-index:
      .. automethod:: _update_options_segment
         :no-index:
      .. automethod:: _update_options_plurals_segment
         :no-index:
      .. automethod:: _remove_options_segment
         :no-index:
      .. automethod:: _remove_options_plurals_segment
         :no-index:

   .. autoclass:: Book

      .. automethod:: add
      .. automethod:: remove
      .. automethod:: load
      .. automethod:: save
      .. automethod:: get_language
      .. automethod:: add_language
      .. automethod:: update_language
      .. automethod:: remove_language
      .. automethod:: get_domain
      .. automethod:: add_domain
      .. automethod:: update_domain
      .. automethod:: remove_domain
      .. automethod:: get_format
      .. automethod:: add_format
      .. automethod:: update_format
      .. automethod:: remove_format
      .. automethod:: set_metadata
      .. automethod:: __set_filename
         :no-index:
      .. automethod:: _compute_statistics
         :no-index:
      .. automethod:: __iter__
         :no-index:


   .. autoclass:: Corpus

   .. autoclass:: Encyclopaedia


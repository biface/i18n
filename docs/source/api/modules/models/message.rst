Message module
==============

.. automodule:: i18n_tools.models.message

   .. autoclass:: Declension
      :members: segments, from_segments

   .. autoclass:: Location

   .. autoclass:: DeclensionFields

   .. autoclass:: Message

      .. autoproperty:: message
      .. autoproperty:: principal
      .. autoproperty:: variants
      .. autoproperty:: has_variants
      .. autoproperty:: has_plurals
      .. autoproperty:: translations_set
      .. automethod:: get_id
      .. automethod:: add_message
      .. automethod:: update_message
      .. automethod:: remove_message
      .. automethod:: get_principal
      .. automethod:: get_principal_plurals
      .. automethod:: add_principal
      .. automethod:: update_principal
      .. automethod:: remove_principal
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

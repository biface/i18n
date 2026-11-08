Message module
==============

.. automodule:: i18n_tools.models.message

   .. autoclass:: Declension
      :members: segments, from_segments

   .. autoclass:: Location

   .. autoclass:: DeclensionFields

   .. autoclass:: Message

      .. automethod:: from_matrix
      .. automethod:: get_id
      .. autoproperty:: principal
      .. autoproperty:: variants
      .. autoproperty:: matrix
      .. autoproperty:: has_variants
      .. autoproperty:: has_plurals
      .. automethod:: get_variant
      .. automethod:: get_segment
      .. autoproperty:: status
      .. autoproperty:: observed
      .. autoproperty:: recorded
      .. autoproperty:: has_divergence
      .. automethod:: mark_complete
      .. automethod:: reopen
      .. automethod:: add_principal
      .. automethod:: update_principal
      .. automethod:: remove_principal
      .. automethod:: add_variant
      .. automethod:: update_variant
      .. automethod:: remove_variant
      .. automethod:: add_segment
      .. automethod:: update_segment
      .. automethod:: remove_segment
      .. automethod:: switch
      .. automethod:: toggle
      .. automethod:: format
      .. automethod:: get_tokens
      .. autoproperty:: texts
      .. automethod:: equal
      .. automethod:: isomorph
      .. automethod:: similar
      .. automethod:: get_metadata
      .. automethod:: add_location
      .. automethod:: add_language
      .. automethod:: add_comment
      .. automethod:: add_metadata
      .. automethod:: update_metadata
      .. automethod:: remove_metadata

   .. autofunction:: extract_tokens

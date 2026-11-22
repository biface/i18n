Message module
==============

.. py:module:: i18n_tools.models.message

.. autoclass:: Declension
   :members: segments, from_segments

.. autoclass:: LocationEntry

.. autoclass:: DeclensionFields

.. autoclass:: MessageOptions

.. py:type:: MessageStatus
   :canonical: Literal['draft', 'complete']

   Completion status of a message: ``"draft"`` or ``"complete"``.

.. autoclass:: Message

   .. automethod:: from_matrix
   .. autoproperty:: id
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
   .. automethod:: record
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
   .. autoproperty:: context
   .. autoproperty:: rules
   .. autoproperty:: locations
   .. autoproperty:: flags
   .. autoproperty:: user_comments
   .. autoproperty:: auto_comments
   .. automethod:: get_metadata
   .. automethod:: add_location
   .. automethod:: remove_location
   .. automethod:: add_flag
   .. automethod:: remove_flag
   .. automethod:: add_comment
   .. automethod:: remove_comment
   .. automethod:: add_metadata
   .. automethod:: update_metadata
   .. automethod:: remove_metadata

.. autofunction:: extract_tokens

.. autoclass:: i18n_tools.models.ContentCounters

   .. autoproperty:: declensions
   .. autoproperty:: alternatives
   .. autoproperty:: singulars
   .. autoproperty:: plurals
   .. autoproperty:: segments
   .. autoproperty:: tokens
   .. autoproperty:: fill_mask
   .. automethod:: defects
   .. automethod:: differences

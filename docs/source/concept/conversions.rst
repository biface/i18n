Conversion of Alternative Messages
==================================
To integrate alternative messages from the proprietary `i18n-tools` format into classic translation formats like Babel and i18next, an extended ID convention can be used. This approach ensures clarity and compatibility with existing tools.

.. warning::
   The following is finalised and will likely be subject to revision.

Extended ID Convention in GNU i18n Standard
-------------------------------------------

The extended ID convention involves appending a numerical suffix to the base message ID to represent alternative messages and their plural forms. Here's how it works:

1. **Main Message**:
   - Use the base ID (e.g., ``id``) for the main message.
   - Example:

     .. code-block:: po

         msgid "id"
         msgstr "main_msg"

2. **Alternative Messages**:
   - Use extended IDs (e.g., ``id_001``, ``id_002``) for alternative messages.
   - Example:

     .. code-block:: po

         msgid "id_001"
         msgstr "alt_1_msg"

         msgid "id_002"
         msgstr "alt_2_msg_with'{variable}'_inside"

3. **Plural Forms**:
   - Use a ``_plural`` suffix for plural forms of the main message and its alternatives.
   - Example:

     .. code-block:: po

         msgid "id_plural"
         msgid_plural "plural_1_of_main_msg"
         msgstr[0] "plural_2_of_main_msg"
         msgstr[1] "plural_3_of_main_msg"

         msgid "id_001_plural"
         msgid_plural "plural_1_of_alt_1_msg"
         msgstr[0] "plural_2_of_alt_1_msg"
         msgstr[1] "plural_3_of_alt_1_msg"

Extended ID Convention for i18next Format
-----------------------------------------

The extended ID convention involves appending a numerical suffix to the base message ID to represent alternative messages and their plural forms. Here's how it works:

1. **Main Message**:
   - Use the base ID (e.g., ``id``) for the main message.
   - Example:

     .. code-block:: json

        {
            "key1": "value1",
            "key2": "value2",
            "key3_plural": "plural value",
            "key3": "singular value",
            "nested": {
                "key": "nested value"
            }
        }

2. **Alternative Messages**:
   - Use extended IDs (e.g., ``id_001``, ``id_002``) for alternative messages.
   - Example:

     .. code-block:: json

         {
           "id_001": "alt_1_msg",
           "id_002": "alt_2_msg_with'{variable}'_inside"
         }

3. **Plural Forms**:
   - Use a ``_plural`` suffix for plural forms of the main message and its alternatives.
   - Example:

     .. code-block:: json

         {
           "id_plural": {
             "one": "plural_1_of_main_msg",
             "other": "plural_2_of_main_msg"
           },
           "id_001_plural": {
             "one": "plural_1_of_alt_1_msg",
             "other": "plural_2_of_alt_1_msg"
           }
         }

Benefits
--------

- **Clarity**: This convention clearly distinguishes between main messages, alternatives, and their plural forms.
- **Compatibility**: It is compatible with the ``.po`` format used by Babel and the i18next format, allowing seamless integration with existing i18next setups.
- **Automation**: Scripts can be created to automate the conversion process, ensuring consistency across translations.

By following this extended ID convention, you can efficiently manage alternative messages and their plural forms in a format that is both clear and compatible with the i18next framework.
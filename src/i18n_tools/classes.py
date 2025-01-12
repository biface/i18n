"""
classes.py
==========

This module provides utility classes for the i18n-tools package, including
the `Singleton` metaclass.

**Key Features:**
- Define the `Singleton` metaclass to ensure single-instance objects.
- Provide reusable structures for core package functionality.

**License:**
This file is distributed under the `CeCILL-C Free Software License Agreement
<https://cecill.info/licences/Licence_CeCILL-C_V1-en.html>`_. By using or
modifying this file, you agree to abide by the terms of this license.

**Author(s):**
This module is authored and maintained as part of the i18n-tools package.

"""

from threading import Lock


class Singleton(type):
    """
    Metaclass for menu singleton class
    """

    _instances = {}
    _lock = Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)

        return cls._instances[cls]

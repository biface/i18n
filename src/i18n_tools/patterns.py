"""
Design Patterns Module
======================

This module contains essential design patterns such as Singleton, which are necessary for the architecture of the i18n-tools package. These patterns ensure that the system is robust, scalable, and maintains a clean and efficient structure.

Key Responsibilities:
    - Implement and manage design patterns like Singleton.
    - Ensure the architectural integrity of the i18n-tools package.
"""

from threading import Lock


class Singleton(type):
    """
    Metaclass for singleton class

    This metaclass ensures that only one instance of a class is created. It used in i18n-tools to ensure that only one
    instance of the `Config` class is created.
    """

    _instances = {}
    _lock = Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)

        return cls._instances[cls]

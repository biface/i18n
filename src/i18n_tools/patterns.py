"""
Design Patterns Module
======================

This module contains essential design patterns such as Singleton, which are necessary for the architecture of the i18n-tools package. These patterns ensure that the system is robust, scalable, and maintains a clean and efficient structure.

Key Responsibilities:
    - Implement and manage design patterns like Singleton.
    - Ensure the architectural integrity of the i18n-tools package.
"""

from threading import Lock
from typing import ClassVar, TypeVar, cast

from ._compat import override

_T = TypeVar("_T")


class Singleton(type):
    """
    Metaclass for singleton class

    This metaclass ensures that only one instance of a class is created. It used in i18n-tools to ensure that only one
    instance of the `Config` class is created.
    """

    _instances: ClassVar[dict[type, object]] = {}
    _lock: ClassVar[Lock] = Lock()

    @override
    def __call__(cls: type[_T], *args: object, **kwargs: object) -> _T:
        # Returning the instance type lets type checkers check the call's
        # arguments against the class's own __init__ signature.
        with Singleton._lock:
            if cls not in Singleton._instances:
                Singleton._instances[cls] = type.__call__(cls, *args, **kwargs)
            instance = Singleton._instances[cls]

        # Safe: the mapping only ever stores an instance of its key.
        return cast(_T, instance)

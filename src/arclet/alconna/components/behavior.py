from __future__ import annotations

from abc import ABCMeta, abstractmethod
from functools import lru_cache
from typing import TYPE_CHECKING, Union, Type, Callable
from inspect import isclass

if TYPE_CHECKING:
    from ..arparma import Arparma


class ArparmaBehavior(metaclass=ABCMeta):
    """
    解析结果行为器的基类, 对应一个对解析结果的操作行为
    """

    requires: list[type[ArparmaBehavior] | ArparmaBehavior]

    if TYPE_CHECKING:
        operate: Callable[[Arparma], None]
    else:
        @abstractmethod
        def operate(self, interface: Arparma):
            ...


T_ABehavior = Union[Type['ArparmaBehavior'], 'ArparmaBehavior']


@lru_cache(4096)
def requirement_handler(behavior: T_ABehavior) -> list[T_ABehavior]:
    unbound_mixin = getattr(behavior, "requires", [])
    result: list[T_ABehavior] = []
    for i in unbound_mixin:
        if (isclass(i) and issubclass(i, ArparmaBehavior)) or isinstance(i, ArparmaBehavior):
            result.extend(requirement_handler(i))
    result.append(behavior)
    return result

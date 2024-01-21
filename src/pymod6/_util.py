from __future__ import annotations

import io
from typing import Any, BinaryIO, MutableMapping, Sequence, TextIO, TypeVar

from typing_extensions import TypeGuard

_K = TypeVar("_K")
_V = TypeVar("_V")


def is_binary_io(obj: Any) -> TypeGuard[BinaryIO]:
    return isinstance(obj, (io.RawIOBase, io.BufferedIOBase))


def is_text_io(obj: Any) -> TypeGuard[TextIO]:
    return isinstance(obj, io.TextIOBase)


def assign_nested_mapping(
    mapping: MutableMapping[_K, MutableMapping[_K, _V] | _V],
    keys: Sequence[_K],
    value: _V,
) -> None:
    """
    >>> x = {}; assign_nested_mapping(x, ("a", "b", "c"), 1); x
    {'a': {'b': {'c': 1}}}
    >>> x = {"a": {}}; assign_nested_mapping(x, ("a", "b", "c"), 1); x
    {'a': {'b': {'c': 1}}}
    >>> x = {"a": 123}; assign_nested_mapping(x, ("a", "b", "c"), 1); x
    Traceback (most recent call last):
    ...
    ValueError: expected mapping at (..., 'b'), found <class 'int'>
    """
    curr: MutableMapping[_K, MutableMapping[_K, _V] | _V] = mapping
    for k in keys[:-1]:
        try:
            curr.setdefault(k, mapping.__class__())  # type: ignore[arg-type]
        except AttributeError as ex:
            raise ValueError(
                f"expected mapping at (..., '{k}'), found {type(curr)}"
            ) from ex
        curr = curr[k]  # type: ignore[assignment]
    curr[keys[-1]] = value

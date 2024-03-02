from __future__ import annotations

import functools
import io
import math
from typing import (
    Any,
    BinaryIO,
    Mapping,
    MutableMapping,
    Sequence,
    TextIO,
    TypeVar,
    Union,
    cast,
)

import pydantic
from typing_extensions import TypeAlias, TypeGuard

_K = TypeVar("_K")
_V = TypeVar("_V")

_NestedMapping: TypeAlias = Mapping[_K, Union[_V, "_NestedMapping[_K, _V]"]]
_NestedMutableMapping: TypeAlias = MutableMapping[
    _K, Union[_V, "_NestedMutableMapping[_K, _V]"]
]


class MappingMergeError(ValueError):
    """Raised when merging nested maps fails due to a key collision."""

    key_path: tuple[Any, ...]

    def __init__(self, *args: Any, key_path: tuple[Any, ...]) -> None:
        self.key_path = key_path
        super().__init__(*args)

    def __str__(self) -> str:
        return f"collision at key {self.key_path}: {super().__str__()}"


def is_binary_io(obj: Any) -> TypeGuard[BinaryIO]:
    return isinstance(obj, (io.RawIOBase, io.BufferedIOBase))


def is_text_io(obj: Any) -> TypeGuard[TextIO]:
    return isinstance(obj, io.TextIOBase)


def assign_nested_mapping(
    mapping: _NestedMutableMapping[_K, _V],
    keys: Sequence[_K],
    value: _V,
) -> None:
    """
    Set a nested mapping item to the given value.

    Calling
    ```python
    assign_nested_mapping(obj, (k1, k2, k3), value)
    ```
    is the same as writing
    ```python
    cls = obj.__class__
    obj.setdefault(k1, cls()).setdefault(k2, cls()).setdefault(k3, cls()) = value
    ```

    >>> x = {}; assign_nested_mapping(x, ("a", "b", "c"), 1); x
    {'a': {'b': {'c': 1}}}
    >>> x = {"a": {}}; assign_nested_mapping(x, ("a", "b", "c"), 1); x
    {'a': {'b': {'c': 1}}}
    >>> x = {"a": 123}; assign_nested_mapping(x, ("a", "b", "c"), 1); x
    Traceback (most recent call last):
    ...
    ValueError: expected mapping at (..., 'b'), found <class 'int'>
    """
    curr: _NestedMutableMapping[_K, _V] = mapping
    cls = mapping.__class__

    for k in keys[:-1]:
        try:
            curr.setdefault(k, cls())
        except AttributeError as ex:
            raise ValueError(
                f"expected mapping at (..., '{k}'), found {type(curr)}"
            ) from ex
        curr = cast("_NestedMutableMapping[_K, _V]", curr[k])
    curr[keys[-1]] = value


def merge_nested_mappings(
    target: _NestedMutableMapping[_K, _V],
    *sources: _NestedMapping[_K, _V],
    allow_override: bool = False,
) -> None:
    """
    Merge nested mappings into a single mapping.

    After calling this funciton, the value of
    ```
    target[k1][k2][k3]
    ```
    will be equal to one of the following:
    ```
    sources[0][k1][k2][k3]
    sources[1][k1][k2][k3]
    # ...
    sources[-2][k1][k2][k3]
    sources[-1][k1][k2][k3]
    ```
    If `allow_override` is `False`, then only one of the expressions above may
    successully evaluate to a value, and the rest must raise a `KeyError`.
    The value of `target[k1][k2][k3]` is the single possible value.

    If `allow_override` is `False`, then multiple of the expressions above may
    successfully evaluate to a value. The value of `target[k1][k2][k3]` will be equal
    to the *last* possible value.

    Examples
    --------

    >>> x = {}
    >>> merge_nested_mappings(x, {'color': 'red'}); x
    {'color': 'red'}
    >>> merge_nested_mappings(x, {'color': 'blue'}); x
    Traceback (most recent call last):
    ...
    pymod6._util.MappingMergeError: collision at key ('color',): cannot override value when allow_override=False
    >>> merge_nested_mappings(x, {'color': 'blue'}, allow_override=True); x
    {'color': 'blue'}
    >>> merge_nested_mappings(x, {"legs": {"cat": 4}}, {"legs": {"spider": 8}}); x
    {'color': 'blue', 'legs': {'cat': 4, 'spider': 8}}

    Mappings will be deeply copied, while all other values will be assigned directly:
    >>> m = {"a": {"b": [1, 2, 3]}}
    >>> x = {}
    >>> merge_nested_mappings(x, m)
    >>> x["a"] is m["a"]
    False
    >>> x["a"]["b"] is m["a"]["b"]
    True
    """
    for source_map in sources:
        for key, value in source_map.items():
            key_defined = key in target

            # Check for collision
            if (
                not allow_override
                and key_defined
                and not isinstance(target[key], Mapping)
            ):
                raise MappingMergeError(
                    "cannot override value when allow_override=False",
                    key_path=(key,),
                )

            # Merge 'value' into `target[key]'.
            if isinstance(value, Mapping):
                if not key_defined:
                    target[key] = target.__class__()
                try:
                    merge_nested_mappings(
                        cast("_NestedMutableMapping[_K, _V]", target[key]),
                        value,
                        allow_override=allow_override,
                    )
                except MappingMergeError as ex:
                    ex.key_path = (key, *ex.key_path)
                    raise
            else:
                target[key] = value


def num_digits(x: int) -> int:
    """
    Return the number of decimal digits needed to represent the non-negative integer x.

    >>> num_digits(0)
    1
    >>> num_digits(9)
    1
    >>> num_digits(10)
    2
    >>> num_digits(999_999_999_999)
    12
    >>> num_digits(1_000_000_000_000)
    13
    >>> num_digits(-1)
    Traceback (most recent call last):
    ...
    ValueError: value must be non-negative, got -1
    """
    if x < 0:
        raise ValueError(f"value must be non-negative, got {x}")
    if x == 0:
        return 1
    return 1 + int(math.log10(x))


def make_adapter(schema: type[_V]) -> pydantic.TypeAdapter[_V]:
    """Create and cache a `pydantic.TypeAdapter` instance for the given schema."""
    return pydantic.TypeAdapter(schema)


# Using functools.lru_cache as a decorator confuses mypy.
make_adapter = functools.lru_cache(None)(make_adapter)  # type: ignore[assignment]

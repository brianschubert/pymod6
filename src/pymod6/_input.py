"""
Input JSON file handling.
"""

from __future__ import annotations

import json
import re
from typing import Any, Final

import pydantic
from pydantic import ConfigDict
from typing_extensions import TypedDict

_COMMENT_PATTERN: Final = re.compile(
    r'#(?:[^\n"]*(!<\\)"[^\n"]*(!<\\)")*[^\n"]*$', flags=re.MULTILINE
)


class ModtranInput(TypedDict, total=False):
    NAME: str
    DESCRIPTION: str
    CASE: int
    CASE_TEMPLATE: int


class Case(TypedDict, total=False):
    MODTRANINPUT: ModtranInput


class JSONInput(TypedDict, total=True):
    # noinspection PyTypedDict
    __pydantic_config__ = ConfigDict(extra="forbid")

    MODTRAN: list[Case]


class _CommentedJSONDecoder(json.JSONDecoder):
    _comment_pattern: re.Pattern

    def __init__(self, comment_pattern: str | re.Pattern, **kwargs: Any) -> None:
        self._comment_pattern = re.compile(comment_pattern)
        super().__init__(**kwargs)

    # noinspection PyMethodOverriding
    def decode(self, s) -> Any:
        return super().decode(self._comment_pattern.sub("", s))


def read_json_input(
    s: str, strip_comments: bool = True, validate: bool = True
) -> JSONInput:
    if strip_comments:
        input_dict = json.loads(
            s, cls=_CommentedJSONDecoder, comment_pattern=_COMMENT_PATTERN
        )
    else:
        input_dict = json.loads(s)

    if validate:
        return pydantic.TypeAdapter(JSONInput).validate_python(input_dict)

    return input_dict

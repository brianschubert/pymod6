from __future__ import annotations

import copy
import datetime
from typing import NamedTuple

import pydantic
from typing_extensions import Self, Unpack

from .. import _util
from . import schema as _schema


class ModtranInputBuilder:
    """
    Input builder.

    For:
    - Conveniently and programmatically constructing series of templated cases.
    - Ensuring consistent file options across all cases.
    """

    _cases: list[_schema.ModtranInput]

    _root_name_format: str

    _validate: bool

    def __init__(
        self,
        *,
        root_name_format: str = "case{case_index:0{case_digits}}",  # {timestamp:%Y-%m-%dT%H-%M-%S}_
        validate: bool = True,
    ) -> None:
        self._cases = []
        self._root_name_format = root_name_format
        self._validate = validate

    def add_case(
        self,
        case_input: _schema.ModtranInput,
        /,
        make_copy: bool = True,
        **kwargs: Unpack[_schema.ModtranInput],
    ) -> CaseHandle:
        if make_copy:
            case_input = copy.deepcopy(case_input)

        index = self._next_index()
        case_input["CASE"] = index

        for key, value in kwargs.items():
            _util.assign_nested_mapping(case_input, key.split("__"), value)  # type: ignore[arg-type]

        if self._validate:
            case_input = pydantic.TypeAdapter(_schema.ModtranInput).validate_python(
                case_input
            )

        self._cases.append(case_input.copy())
        return CaseHandle(self, index)

    def _next_index(self) -> int:
        return len(self._cases)

    def build_json_input(
        self,
        *,
        output_legacy: bool = False,
        output_sli: bool = False,
        output_csv: bool = False,
        outupt_corrk: bool = False,
        binary: bool = False,
        json_opt: _schema.JSONPrintOpt = _schema.JSONPrintOpt.WRT_STAT_INPUT,
        unify_json: bool = False,
        unify_csv: bool = False,
    ) -> _schema.JSONInput:
        case_digits = _util.num_digits(len(self._cases) - 1)

        for case in self._cases:
            root_name = self._root_name_format.format(
                case_index=case["CASE"],
                case_digits=case_digits,
                timestamp=datetime.datetime.now(),
            )

            case.setdefault("NAME", root_name)

            file_options: _schema.FileOptions = case.setdefault("FILEOPTIONS", {})
            file_options["FLROOT"] = root_name

            file_options["JSONPRNT"] = (
                "all_cases.json" if unify_json else f"{root_name}.json"
            )
            file_options["JSONOPT"] = json_opt

            file_options["NOFILE"] = 0 if output_legacy else 2

            if output_sli:
                file_options["SLIPRNT"] = root_name

            if output_csv:
                file_options["CSVPRNT"] = (
                    "all_cases.csv" if unify_csv else f"{root_name}.csv"
                )

            file_options["BINARY"] = binary
            file_options["CKPRNT"] = outupt_corrk

        input_json: _schema.JSONInput = {
            "MODTRAN": [{"MODTRANINPUT": case} for case in self._cases]
        }

        if self._validate:
            return pydantic.TypeAdapter(_schema.JSONInput).validate_python(input_json)

        return input_json


class CaseHandle(NamedTuple):
    builder: ModtranInputBuilder
    case_index: int

    def template_extend(
        self,
        case_extension: _schema.ModtranInput | None = None,
        /,
        make_copy: bool = True,
        **kwargs: Unpack[_schema.ModtranInput],
    ) -> Self:
        if case_extension is None:
            case_extension = {}
        elif make_copy:
            case_extension = copy.deepcopy(case_extension)

        case_extension["CASE TEMPLATE"] = self.case_index
        self.builder.add_case(case_extension, make_copy=False, **kwargs)
        return self

    def finish_case(self) -> ModtranInputBuilder:
        return self.builder

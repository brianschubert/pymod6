from __future__ import annotations

import math
from typing import NamedTuple

from typing_extensions import Unpack

from ._json import FileOptions, JSONInput, JSONPrintOpt, ModtranInput


class ModtranInputBuilder:
    """
    Input builder.

    For:
    - Conveniently and programmatically constructing series of templated cases.
    - Ensuring consistent file options across all cases.
    """

    _cases: list[ModtranInput]

    _root_name_format: str

    def __init__(
        self,
        root_name_format: str = "case{case_index:0{case_digits}}",
    ) -> None:
        self._cases = []
        self._root_name_format = root_name_format

    def add_case(self, case_input: ModtranInput) -> CaseHandle:
        index = self._next_index()
        case_input["CASE"] = index
        self._cases.append(case_input)
        return CaseHandle(self, index)

    def _next_index(self) -> int:
        return len(self._cases)

    def build_json_input(
        self,
        *,
        output_legacy: bool = False,
        output_sli: bool = False,
        output_csv: bool = False,
        binary: bool = False,
        json_opt: JSONPrintOpt = JSONPrintOpt.WRT_NONE,
    ) -> JSONInput:
        case_digits = 1 + int(math.log10(len(self._cases)))

        for case in self._cases:
            root_name = self._root_name_format.format(
                case_index=case["CASE"], case_digits=case_digits
            )

            file_options: FileOptions = case.setdefault("FILEOPTIONS", {})
            file_options["FLROOT"] = root_name

            file_options["JSONPRNT"] = f"{root_name}.json"
            file_options["JSONOPT"] = json_opt

            file_options["NOFILE"] = 0 if output_legacy else 2

            if output_sli:
                file_options["SLIPRNT"] = root_name

            if output_csv:
                file_options["CSVPRNT"] = f"{root_name}.csv"

            file_options["BINARY"] = binary

        return {"MODTRAN": [{"MODTRANINPUT": case} for case in self._cases]}


class CaseHandle(NamedTuple):
    builder: ModtranInputBuilder
    case_index: int

    def template_extend(
        self,
        case_extension: ModtranInput | None = None,
        /,
        **kwargs: Unpack[ModtranInput],
    ) -> CaseHandle:
        if case_extension is not None and kwargs:
            raise ValueError("positional and keyword arguments cannot both be used")

        if case_extension is None:
            case_extension = kwargs

        case_extension["CASE TEMPLATE"] = self.case_index
        return self.builder.add_case(case_extension)

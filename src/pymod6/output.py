"""
Output file handling.

Utilities for navigating output file placement in the filesystem.
"""


from __future__ import annotations

import pathlib
from dataclasses import dataclass
from typing import Sequence, overload

from pymod6.input import _json


@dataclass
class ModtranOutputFiles(Sequence["CaseResultFilesNavigator"]):
    """
    Collection of output files from a MODTRAN run, organized by case.

    Output file paths are resolved lazily.
    """

    input: _json.JSONInput
    work_dir: pathlib.Path

    # TODO: interface for collecting output files "post mortem" / directly from disk.

    # Sequence.__getitem__ overloads required by type checkers.

    @overload
    def __getitem__(self, case_index: int, /) -> CaseResultFilesNavigator:
        ...

    @overload
    def __getitem__(self, case_index: slice, /) -> Sequence[CaseResultFilesNavigator]:
        ...

    def __getitem__(
        self, case_index: int | slice, /
    ) -> CaseResultFilesNavigator | Sequence[CaseResultFilesNavigator]:
        if isinstance(case_index, slice):
            # https://docs.python.org/3/reference/datamodel.html#slice.indices
            return [self[idx] for idx in range(*case_index.indices(len(self)))]

        # TODO: fallback to case listed in 'CASE TEMPLATE' on lookup fail?
        case = self.input["MODTRAN"][case_index]
        return CaseResultFilesNavigator(
            self.work_dir,
            case["MODTRANINPUT"]["FILEOPTIONS"],
            case["MODTRANINPUT"].get("NAME"),
        )

    def __len__(self) -> int:
        return len(self.input["MODTRAN"])


@dataclass
class CaseResultFilesNavigator:
    """
    Index into available result files for a single case.

    Not all files will exist, depending on execution options.

    .. warning::
        Some files may contain results for multiple cases (e.g. '.csv', '.acd', ...)
        if the same options are used in multiple cases.

    .. warning::
        SLI files will have numeric suffixes added if multiple cases use the same SLIPRNT,
         which this class does not account for.
    """

    work_dir: pathlib.Path
    file_options: _json.FileOptions
    name: str | None

    @property
    def json(self) -> pathlib.Path:
        path = self.work_dir.joinpath(self.file_options["JSONPRNT"])
        # Always replaces last suffix with .json
        return path.with_suffix(".json")

    @property
    def sli_header(self) -> pathlib.Path:
        return self._resolve_sli(".hdr")

    @property
    def sli_data(self) -> pathlib.Path:
        return self._resolve_sli(".sli")

    @property
    def sli_flux_header(self) -> pathlib.Path:
        return self._resolve_sli("_flux.hdr")

    @property
    def sli_flux_data(self) -> pathlib.Path:
        return self._resolve_sli("_flux.sli")

    @property
    def sli_scan_header(self) -> pathlib.Path:
        return self._resolve_sli("_scan.hdr")

    @property
    def sli_scan_data(self) -> pathlib.Path:
        return self._resolve_sli("_scan.sli")

    @property
    def sli_corrk_header(self) -> pathlib.Path:
        return self._resolve_sli("_highres.hdr")

    @property
    def sli_corrk_data(self) -> pathlib.Path:
        return self._resolve_sli("_highres.sli")

    @property
    def csv(self) -> pathlib.Path:
        return self._resolved_csv("")

    @property
    def csv_flux(self) -> pathlib.Path:
        return self._resolved_csv("_flux")

    @property
    def csv_scan(self) -> pathlib.Path:
        return self._resolved_csv("_scan")

    @property
    def csv_corrk(self) -> pathlib.Path:
        return self._resolved_csv("_highres")

    @property
    def acd_text(self) -> pathlib.Path:
        return self._resolve_legacy_path(".acd", "atmcor.asc")

    @property
    def acd_binary(self) -> pathlib.Path:
        return self._resolve_legacy_path("_b.acd", "atmcor.bin")

    @property
    def tape7_text(self) -> pathlib.Path:
        return self._resolve_legacy_path(".tp7", "tape7")

    @property
    def tape7_binary(self) -> pathlib.Path:
        return self._resolve_legacy_path("_b.tp7", "tap7bin")

    @property
    def tape6(self) -> pathlib.Path:
        return self._resolve_legacy_path(".tp6", "tape6")

    @property
    def scan(self) -> pathlib.Path:
        return self._resolve_legacy_path(".7sc", "tape7.scn")

    @property
    def pth(self) -> pathlib.Path:
        return self._resolve_legacy_path("._pth", "rfract._pth")

    @property
    def plt_text(self) -> pathlib.Path:
        return self._resolve_legacy_path(".plt", "pltout.asc")

    @property
    def plt_binary(self) -> pathlib.Path:
        return self._resolve_legacy_path("_b.plt", "pltout.bin")

    @property
    def psc(self) -> pathlib.Path:
        return self._resolve_legacy_path(".psc", "pltout.scn")

    @property
    def wrn(self) -> pathlib.Path:
        return self._resolve_legacy_path(".wrn", "warnings.txt")

    @property
    def corrk_trans_text(self) -> pathlib.Path:
        return self._resolve_legacy_path(".t_k", "t_kdis.dat")

    @property
    def corrk_trans_binary(self) -> pathlib.Path:
        return self._resolve_legacy_path("_b.t_k", "t_kdis.bin")

    @property
    def corrk_rad_text(self) -> pathlib.Path:
        return self._resolve_legacy_path(".r_k", "r_kdis.dat")

    @property
    def corrk_rad_binary(self) -> pathlib.Path:
        return self._resolve_legacy_path("_b.r_k", "r_kdis.bin")

    def all_files(self, *, only_existing: bool = False) -> list[pathlib.Path]:
        file_properties = [
            getattr(self, name)
            for name, value in self.__class__.__dict__.items()
            if isinstance(value, property)
        ]
        if only_existing:
            file_properties = [f for f in file_properties if f.exists()]

        return file_properties

    def _root_name(self) -> str:
        try:
            return self.file_options["FLROOT"].strip()
        except KeyError:
            pass

        return "mod6" if self.name is None else self.name.strip()

    def _resolve_sli(self, tail: str) -> pathlib.Path:
        try:
            sli_root = self.file_options["SLIPRNT"]
        except KeyError:
            # SLI files not requested. Return sentinel that should fail .exists() checks.
            sli_root = ".SLIPRNT_NOT_SET"
        return self.work_dir.joinpath(f"{sli_root}{tail}")

    def _resolved_csv(self, tail: str) -> pathlib.Path:
        try:
            csv_root = self.file_options["CSVPRNT"]
        except KeyError:
            # CSV file not requested. Return sentinel that should fail .exists() checks.
            csv_root = ".CSVPRNT_NOT_SET"

        path = self.work_dir.joinpath(csv_root)
        path = path.with_stem(f"{path.stem}{tail}")

        # Add .txt suffix only if no suffix is present.
        if path.suffix == "":
            path = path.with_suffix(".txt")
        return path

    def _resolve_legacy_path(self, tail: str, blank_name: str) -> pathlib.Path:
        """
        Resolve filename of legacy output file.
        """
        # <ROOT NAME> = FILEOPTIONS.FLROOT if set (even if blank).
        # If FILEOPTIONS.FLROOT is not set, NAME is used instead.
        #
        # If <ROOT NAME> is blank (meaning FILEOPTIONS.FLROOT or NAME is set per the above and contains only spaces),
        # then default legacy filenames are used. If <ROOT NAME> is unset, (meaining neither FILEOPTIONS.FLROOT or NAME
        # were set, then <ROOT NAME> = "mod6".

        if (root := self._root_name()) != "":
            name = f"{root}{tail}"
        else:
            name = blank_name

        return self.work_dir.joinpath(name)

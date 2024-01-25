from __future__ import annotations

import contextlib
import pathlib
import struct
from dataclasses import dataclass
from typing import Any, BinaryIO, ContextManager, Sequence, TextIO, cast, overload

import numpy as np

from . import _util
from .input import FileOptions, JSONInput

_AtmoCorrectDataDType = np.dtype(
    [
        ("freq", "<f4"),
        ("los", "<i4"),
        ("k_int", "<i4"),
        ("k_weight", "<f4"),
        ("sun_gnd_diffuse_transm", "<f4"),
        ("sun_gnd_obs_direct_transm", "<f4"),
        ("obs_gdn_embedded_dif_transm", "<f4"),
        ("obs_gnd_direct_transm", "<f4"),
        ("spherical_albedo", "<f4"),
    ]
)

_AtmoCorrectDataFileDtype = np.dtype(
    [
        ("_delim1", "<i4"),
        ("data", _AtmoCorrectDataDType),
        ("_delim2", "<i4"),
    ]
)


def read_acd_text(
    file: pathlib.Path | TextIO, *, dtype: npt.DTypeLike = _AtmoCorrectDataDType
) -> np.ndarray[Any, Any]:
    return np.loadtxt(file, skiprows=5, dtype=dtype)


def read_acd_binary(
    file: str | pathlib.Path | BinaryIO, *, check: bool = False
) -> np.ndarray[Any, Any]:
    # TODO handle multiple cases in one file?
    cm: ContextManager[BinaryIO]
    if _util.is_binary_io(file):
        cm = contextlib.nullcontext(file)
    else:
        cm = open(cast("str | pathlib.Path", file), "rb")

    with cm as fd:
        buffer = fd.read()

    contents = np.frombuffer(
        buffer,
        offset=_AtmoCorrectDataFileDtype.itemsize,
        dtype=_AtmoCorrectDataFileDtype,
    )

    # Run optional sanity checks.
    if check:
        # Check header row contents.
        expected_header = struct.pack(
            "ifiiiiiiiii", ord("$"), -9999.0, 0, 1, 0, 0, 0, 0, 0, 0, ord("$")
        )
        if buffer[: _AtmoCorrectDataFileDtype.itemsize] != expected_header:
            raise ValueError(
                f"invalid header: expected '{expected_header.hex()}',"
                f" got '{buffer[: _AtmoCorrectDataFileDtype.itemsize].hex()}'"
            )

        # Check start and end word of every row.
        delim_words = set(contents["_delim1"]) | set(contents["_delim2"])
        if unexpected_delims := delim_words - {ord("$")}:
            raise ValueError(
                f"got unexpected word(s) in delimiter columns: {unexpected_delims}"
            )

    return contents["data"]


@dataclass
class _ModtranOutputFiles(Sequence["_CaseResultFilesNavigator"]):
    """
    Collection of output files from a MODTRAN run, organized by case.

    Output file paths are resolved lazily.
    """

    input: JSONInput
    work_dir: pathlib.Path

    # TODO: interface for collecting output files "post mortem" / directly from disk.

    @overload
    def __getitem__(self, case_index: int, /) -> _CaseResultFilesNavigator:
        ...

    @overload
    def __getitem__(self, case_index: slice, /) -> Sequence[_CaseResultFilesNavigator]:
        ...

    def __getitem__(
        self, case_index: int | slice, /
    ) -> _CaseResultFilesNavigator | Sequence[_CaseResultFilesNavigator]:
        if isinstance(case_index, slice):
            # https://docs.python.org/3/reference/datamodel.html#slice.indices
            return [self[idx] for idx in range(*case_index.indices(len(self)))]

        # TODO: fallback to case listed in 'CASE TEMPLATE' on lookup fail?
        case = self.input["MODTRAN"][case_index]
        return _CaseResultFilesNavigator(
            self.work_dir,
            case["MODTRANINPUT"]["FILEOPTIONS"],
            case["MODTRANINPUT"].get("NAME"),
        )

    def __len__(self) -> int:
        return len(self.input["MODTRAN"])


@dataclass
class _CaseResultFilesNavigator:
    """
    Index into available result files for a single case.

    Not all files will exist, depending on execution options.

    WARNING: Some files may contain results for multiple cases
    (e.g. '.csv', '.acd', ...) if the same options are used in multiple cases.

    SLI files will have numeric suffixes added if multiple cases use the same
    SLIPRNT, which this class does not account for.
    """

    work_dir: pathlib.Path
    file_options: FileOptions
    name: str | None

    @property
    def json(self) -> pathlib.Path:
        path = self.work_dir.joinpath(self.file_options["JSONPRNT"])
        # Always replaces last suffix with .json
        return path.with_suffix(".json")

    @property
    def sli_header(self) -> pathlib.Path:
        return self._sli_appended(".hdr")

    @property
    def sli_data(self) -> pathlib.Path:
        return self._sli_appended(".sli")

    @property
    def sli_flux_header(self) -> pathlib.Path:
        return self._sli_appended("_flux.hdr")

    @property
    def sli_flux_data(self) -> pathlib.Path:
        return self._sli_appended("_flux.sli")

    @property
    def csv_txt(self) -> pathlib.Path:
        try:
            csv_root = self.file_options["CSVPRNT"]
        except KeyError:
            # CSV file not requested. Return sentinel that should file .exists() checks.
            csv_root = ".CSVPRNT_NOT_SET"

        path = self.work_dir.joinpath(csv_root)
        # Add .txt suffix only if no suffix is present.
        if path.suffix == "":
            path = path.with_suffix(".txt")
        return path

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

    def _sli_appended(self, tail: str) -> pathlib.Path:
        try:
            sli_root = self.file_options["SLIPRNT"]
        except KeyError:
            # SLI files not requested. Return sentinel that should file .exists() checks.
            sli_root = ".SLIPRNT_NOT_SET"
        return self.work_dir.joinpath(f"{sli_root}{tail}")

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

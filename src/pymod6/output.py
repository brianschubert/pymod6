"""
Utilities for navigating output file placement in the filesystem.
"""


from __future__ import annotations

import pathlib
from collections.abc import Sequence
from dataclasses import dataclass
from typing import overload

from typing_extensions import Self

import pymod6.io
from pymod6.input import schema as _schema


class ModtranOutputFiles(Sequence["CaseResultFilesNavigator"]):
    """
    Collection of output files from a MODTRAN run, organized by case.

    Output file paths are resolved lazily.
    """

    input_json: _schema.JSONInput
    """
    JSON input file used to generate these outputs.
    """

    work_dir: pathlib.Path
    """
    Base directory for output files.
    """

    def __init__(
        self, input_json: _schema.JSONInput, work_dir: str | pathlib.Path
    ) -> None:
        self.input_json = input_json
        self.work_dir = pathlib.Path(work_dir)

    @classmethod
    def load(
        cls,
        input_file: str | pathlib.Path,
        work_dir: str | pathlib.Path,
        validate_json: bool = True,
    ) -> Self:
        """
        Load output files that were produced by the given input file.

        Parameters
        ----------
        input_file : path-like
            Path to input file
        work_dir : path-like
            Working directory containing the output files.
        validate_json : bool, optional
            Whether to validate the JSON files against the expected schema. Defaults to `True`.
            Set to `False` if for whatever reason the expected schema deviates from the file
            contents, and you still wish to attempt to load the JSON files.

        Returns
        -------
        Self
            Case output file collection for the given input file.
        """
        input_dict = pymod6.io.read_json_input(
            pathlib.Path(input_file).read_text(), validate=validate_json
        )
        return cls(input_dict, work_dir)

    @classmethod
    def load_directory(
        cls, directory: str | pathlib.Path, validate_json: bool = True
    ) -> Self:
        """
        Load directory of case outputs.

        The directory must either contain a single `.json` file with all case inputs,
        or it must contain a separate `.json` file for each case. All cases must
        include a `MODTRANINPUT` entry.

        If the directory contains a single `.json` file, then the order of the loaded
        cases will match the order of the cases in the JSON file. If the directory
        contains multiple `.json` files, then the loaded cases will be ordered
        lexicographically by corresponding JSON file name.

        Parameters
        ----------
        directory : path-like
            Directory containing output files.

        validate_json : bool, optional
            Whether to validate the JSON files against the expected schema. Defaults to `True`.
            Set to `False` if for whatever reason the expected schema deviates from the file
            contents, and you still wish to attempt to load the JSON files.

        Returns
        -------
        Self
            Case output file collection for the given directory.

        Examples
        --------
        ```python
        work_dir = "some/work/directory"

        mod_exec = pymod6.ModtranExecutable()
        mod_exec.run(..., work_dir=work_dir)

        # later...

        output_files = ModtranOutputFiles.load_directory(work_dir)
        ```
        """

        directory = pathlib.Path(directory)
        json_files = sorted(f for f in directory.iterdir() if f.suffix == ".json")

        if not json_files:
            raise ValueError(f"directory contains no JSON files: '{directory}'")

        all_cases: list[_schema.Case] = []
        for case_json in json_files:
            try:
                case_input_dict = pymod6.io.read_json_input(
                    case_json.read_text(), validate=validate_json
                )
            except ValueError as ex:
                raise ValueError(f"failed to load output JSON: {case_json}") from ex

            if len(json_files) != 1 and len(case_input_dict["MODTRAN"]) != 1:
                raise ValueError(
                    f"directory contains multiple JSON files. Expected exactly 1 case per file,"
                    f" but found {len(case_input_dict['MODTRAN'])} cases in '{case_json}'"
                )

            for case_idx, case in enumerate(case_input_dict["MODTRAN"]):
                if "MODTRANINPUT" not in case:
                    raise ValueError(
                        f"case {case_idx} missing MODTRANINPUT: {case_json}"
                    )

                all_cases.append(case)

        return cls({"MODTRAN": all_cases}, directory)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(<{len(self)} cases from '{self.work_dir}'>)"

    def __len__(self) -> int:
        return len(self.input_json["MODTRAN"])

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
        case = self.input_json["MODTRAN"][case_index]
        return CaseResultFilesNavigator(
            self.work_dir,
            case["MODTRANINPUT"].get("FILEOPTIONS", {}),
            case["MODTRANINPUT"].get("NAME"),
        )


@dataclass
class CaseResultFilesNavigator:
    """
    Index into available result files for a single case.

    This class inspects the `"FILEOPTIONS"` from a MODTRAN run to determine the
    locations of various output files.

    Not all files will exist, depending on execution options. You can use the
    [`exists`](https://docs.python.org/3/library/pathlib.html#pathlib.Path.exists)
    or
    [`is_file`](https://docs.python.org/3/library/pathlib.html#pathlib.Path.is_file)
    methods on the `Path` objects to check for file existence.

    .. warning::
        Some files may contain results for multiple cases (e.g. '.csv', '.acd', ...)
        if the same options are used in multiple cases.

    .. warning::
        SLI files will have numeric suffixes added if multiple cases use the same SLIPRNT,
         which this class does not account for.
    """

    work_dir: pathlib.Path
    file_options: _schema.FileOptions
    name: str | None

    @property
    def json(self) -> pathlib.Path:
        # If JSON file not requested, return sentinel that should fail .exists() checks.
        path = self.work_dir.joinpath(
            self.file_options.get("JSONPRNT", ".JSONPRNT_NOT_SET")
        )
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
        # <ROOT NAME> = FILEOPTIONS.FLROOT if set (even if blank).
        # If FILEOPTIONS.FLROOT is not set, NAME is used instead.
        #
        # If <ROOT NAME> is blank (meaning FILEOPTIONS.FLROOT or NAME is set per the above and contains only spaces),
        # then default legacy filenames are used. If <ROOT NAME> is unset, (meaining neither FILEOPTIONS.FLROOT or NAME
        # were set, then <ROOT NAME> = "mod6".
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
        if (root := self._root_name()) != "":
            name = f"{root}{tail}"
        else:
            name = blank_name

        return self.work_dir.joinpath(name)

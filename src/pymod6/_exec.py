from __future__ import annotations

import concurrent.futures
import json
import math
import os
import pathlib
import subprocess
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass
from typing import NamedTuple, cast, overload

from pymod6._env import ModtranEnv
from pymod6.input import FileOptions, JSONInput


class _ModtranResult(NamedTuple):
    process: subprocess.CompletedProcess[str]
    cases_output_files: _ModtranOutputFiles


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


class ModtranExecutable:
    _env: ModtranEnv

    def __init__(self, *, env: ModtranEnv | None = None) -> None:
        if env is None:
            env = ModtranEnv.from_environ()
        self._env = env

    def license_status(self) -> str:
        result = subprocess.run(
            [self._env.exe, "-license_status"],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()

    def version(self) -> str:
        result = subprocess.run(
            [self._env.exe, "-version"],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()

    def run(
        self,
        input_file: JSONInput,
        *,
        work_dir: pathlib.Path | None = None,
    ) -> _ModtranResult:
        # TODO: should there be any treatment (different output type, warnings, etc) for output files that are
        #  written to by multiple cases?

        if work_dir is None:
            work_dir = pathlib.Path.cwd()

        with tempfile.NamedTemporaryFile("w") as temp_file:
            json.dump(input_file, temp_file)
            temp_file.flush()

            result = subprocess.run(
                [self._env.exe, temp_file.name],
                env=self._env.to_environ(),
                cwd=work_dir,
                capture_output=True,
                text=True,
            )

        return _ModtranResult(result, _ModtranOutputFiles(input_file, work_dir))

    def run_parallel(
        self,
        input_files: Sequence[JSONInput],
        *,
        work_dir: pathlib.Path | None = None,
        max_workers: int | None = None,
    ) -> list[_ModtranResult]:
        if work_dir is None:
            work_dir = pathlib.Path.cwd()

        if max_workers is None:
            # TODO: warning when number of CPUs can not be determined?
            max_workers = min(len(input_files), os.cpu_count() or 16)

        results = [cast(_ModtranResult, None)] * len(input_files)
        num_job_digits = 1 + int(math.log10(len(input_files) - 1))

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures_to_index: dict[concurrent.futures.Future[_ModtranResult], int] = {}
            for idx, curr_file in enumerate(input_files):
                job_work_dir = work_dir.joinpath(f"job{idx:0{num_job_digits}}")
                job_work_dir.mkdir(parents=False, exist_ok=False)
                future = executor.submit(self.run, curr_file, work_dir=job_work_dir)
                futures_to_index[future] = idx

            for future in concurrent.futures.as_completed(futures_to_index):
                idx = futures_to_index[future]
                try:
                    results[idx] = future.result()
                except Exception:
                    # TODO handle?
                    raise

        return results


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

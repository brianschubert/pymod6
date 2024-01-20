from __future__ import annotations

import json
import pathlib
import subprocess
import tempfile
from dataclasses import dataclass

from pymod6._env import ModtranEnv
from pymod6._input import FileOptions, JSONInput


class ModtranExecutable:
    _env: ModtranEnv
    _work_dir: pathlib.Path

    def __init__(
        self, *, env: ModtranEnv | None = None, work_dir: pathlib.Path | None = None
    ) -> None:
        if env is None:
            env = ModtranEnv.from_environ()

        if work_dir is None:
            work_dir = pathlib.Path.cwd()

        self._env = env
        self._work_dir = work_dir

    def license_status(self) -> str:
        result = subprocess.run(
            [self._env.exe, "-license_status"],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()

    def run_single_case(
        self, input_file: JSONInput
    ) -> tuple[subprocess.CompletedProcess, _ResultFiles]:
        if (num_cases := len(input_file["MODTRAN"])) != 1:
            raise ValueError(
                f"input file must include exactly on case, got {num_cases}"
            )

        with tempfile.NamedTemporaryFile("w") as temp_file:
            json.dump(input_file, temp_file)
            temp_file.flush()

            result = subprocess.run(
                [self._env.exe, temp_file.name],
                env=self._env.to_environ(),
                cwd=self._work_dir,
                capture_output=True,
                text=True,
            )

        return result, _ResultFiles(
            self._work_dir, input_file["MODTRAN"][0]["MODTRANINPUT"]["FILEOPTIONS"]
        )


@dataclass
class _ResultFiles:
    """
    Index into available result files.

    Not all files will exist, depending on execution options.

    Some files may contain results for multiple cases (e.g. '.csv', '.acd', ...) if
    the same options are used.

    SLI files will have numeric suffixes added if multiple cases use the same SLIPRNT,
    which this class does not account for.
    """

    working_dir: pathlib.Path
    file_options: FileOptions

    @property
    def json(self) -> pathlib.Path:
        path = self.working_dir.joinpath(self.file_options["JSONPRNT"])
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
        path = self.working_dir.joinpath(self.file_options["CSVPRNT"])
        # Add .txt suffix only if no suffix is present.
        if path.suffix == "":
            path = path.with_suffix(".txt")
        return path

    @property
    def acd_text(self) -> pathlib.Path:
        return self._flroot_appended(".acd")

    @property
    def acd_binary(self) -> pathlib.Path:
        return self._flroot_appended("_b.acd")

    @property
    def tape7_text(self) -> pathlib.Path:
        return self._flroot_appended(".tp7")

    @property
    def tape7_binary(self) -> pathlib.Path:
        return self._flroot_appended("_b.tp7")

    @property
    def tape6(self) -> pathlib.Path:
        return self._flroot_appended(".tp6")

    @property
    def scan(self) -> pathlib.Path:
        return self._flroot_appended(".7sc")

    @property
    def pth(self) -> pathlib.Path:
        return self._flroot_appended("._pth")

    @property
    def plt_text(self) -> pathlib.Path:
        return self._flroot_appended(".plt")

    @property
    def plt_binary(self) -> pathlib.Path:
        return self._flroot_appended("_b.plt")

    @property
    def psc(self) -> pathlib.Path:
        return self._flroot_appended(".psc")

    @property
    def wrn(self) -> pathlib.Path:
        return self._flroot_appended(".wrn")

    def _flroot_appended(self, tail: str) -> pathlib.Path:
        return self.working_dir.joinpath(f"{self.file_options['FLROOT']}{tail}")

    def _sli_appended(self, tail: str) -> pathlib.Path:
        return self.working_dir.joinpath(f"{self.file_options['SLIPRNT']}{tail}")

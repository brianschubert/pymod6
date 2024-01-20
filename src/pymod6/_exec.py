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
    ) -> tuple[subprocess.CompletedProcess[str], _ResultFiles]:
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

        case_input = input_file["MODTRAN"][0]["MODTRANINPUT"]
        return result, _ResultFiles(
            self._work_dir, case_input["FILEOPTIONS"], case_input.get("NAME")
        )


@dataclass
class _ResultFiles:
    """
    Index into available result files.

    Not all files will exist, depending on execution options.

    Some files may contain results for multiple cases (e.g. '.csv', '.acd', ...) if
    the same options are used in multiple cases.

    SLI files will have numeric suffixes added if multiple cases use the same SLIPRNT,
    which this class does not account for.
    """

    working_dir: pathlib.Path
    file_options: FileOptions
    name: str | None

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

    def _root_name(self) -> str:
        try:
            return self.file_options["FLROOT"].strip()
        except KeyError:
            pass

        return "mod6" if self.name is None else self.name.strip()

    def _sli_appended(self, tail: str) -> pathlib.Path:
        return self.working_dir.joinpath(f"{self.file_options['SLIPRNT']}{tail}")

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

        return self.working_dir.joinpath(name)

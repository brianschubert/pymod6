from __future__ import annotations

import concurrent.futures
import datetime
import json
import os
import pathlib
import subprocess
import tempfile
from collections.abc import Sequence
from typing import NamedTuple, Union, cast

from typing_extensions import TypeAlias

from pymod6 import ModtranEnv
from pymod6.input import JSONInput

from . import _util
from .output import ModtranOutputFiles

_PathLike: TypeAlias = Union[str, os.PathLike[str]]


class ModtranResult(NamedTuple):
    """Result from executing MODTRAN."""

    process: subprocess.CompletedProcess[str]
    """Completed MODTRAN subprocess status."""

    cases_output_files: ModtranOutputFiles
    """
    Collection of  case results (`pymod6.output.CaseResultFilesNavigator`), each
    consisting of paths to result files.
    """


class ModtranExecutable:
    """
    Low-level functional wrapper to MODTRAN's command line interface.
    """

    _env: ModtranEnv

    def __init__(self, *, env: ModtranEnv | None = None) -> None:
        """
        Create a MODTRAN executable for the given MODTRAN environment.

        Parameters
        ---------
        env : ModtranEnv, optional
            MODTRAN environment. Defaults to being detected from the current process'
            environment variables.
        """
        if env is None:
            env = ModtranEnv.from_environ()
        self._env = env

    def license_status(self) -> str:
        """
        Query the license status of the configured MODTRAN executable.

        Returns
        -------
        status : str
            License status string.

        Examples
        --------

        >>> mod_exec = ModtranExecutable()
        >>> mod_exec.license_status()
        'STAT_VALID ...'
        """
        result = subprocess.run(
            [self._env.exe, "-license_status"],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()

    def version(self) -> str:
        """
        Query the version of the configured MODTRAN executable.

        Returns
        -------
        version : str
            Version string.

        Examples
        --------

        >>> mod_exec = ModtranExecutable()
        >>> mod_exec.version()
        'MODTRAN(R) 6.0...'
        """
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
        work_dir: _PathLike | None = None,
    ) -> ModtranResult:
        """
        Run MODTRAN for the given input.

        Parameters
        ----------
        input_file : JSONInput
            Mapping representing a complete MODTRAN input JSON file.

        work_dir : path-like, optional
            Path to the directory MODTRAN should run in. This is the base for all output file paths.
            Defaults to `./modtran_runs/run_<timestamp>/`.

        Returns
        -------
        result : ModtranResult
            Subprocess status and result files.
        """
        # TODO: should there be any treatment (different output type, warnings, etc) for output files that are
        #  written to by multiple cases?

        work_dir = _path_or_default_work_dir(work_dir)

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

        return ModtranResult(result, ModtranOutputFiles(input_file, work_dir))

    def run_parallel(
        self,
        input_files: Sequence[JSONInput],
        *,
        work_dir: _PathLike | None = None,
        max_workers: int | None = None,
    ) -> list[ModtranResult]:
        """
        Run parallel MODTRAN processes for the given input files.

        A separate subdirectory will be created for each run in the
        specified `work_dir`.

        Parameters
        ----------
        input_files : Sequence[JSONInput]
            Sequence of input file mappings.
        work_dir : path-like, optional
            Same as in `run`.
        max_workers : int, optional
            Maximum number of concurrent subprocesses to use.

        Returns
        -------
        results : list[ModtranResult]
            List of MODTRAN run results, in the same order as the input files.
        """
        work_dir = _path_or_default_work_dir(work_dir)

        if max_workers is None:
            # TODO: warning when number of CPUs can not be determined?
            max_workers = min(len(input_files), os.cpu_count() or 16)

        results = [cast(ModtranResult, None)] * len(input_files)
        num_job_digits = _util.num_digits(len(input_files) - 1)

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures_to_index: dict[concurrent.futures.Future[ModtranResult], int] = {}
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


def _path_or_default_work_dir(p: _PathLike | None) -> pathlib.Path:
    if p is None:
        work_dir = (
            pathlib.Path.cwd()
            / "modtran_runs"
            / f"run{datetime.datetime.now().isoformat(timespec='seconds')}"
        )
        work_dir.mkdir(parents=True, exist_ok=False)
        return work_dir

    return pathlib.Path(p)

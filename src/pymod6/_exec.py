from __future__ import annotations

import concurrent.futures
import json
import os
import pathlib
import subprocess
import tempfile
from collections.abc import Sequence
from typing import NamedTuple, cast

from pymod6._env import ModtranEnv
from pymod6._output import _ModtranOutputFiles
from pymod6.input import JSONInput

from . import _util

class _ModtranResult(NamedTuple):
    process: subprocess.CompletedProcess[str]
    cases_output_files: _ModtranOutputFiles


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
        num_job_digits = _util.num_digits(len(input_files) - 1)

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

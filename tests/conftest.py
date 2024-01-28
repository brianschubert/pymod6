from __future__ import annotations

import copy
import pathlib

import pytest

import pymod6
from pymod6 import input as mod_input


@pytest.fixture(scope="session")
def modtran_env() -> pymod6.ModtranEnv:
    try:
        env = pymod6.ModtranEnv.from_environ()
    except ValueError as ex:
        pytest.skip(f"unable to detect MODTRAN environment: {ex}")

    if not env.exe.is_file():
        pytest.fail(f"MODTRAN executable does not exist or is not a file: {env.exe}")

    if not env.data.is_dir():
        pytest.fail(
            f"MODTRAN DATA directory does not exist or is not a directory: {env.exe}"
        )

    return env


@pytest.fixture(scope="session")
def modtran_exec(modtran_env) -> pymod6.ModtranExecutable:
    mod_exec = pymod6.ModtranExecutable(env=modtran_env)

    # Check license is active.
    if not (status := mod_exec.license_status()).startswith("STAT_VALID"):
        pytest.fail(f"MODTRAN license not active: {status}")

    # Check version is compatible.
    version = mod_exec.version().split()[-1]
    if version.split(".")[0] != "6":
        pytest.fail(f"invalid MODTRAN version, expected version 6.*, found {version}")

    return mod_exec


@pytest.fixture(scope="session")
def simple_case() -> mod_input.ModtranInput:
    case: mod_input.ModtranInput = copy.deepcopy(mod_input.basecases.BASE)
    case["SPECTRAL"]["V1"] = 4000
    case["SPECTRAL"]["V2"] = 4001
    return case


@pytest.fixture
def helpers() -> type[_Helpers]:
    return _Helpers


class _Helpers:
    """
    Hack to make helper functions available to tests without fiddling with the
    import path.
    """

    @staticmethod
    def run_single_checked(
        mod_exe: pymod6.ModtranExecutable,
        input_json: mod_input.JSONInput,
        work_dir: pathlib.Path,
    ) -> pymod6.output.CaseResultFilesNavigator:
        """Execute a single-case MODTRAN run. Verify the process exited OK."""
        result = mod_exe.run(input_json, work_dir=work_dir)

        assert result.process.returncode == 0
        assert "Error" not in result.process.stdout
        assert "" == result.process.stderr

        [case_files] = result.cases_output_files
        _assert_all_named(case_files)

        return case_files


def _assert_all_named(case_files: pymod6.output.CaseResultFilesNavigator) -> None:
    """
    Assert that all files in the given case output file directory are named
    by an associated property
    """
    located_files = {f.name for f in case_files.all_files(only_existing=True)}
    actual_files = {f.name for f in case_files.work_dir.iterdir()}

    assert located_files == actual_files

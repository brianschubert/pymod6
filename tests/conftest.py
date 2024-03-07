from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import pymod6

if TYPE_CHECKING:
    import pathlib


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


@pytest.fixture()
def simple_case() -> pymod6.input.schema.CaseInput:
    spectral_inputs = pymod6.input.make_case(
        SPECTRAL__V1=4000.0,
        SPECTRAL__V2=4001.0,
    )
    return pymod6.input.merge_case_parts(
        pymod6.input.basecases.BASE_0,
        spectral_inputs,
    )


@pytest.fixture(scope="session")
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
        input_json: pymod6.input.schema.JSONInput,
        work_dir: pathlib.Path,
    ) -> pymod6.output.CaseResultFilesNavigator:
        """Execute a single-case MODTRAN run. Verify the process exited OK."""
        result = mod_exe.run(input_json, work_dir=work_dir)

        assert result.process.returncode == 0
        assert "Error" not in result.process.stdout
        assert result.process.stderr == ""

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

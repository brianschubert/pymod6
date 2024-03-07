"""
Tests for examples in `<install root>/TEST/JSON`.
"""

import os
import pathlib
import shutil
from typing import TYPE_CHECKING

import pytest

import pymod6

if TYPE_CHECKING:

    @pytest.fixture(scope="module")
    def example_file() -> pathlib.Path:  # noqa: PT004
        ...


@pytest.fixture(scope="module")
def example_json(example_file) -> pymod6.input.schema.JSONInput:
    return pymod6.io.read_json_input(example_file.read_text(), validate=True)


@pytest.fixture(scope="module")
def example_outputs(
    modtran_exec, example_file, example_json, tmp_path_factory
) -> pymod6.output.ModtranOutputFiles:
    if os.environ.get("TEST_EXAMPLES") != "1":
        pytest.skip("set TEST_EXAMPLE=1 in the environment to run examples")

    # TODO diagnosis why this example fails.
    # Suppress for now, since its failure produces massive stdout.
    if example_file.stem == "DISIsaacs":
        pytest.skip(
            "DISIsaacs example consistently errors with"
            " 'Finite spectral bin equivalent width expansion did not converge'"
        )

    # Pre-fail examples that depend on 'DATA/Landsat8.flt' when missing.
    if (
        example_json["MODTRAN"][0]
        .get("MODTRANINPUT", {})
        .get("SPECTRAL", {})
        .get("FILTNM")
        == "DATA/Landsat8.flt"
        and not modtran_exec._env.data.joinpath("DATA/Landsat8.flt").exists()
    ):
        pytest.fail("missing DATA/Landsat8.flt")

    run_dir = tmp_path_factory.mktemp("modtran_run")

    # Copy corresponding .rng file to work dir if it exists.
    rng_file = example_file.with_suffix(".rng")
    if rng_file.exists():
        shutil.copy(rng_file, run_dir)

    # Pre-fail examples that are missing a required .rng file.
    if not rng_file.exists() and any(
        "~" in p.get("UNAME", "")
        for p in example_json["MODTRAN"][0]["MODTRANINPUT"]["ATMOSPHERE"].get(
            "PROFILES", []
        )
    ):
        pytest.fail(
            f"missing .rng file '{rng_file}' despite UNAME with '~' in ATMOSPHERE.PROFILE"
        )

    # Copy corresponding .OUT file to work dir if it exists.
    out_file = example_file.with_suffix(".OUT")
    if out_file.exists():
        shutil.copy(out_file, run_dir)

    # Run example.
    result = modtran_exec.run(example_json, work_dir=run_dir)
    assert result.process.returncode == 0
    assert "Error" not in result.process.stdout
    assert result.process.stderr == ""

    return result.cases_output_files


def test_read(example_json) -> None:
    assert example_json.keys() == {"MODTRAN"}
    assert len(example_json["MODTRAN"]) > 0


def test_generate_same_output_files(
    example_file, example_outputs, example_json
) -> None:
    # Located expected output files.
    expected_output_dir = example_file.parent.joinpath("COMPARE")
    expected_case_files = pymod6.output.ModtranOutputFiles(
        example_json, expected_output_dir
    )

    assert len(expected_case_files) == len(example_outputs)

    for exp_case, act_case in zip(expected_case_files, example_outputs):
        exp_names = {p.name for p in exp_case.all_files(only_existing=True)}
        act_names = {p.name for p in act_case.all_files(only_existing=True)}

        assert exp_names == act_names


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if "example_file" in metafunc.fixturenames:
        try:
            metafunc.parametrize(
                "example_file",
                _find_example_files(),
                ids=lambda p: p.stem,
                scope="module",
            )
        except (ValueError, RuntimeError) as ex:
            pytest.mark.skip(f"unable to find example files: {ex}")(metafunc.function)


def _find_example_files() -> list[pathlib.Path]:
    install_root = pymod6.ModtranEnv.from_environ().data.resolve().parent

    candidates = ("TEST", "TestCases")

    for directory in candidates:
        test_root = install_root / directory / "JSON"
        if test_root.exists():
            example_files = list(test_root.glob("*.json"))
            if not example_files:
                raise RuntimeError(f"found no example files in '{test_root}'")
            return example_files
    raise RuntimeError(f"unable to locate examples directory in '{install_root}'")

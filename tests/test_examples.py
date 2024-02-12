"""
Tests for examples in `<install root>/TEST/JSON`.
"""
import pathlib

import pytest

import pymod6


def test_read(example_file):
    pymod6.io.read_json_input(example_file.read_text())


def pytest_generate_tests(metafunc):
    if "example_file" in metafunc.fixturenames:
        try:
            metafunc.parametrize(
                "example_file", _find_example_files(), ids=lambda p: p.stem
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
    else:
        raise RuntimeError(f"unable to locate examples directory in '{install_root}'")

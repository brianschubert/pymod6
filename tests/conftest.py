import copy

import pytest

import pymod6
from pymod6 import input as mod_input


@pytest.fixture(scope="session")
def modtran_env() -> pymod6.ModtranEnv:
    try:
        return pymod6.ModtranEnv.from_environ()
    except ValueError as ex:
        pytest.skip(f"unable to detecte MODTRAN environment: {ex}")


@pytest.fixture(scope="session")
def modtran_exec(modtran_env) -> pymod6.ModtranExecutable:
    mod_exec = pymod6.ModtranExecutable(env=modtran_env)

    # Check license is active.
    if not (status := mod_exec.license_status()).startswith("STAT_VALID"):
        pytest.skip(f"MODTRAN license not active: {status}")

    # Check version is compatible.
    version = mod_exec.version().split()[-1]
    if version.split(".")[0] != "6":
        pytest.skip(f"invalid MODTRAN version, expected version 6.*, found {version}")

    return mod_exec


@pytest.fixture(scope="session")
def simple_case() -> mod_input.ModtranInput:
    case: mod_input.ModtranInput = copy.deepcopy(mod_input.basecases.BASE)
    case["SPECTRAL"]["V1"] = 4000
    case["SPECTRAL"]["V2"] = 4001
    return case

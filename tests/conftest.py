import pytest

import pymod6._env
import pymod6._exec


@pytest.fixture(scope="session")
def modtran_env() -> pymod6._env.ModtranEnv:
    try:
        return pymod6._env.ModtranEnv.from_environ()
    except ValueError as ex:
        pytest.skip(f"unable to detecte MODTRAN environment: {ex}")


@pytest.fixture(scope="session")
def modtran_exec(modtran_env) -> pymod6._exec.ModtranExecutable:
    mod_exec = pymod6._exec.ModtranExecutable(env=modtran_env)
    if (
        status := mod_exec.license_status()
    ) != "STAT_VALID MODTRAN license is activated.":
        pytest.skip(f"MODTRAN license not active: {status}")

    return mod_exec

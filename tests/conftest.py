import pathlib
import tempfile

import pytest

import pymod6._env
import pymod6._exec


@pytest.fixture(scope="session")
def modtran_env() -> pymod6._env.ModtranEnv:
    try:
        return pymod6._env.ModtranEnv.from_environ()
    except ValueError as ex:
        pytest.skip(f"unable to detecte MODTRAN environment: {ex}")


@pytest.fixture()
def modtran_exec(modtran_env) -> pymod6._exec.ModtranExecutable:
    with tempfile.TemporaryDirectory() as temp_dir:
        yield pymod6._exec.ModtranExecutable(
            env=modtran_env,
            work_dir=pathlib.Path(temp_dir),
        )

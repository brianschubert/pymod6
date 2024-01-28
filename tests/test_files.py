"""
Tests for the existence and placement of output files.

Note: this module should be named such that it runs before other test modules.
That way, failures due to missing output files are obvious and visible.
"""
import pathlib

import pytest

import pymod6
import pymod6.input as mod_input
import pymod6.io
import pymod6.output


@pytest.fixture(params=[False, True], ids=lambda flag: f"use_corrk={flag}")
def use_corrk(request) -> bool:
    return request.param


@pytest.mark.parametrize("json_opt", list(mod_input.JSONPrintOpt))
def test_files_exist_json(modtran_exec, tmp_path, json_opt, simple_case) -> None:
    input_json = (
        mod_input.ModtranInputBuilder()
        .add_case(simple_case)
        .finish_case()
        .build_json_input(json_opt=json_opt)
    )

    case_files = _run_single_checked(modtran_exec, input_json, tmp_path)
    file_names = [f.name for f in case_files.all_files(only_existing=True)]

    if json_opt == mod_input.JSONPrintOpt.WRT_NONE:
        assert file_names == []
    else:
        assert file_names == ["case0.json"]

        output_json = pymod6.io.read_json_input(case_files.json.read_text())
        [case] = output_json["MODTRAN"]

        assert (
            "MODTRANSTATUS" in case,
            "MODTRANINPUT" in case,
            "MODTRANOUTPUT" in case,
        ) == (
            mod_input.JSONPrintOpt.WRT_STATUS in json_opt,
            mod_input.JSONPrintOpt.WRT_INPUT in json_opt,
            mod_input.JSONPrintOpt.WRT_OUTPUT in json_opt,
        )


@pytest.mark.parametrize("binary", [False, True], ids=lambda flag: f"binary={flag}")
def test_files_exist_legacy(
    modtran_exec, tmp_path, simple_case, binary, use_corrk
) -> None:
    input_json = (
        mod_input.ModtranInputBuilder()
        .add_case(
            simple_case,
            RTOPTIONS__MODTRN=mod_input.RTAlgorithm.RT_CORRK_FAST,
        )
        .finish_case()
        .build_json_input(
            output_legacy=True,
            binary=binary,
            outupt_corrk=use_corrk,
            json_opt=mod_input.JSONPrintOpt.WRT_NONE,
        )
    )

    case_files = _run_single_checked(modtran_exec, input_json, tmp_path)

    actual_files = {f.name for f in case_files.all_files(only_existing=True)}
    expected_files = {
        "case0.7sc",
        "case0._pth",
        "case0.psc",
        "case0.tp6",
        "case0.tp7",
        "case0.wrn",
    }
    if binary:
        expected_files |= {
            "case0_b.acd",
            "case0_b.plt",
            "case0_b.tp7",
        }
        if use_corrk:
            expected_files |= {
                "case0_b.t_k",
                "case0_b.r_k",
            }
    else:
        expected_files |= {
            "case0.acd",
            "case0.plt",
        }
        if use_corrk:
            expected_files |= {
                "case0.t_k",
                "case0.r_k",
            }

    assert actual_files == expected_files


def test_files_exist_sli(modtran_exec, tmp_path, simple_case, use_corrk) -> None:
    input_json = (
        mod_input.ModtranInputBuilder()
        .add_case(
            simple_case,
            RTOPTIONS__MODTRN=mod_input.RTAlgorithm.RT_CORRK_FAST,
        )
        .finish_case()
        .build_json_input(
            output_sli=True,
            outupt_corrk=use_corrk,
            json_opt=mod_input.JSONPrintOpt.WRT_NONE,
        )
    )

    case_files = _run_single_checked(modtran_exec, input_json, tmp_path)

    actual_files = {f.name for f in case_files.all_files(only_existing=True)}
    expected_files = {
        "case0.hdr",
        "case0.sli",
        "case0_flux.hdr",
        "case0_flux.sli",
        "case0_scan.hdr",
        "case0_scan.sli",
    }
    if use_corrk:
        expected_files |= {
            "case0_highres.hdr",
            "case0_highres.sli",
        }

    assert actual_files == expected_files


def test_files_exist_csv(modtran_exec, tmp_path, simple_case, use_corrk) -> None:
    input_json = (
        mod_input.ModtranInputBuilder()
        .add_case(
            simple_case,
            RTOPTIONS__MODTRN=mod_input.RTAlgorithm.RT_CORRK_FAST,
        )
        .finish_case()
        .build_json_input(
            output_csv=True,
            outupt_corrk=use_corrk,
            json_opt=mod_input.JSONPrintOpt.WRT_NONE,
        )
    )

    case_files = _run_single_checked(modtran_exec, input_json, tmp_path)

    actual_files = {f.name for f in case_files.all_files(only_existing=True)}
    expected_files = {"case0.csv", "case0_flux.csv", "case0_scan.csv"}
    if use_corrk:
        expected_files |= {"case0_highres.csv"}

    assert actual_files == expected_files


def _run_single_checked(
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

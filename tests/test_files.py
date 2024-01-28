"""
Tests for the existence and placement of output files.

Note: this module should be named such that it runs before other test modules.
That way, failures due to missing output files are obvious and visible.
"""

import pytest

import pymod6
import pymod6.input as mod_input
import pymod6.io
import pymod6.output


def test_files_exist_legacy_text(modtran_exec, tmp_path, simple_case) -> None:
    input_json = (
        mod_input.ModtranInputBuilder()
        .add_case(simple_case)
        .finish_case()
        .build_json_input(output_legacy=True, json_opt=mod_input.JSONPrintOpt.WRT_NONE)
    )

    case_files: pymod6.output.CaseResultFilesNavigator
    result_proc, [case_files] = modtran_exec.run(input_json, work_dir=tmp_path)

    assert result_proc.returncode == 0
    assert "Error" not in result_proc.stdout

    assert [f.name for f in case_files.all_files(only_existing=True)] == [
        "case0.acd",
        "case0.tp7",
        "case0.tp6",
        "case0.7sc",
        "case0._pth",
        "case0.plt",
        "case0.psc",
        # "case0.wrn",
    ]


def test_files_exist_legacy_binary(modtran_exec, tmp_path, simple_case) -> None:
    input_json = (
        mod_input.ModtranInputBuilder()
        .add_case(simple_case)
        .finish_case()
        .build_json_input(
            output_legacy=True, binary=True, json_opt=mod_input.JSONPrintOpt.WRT_NONE
        )
    )

    case_files: pymod6.output.CaseResultFilesNavigator
    result_proc, [case_files] = modtran_exec.run(input_json, work_dir=tmp_path)

    assert result_proc.returncode == 0
    assert "Error" not in result_proc.stdout

    assert [f.name for f in case_files.all_files(only_existing=True)] == [
        "case0_b.acd",
        "case0.tp7",
        "case0_b.tp7",
        "case0.tp6",
        "case0.7sc",
        "case0._pth",
        "case0_b.plt",
        "case0.psc",
        # "case0.wrn",
    ]


def test_files_exist_sli(modtran_exec, tmp_path, simple_case) -> None:
    input_json = (
        mod_input.ModtranInputBuilder()
        .add_case(simple_case)
        .finish_case()
        .build_json_input(output_sli=True, json_opt=mod_input.JSONPrintOpt.WRT_NONE)
    )

    case_files: pymod6.output.CaseResultFilesNavigator
    result_proc, [case_files] = modtran_exec.run(input_json, work_dir=tmp_path)

    assert result_proc.returncode == 0
    assert "Error" not in result_proc.stdout

    assert [f.name for f in case_files.all_files(only_existing=True)] == [
        "case0.hdr",
        "case0.sli",
        "case0_flux.hdr",
        "case0_flux.sli",
    ]


def test_files_exist_csv(modtran_exec, tmp_path, simple_case) -> None:
    input_json = (
        mod_input.ModtranInputBuilder()
        .add_case(simple_case)
        .finish_case()
        .build_json_input(output_csv=True, json_opt=mod_input.JSONPrintOpt.WRT_NONE)
    )

    case_files: pymod6.output.CaseResultFilesNavigator
    result_proc, [case_files] = modtran_exec.run(input_json, work_dir=tmp_path)

    assert result_proc.returncode == 0
    assert "Error" not in result_proc.stdout

    assert [f.name for f in case_files.all_files(only_existing=True)] == [
        "case0.csv",
    ]


@pytest.mark.parametrize("json_opt", list(mod_input.JSONPrintOpt))
def test_files_exist_json(modtran_exec, tmp_path, json_opt, simple_case) -> None:
    input_json = (
        mod_input.ModtranInputBuilder()
        .add_case(simple_case)
        .finish_case()
        .build_json_input(json_opt=json_opt)
    )

    case_files: pymod6.output.CaseResultFilesNavigator
    result_proc, [case_files] = modtran_exec.run(input_json, work_dir=tmp_path)

    assert result_proc.returncode == 0
    assert "Error" not in result_proc.stdout

    output_files = [f.name for f in case_files.all_files(only_existing=True)]

    if json_opt == mod_input.JSONPrintOpt.WRT_NONE:
        assert output_files == []
    else:
        assert output_files == ["case0.json"]

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

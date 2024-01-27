import copy

import numpy as np
import pytest

import pymod6._exec
import pymod6.input as mod_input
import pymod6.output


@pytest.fixture(scope="session")
def simple_case() -> mod_input.ModtranInput:
    case: mod_input.ModtranInput = copy.deepcopy(mod_input.basecases.BASE)
    case["SPECTRAL"]["V1"] = 4000
    case["SPECTRAL"]["V2"] = 4001
    return case


def test_files_exist_legacy_text(modtran_exec, tmp_path, simple_case) -> None:
    input_json = (
        mod_input.ModtranInputBuilder()
        .add_case(simple_case)
        .finish_case()
        .build_json_input(output_legacy=True, json_opt=mod_input.JSONPrintOpt.WRT_NONE)
    )

    case_files: pymod6.output._nav.CaseResultFilesNavigator
    result_proc, [case_files] = modtran_exec.run(input_json, work_dir=tmp_path)

    assert result_proc.returncode == 0

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

    case_files: pymod6.output._nav.CaseResultFilesNavigator
    result_proc, [case_files] = modtran_exec.run(input_json, work_dir=tmp_path)

    assert result_proc.returncode == 0

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

    case_files: pymod6.output._nav.CaseResultFilesNavigator
    result_proc, [case_files] = modtran_exec.run(input_json, work_dir=tmp_path)

    assert result_proc.returncode == 0

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

    case_files: pymod6.output._nav.CaseResultFilesNavigator
    result_proc, [case_files] = modtran_exec.run(input_json, work_dir=tmp_path)

    assert result_proc.returncode == 0

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

    case_files: pymod6.output._nav.CaseResultFilesNavigator
    result_proc, [case_files] = modtran_exec.run(input_json, work_dir=tmp_path)

    assert result_proc.returncode == 0

    output_files = [f.name for f in case_files.all_files(only_existing=True)]

    if json_opt == mod_input.JSONPrintOpt.WRT_NONE:
        assert output_files == []
    else:
        assert output_files == ["case0.json"]

        output_json = mod_input.read_json_input(case_files.json.read_text())
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


@pytest.mark.parametrize("algo", list(mod_input.RTAlgorithm))
def test_acd_text_binary_match(modtran_exec, tmp_path, algo, simple_case) -> None:
    input_acd_text = (
        mod_input.ModtranInputBuilder()
        .add_case(simple_case, RTOPTIONS__MODTRN=algo)
        .finish_case()
        .build_json_input(output_legacy=True, binary=False)
    )
    input_acd_binary = (
        mod_input.ModtranInputBuilder()
        .add_case(simple_case, RTOPTIONS__MODTRN=algo)
        .finish_case()
        .build_json_input(output_legacy=True, binary=True)
    )

    acd_text = pymod6.output.read_acd_text(
        modtran_exec.run(input_acd_text, work_dir=tmp_path)
        .cases_output_files[0]
        .acd_text,
    )

    acd_binary = pymod6.output.read_acd_binary(
        modtran_exec.run(input_acd_binary, work_dir=tmp_path)
        .cases_output_files[0]
        .acd_binary
    )

    for field_name in acd_binary.dtype.names:
        np.testing.assert_allclose(
            acd_text[field_name], acd_binary[field_name], atol=5e-6, rtol=1e-6
        )

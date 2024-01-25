import numpy as np

import pymod6._exec
import pymod6._output
import pymod6.input as mod_input


def test_files_exist_legacy_text(modtran_exec, tmp_path) -> None:
    input_json = (
        mod_input.ModtranInputBuilder()
        .add_case(mod_input.basecases.VNIR)
        .finish_case()
        .build_json_input(output_legacy=True)
    )

    case_files: pymod6._output._CaseResultFilesNavigator
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
        "case0.wrn",
    ]


def test_files_exist_legacy_binary(modtran_exec, tmp_path) -> None:
    input_json = (
        mod_input.ModtranInputBuilder()
        .add_case(mod_input.basecases.VNIR)
        .finish_case()
        .build_json_input(output_legacy=True, binary=True)
    )

    case_files: pymod6._output._CaseResultFilesNavigator
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
        "case0.wrn",
    ]


def test_files_exist_sli(modtran_exec, tmp_path) -> None:
    input_json = (
        mod_input.ModtranInputBuilder()
        .add_case(mod_input.basecases.VNIR)
        .finish_case()
        .build_json_input(output_sli=True)
    )

    case_files: pymod6._output._CaseResultFilesNavigator
    result_proc, [case_files] = modtran_exec.run(input_json, work_dir=tmp_path)

    assert result_proc.returncode == 0

    assert [f.name for f in case_files.all_files(only_existing=True)] == [
        "case0.hdr",
        "case0.sli",
        "case0_flux.hdr",
        "case0_flux.sli",
    ]


def test_files_exist_csv(modtran_exec, tmp_path) -> None:
    input_json = (
        mod_input.ModtranInputBuilder()
        .add_case(mod_input.basecases.VNIR)
        .finish_case()
        .build_json_input(output_csv=True)
    )

    case_files: pymod6._output._CaseResultFilesNavigator
    result_proc, [case_files] = modtran_exec.run(input_json, work_dir=tmp_path)

    assert result_proc.returncode == 0

    assert [f.name for f in case_files.all_files(only_existing=True)] == [
        "case0.csv",
    ]


def test_files_exist_json(modtran_exec, tmp_path) -> None:
    for json_opt in mod_input.JSONPrintOpt:
        input_json = (
            mod_input.ModtranInputBuilder()
            .add_case(mod_input.basecases.VNIR)
            .finish_case()
            .build_json_input(json_opt=json_opt)
        )

        case_files: pymod6._output._CaseResultFilesNavigator
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


def test_acd_text_binary_match(modtran_exec, tmp_path) -> None:
    input_acd_text = (
        mod_input.ModtranInputBuilder()
        .add_case(mod_input.basecases.VNIR)
        .finish_case()
        .build_json_input(output_legacy=True, binary=False)
    )
    input_acd_binary = (
        mod_input.ModtranInputBuilder()
        .add_case(mod_input.basecases.VNIR)
        .finish_case()
        .build_json_input(output_legacy=True, binary=True)
    )

    acd_text = pymod6._output.read_acd_text(
        modtran_exec.run(input_acd_text, work_dir=tmp_path)
        .cases_output_files[0]
        .acd_text,
    )

    acd_binary = pymod6._output.read_acd_binary(
        modtran_exec.run(input_acd_binary, work_dir=tmp_path)
        .cases_output_files[0]
        .acd_binary,
        check=True,
    )

    for field_name in acd_binary.dtype.names:
        np.testing.assert_allclose(
            acd_text[field_name], acd_binary[field_name], atol=5e-6, rtol=1e-6
        )

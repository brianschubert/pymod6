import pymod6._exec
import pymod6.input as mod_input


def test_files_exist_legacy_text(modtran_exec) -> None:
    input_json = (
        mod_input.ModtranInputBuilder()
        .add_case(mod_input.basecases.VNIR)
        .finish_case()
        .build_json_input(output_legacy=True)
    )

    result_files: pymod6._exec._ResultFiles
    result_proc, [result_files] = modtran_exec.run_all_cases(input_json)

    assert result_proc.returncode == 0

    assert [f.name for f in result_files.all(only_existing=True)] == [
        "case0.acd",
        "case0.tp7",
        "case0.tp6",
        "case0.7sc",
        "case0._pth",
        "case0.plt",
        "case0.psc",
        "case0.wrn",
    ]


def test_files_exist_legacy_binary(modtran_exec) -> None:
    input_json = (
        mod_input.ModtranInputBuilder()
        .add_case(mod_input.basecases.VNIR)
        .finish_case()
        .build_json_input(output_legacy=True, binary=True)
    )

    result_files: pymod6._exec._ResultFiles
    result_proc, [result_files] = modtran_exec.run_all_cases(input_json)

    assert result_proc.returncode == 0

    assert [f.name for f in result_files.all(only_existing=True)] == [
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


def test_files_exist_sli(modtran_exec) -> None:
    input_json = (
        mod_input.ModtranInputBuilder()
        .add_case(mod_input.basecases.VNIR)
        .finish_case()
        .build_json_input(output_sli=True)
    )

    result_files: pymod6._exec._ResultFiles
    result_proc, [result_files] = modtran_exec.run_all_cases(input_json)

    assert result_proc.returncode == 0

    assert [f.name for f in result_files.all(only_existing=True)] == [
        "case0.hdr",
        "case0.sli",
        "case0_flux.hdr",
        "case0_flux.sli",
    ]


def test_files_exist_csv(modtran_exec) -> None:
    input_json = (
        mod_input.ModtranInputBuilder()
        .add_case(mod_input.basecases.VNIR)
        .finish_case()
        .build_json_input(output_csv=True)
    )

    result_files: pymod6._exec._ResultFiles
    result_proc, [result_files] = modtran_exec.run_all_cases(input_json)

    assert result_proc.returncode == 0

    assert [f.name for f in result_files.all(only_existing=True)] == [
        "case0.csv",
    ]


def test_files_exist_json(modtran_exec) -> None:
    for json_opt in mod_input.JSONPrintOpt:
        input_json = (
            mod_input.ModtranInputBuilder()
            .add_case(mod_input.basecases.VNIR)
            .finish_case()
            .build_json_input(json_opt=json_opt)
        )

        result_files: pymod6._exec._ResultFiles
        result_proc, [result_files] = modtran_exec.run_all_cases(input_json)

        assert result_proc.returncode == 0

        output_files = [f.name for f in result_files.all(only_existing=True)]

        if json_opt == mod_input.JSONPrintOpt.WRT_NONE:
            assert output_files == []
        else:
            assert output_files == ["case0.json"]

            output_json = mod_input.read_json_input(result_files.json.read_text())
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

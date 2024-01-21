import pymod6._exec
import pymod6.input as mod_input


def test_legacy_files_exist(modtran_exec) -> None:
    input_json = (
        mod_input.ModtranInputBuilder()
        .add_case(mod_input.basecases.VNIR)
        .finish_case()
        .build_json_input(output_legacy=True)
    )

    result_files: pymod6._exec._ResultFiles
    result_proc, [result_files] = modtran_exec.run_all_cases(input_json)

    assert result_proc.returncode == 0

    assert result_files.acd_text.exists()
    assert result_files.tape7_text.exists()
    assert result_files.wrn.exists()

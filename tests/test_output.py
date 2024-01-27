import copy

import numpy as np
import pytest

import pymod6._exec
import pymod6.input as mod_input
import pymod6.output as mod_output
import pymod6.output._nav


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

    case_files: pymod6.output._nav.CaseResultFilesNavigator
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

    case_files: pymod6.output._nav.CaseResultFilesNavigator
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

    case_files: pymod6.output._nav.CaseResultFilesNavigator
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

    case_files: pymod6.output._nav.CaseResultFilesNavigator
    result_proc, [case_files] = modtran_exec.run(input_json, work_dir=tmp_path)

    assert result_proc.returncode == 0
    assert "Error" not in result_proc.stdout

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


@pytest.mark.parametrize("mode", list(mod_input.RTExecutionMode))
def test_tape7_sli_json_match(modtran_exec, tmp_path, mode, simple_case) -> None:
    if mode in (
        mod_input.RTExecutionMode.RT_SOLAR_IRRADIANCE,
        mod_input.RTExecutionMode.RT_LUNAR_IRRADIANCE,
    ):
        pytest.skip("irradiance mode not yet supported")

    input_json = (
        mod_input.ModtranInputBuilder()
        .add_case(
            simple_case,
            RTOPTIONS__IEMSCT=mode,
            # RTOPTIONS__IMULT=mod_input.RTMultipleScattering.RT_NO_MULTIPLE_SCATTER,
        )
        .finish_case()
        .build_json_input(output_sli=True, json_opt=mod_input.JSONPrintOpt.WRT_OUTPUT)
    )

    result = modtran_exec.run(input_json, work_dir=tmp_path)
    assert result.process.returncode == 0
    assert "Error" not in result.process.stdout

    case_files: pymod6.output._nav.CaseResultFilesNavigator
    [case_files] = result.cases_output_files

    # Read SLI spectral library formatted outputs.
    sli_data = mod_output.read_sli(case_files.sli_header)

    # Read JSON formatted outputs.
    json_case = mod_input.read_json_input(case_files.json.read_text())["MODTRAN"][0]
    json_data = json_case["MODTRANOUTPUT"]["SPECTRA"][mode.spectral_output_keyword]

    # Mapping between SLI spectra names and their corresponding JSON output keywords.
    sli2json = {
        # Transmission
        "combin trans": "TOT_TRANS",
        "H2O trans": "TRANS_H2O",
        "umix trans": "TRANS_UMIX",
        "O3 trans": "TRANS_O3",
        "trace trans": "TRANS_TRACE",
        "N2 trans": "CONT_N2",
        "H2Ocnt trans": "CONT_H2O",
        "molec scat": "MOLEC_SCAT",
        "aercld trans": "TRANS_AERCLD",
        "HNO3 trans": "TRANS_HNO3",
        "aercld abtrns": "ABTRNS_AERCLD",
        "CO2 trans": "TRANS_CO2",
        "CO trans": "TRANS_CO",
        "CH4 trans": "TRANS_CH4",
        "N2O trans": "TRANS_N2O",
        "O2 trans": "TRANS_O2",
        "NH3 trans": "TRANS_NH3",
        "NO trans": "TRANS_NO",
        "NO2 trans": "TRANS_NO2",
        "SO2 trans": "TRANS_SO2",
        "cloud trans": "TRANS_CLOUD",
        "F11 trans": "TRANS_CFC11",
        "F12 trans": "TRANS_CFC12",
        "CCl3F trans": "TRANS_CFC13",
        "CF4 trans": "TRANS_CFC14",
        "F22 trans": "TRANS_CFC22",
        "F113 trans": "TRANS_CFC113",
        "F114 trans": "TRANS_CFC114",
        "F115 trans": "TRANS_CFC115",
        "ClONO2 trans": "TRANS_CLONO2",
        "HNO4 trans": "TRANS_HNO4",
        "CHCl2F trans": "TRANS_CHCL2F",
        "CCl4 trans": "TRANS_CCL4",
        "N2O5 trans": "TRANS_N2O5",
        "H2-H2 trans": "TRANS_H2_H2",
        "H2-He trans": "TRANS_H2_HE",
        "H2-CH4 trans": "TRANS_H2_CH4",
        "CH4-CH4 trans": "TRANS_CH4_CH4",
        # Radiance
        "total transmittance": "TOT_TRANS",
        "path emission": "THRML_EM",
        "path thermal scat": "THRML_SCT",
        "surface emission": "SURF_EMIS",
        "path multiple scat": "MULT_SCAT",
        "path single scat": "SING_SCAT",
        "ground reflect": "GRND_RFLT",
        "direct reflect": "DRCT_RFLT",
        "total radiance": "TOTAL_RAD",
        "reference irradiance": "REF_SOL",
        "irradiance at observer": "SOL_AT_OBS",
        "- nat log path trans": "DEPTH",
        "directional emissivity": "DIR_EM",
        "top-of-atmosphere irradiance": "TOA_RAD",
        "brightness temp": "BBODY_TK",
    }

    for sli_var in sli_data.data_vars.values():
        np.testing.assert_allclose(
            sli_var.data, json_data[sli2json[sli_var.name]], rtol=1e-5, atol=1e-6
        )


@pytest.mark.parametrize("mode", list(mod_input.RTExecutionMode))
def test_tape7_sli_binary_match(modtran_exec, tmp_path, mode, simple_case) -> None:
    if mode in (
        mod_input.RTExecutionMode.RT_SOLAR_IRRADIANCE,
        mod_input.RTExecutionMode.RT_LUNAR_IRRADIANCE,
    ):
        pytest.skip("irradiance mode not yet supported")

    input_json = (
        mod_input.ModtranInputBuilder()
        .add_case(
            simple_case,
            RTOPTIONS__IEMSCT=mode,
            # RTOPTIONS__IMULT=mod_input.RTMultipleScattering.RT_NO_MULTIPLE_SCATTER,
        )
        .finish_case()
        .build_json_input(output_legacy=True, binary=True, output_sli=True)
    )
    result = modtran_exec.run(input_json, work_dir=tmp_path)
    assert result.process.returncode == 0
    assert "Error" not in result.process.stdout

    case_files: pymod6.output._nav.CaseResultFilesNavigator
    [case_files] = result.cases_output_files

    # Read SLI spectral library formatted outputs.
    sli_data = mod_output.read_sli(case_files.sli_header)

    # Read binary tape7 spectral outputs.
    binary_data = mod_output.read_tape7_binary(case_files.tape7_binary)

    for field_name in binary_data.dtype.names:
        if (
            mode == mod_input.RTExecutionMode.RT_TRANSMITTANCE
            and field_name == "-log combin"
        ):
            # Only present in .tp7 text and binary files. Not included in .csv or SLI outputsl.
            continue

        if field_name == "freq":
            sli_name = "wavelength"
        else:
            sli_name = field_name

        np.testing.assert_allclose(
            binary_data[field_name], sli_data[sli_name], rtol=1e-8, atol=1e-14
        )

import numpy as np
import pytest

import pymod6.io
import pymod6.output
from pymod6.input import schema as mod_schema


def test_load_input_defaults(modtran_env) -> None:
    pymod6.io.load_input_defaults(modtran_env.data)


@pytest.mark.parametrize("algo", list(mod_schema.RTAlgorithm))
def test_acd_text_binary_match(modtran_exec, tmp_path, algo, simple_case) -> None:
    input_acd_text = (
        pymod6.input.ModtranInputBuilder()
        .add_case(simple_case, RTOPTIONS__MODTRN=algo)
        .build_json_input(output_legacy=True, binary=False)
    )
    input_acd_binary = (
        pymod6.input.ModtranInputBuilder()
        .add_case(simple_case, RTOPTIONS__MODTRN=algo)
        .build_json_input(output_legacy=True, binary=True)
    )

    acd_text = pymod6.io.read_acd_text(
        modtran_exec.run(input_acd_text, work_dir=tmp_path)
        .cases_output_files[0]
        .acd_text,
    )

    acd_binary = pymod6.io.read_acd_binary(
        modtran_exec.run(input_acd_binary, work_dir=tmp_path)
        .cases_output_files[0]
        .acd_binary
    )

    for field_name in acd_binary.dtype.names:
        np.testing.assert_allclose(
            acd_text[field_name], acd_binary[field_name], atol=5e-6, rtol=1e-6
        )


@pytest.mark.parametrize("mode", list(mod_schema.RTExecutionMode))
def test_tape7_sli_json_match(
    modtran_exec, tmp_path, mode, simple_case, helpers
) -> None:
    if mode in (
        mod_schema.RTExecutionMode.RT_SOLAR_IRRADIANCE,
        mod_schema.RTExecutionMode.RT_LUNAR_IRRADIANCE,
    ):
        pytest.skip("irradiance mode not yet supported")

    input_json = (
        pymod6.input.ModtranInputBuilder()
        .add_case(
            simple_case,
            RTOPTIONS__IEMSCT=mode,
            # RTOPTIONS__IMULT=mod_input.RTMultipleScattering.RT_NO_MULTIPLE_SCATTER,
        )
        .build_json_input(output_sli=True, json_opt=mod_schema.JSONPrintOpt.WRT_OUTPUT)
    )

    case_files = helpers.run_single_checked(modtran_exec, input_json, tmp_path)

    # Read SLI spectral library formatted outputs.
    sli_data = pymod6.io.read_sli(case_files.sli_header)

    # Read JSON formatted outputs.
    json_case = pymod6.io.read_json_input(case_files.json.read_text())["MODTRAN"][0]
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


@pytest.mark.parametrize("mode", list(mod_schema.RTExecutionMode))
def test_tape7_sli_binary_match(
    modtran_exec, tmp_path, mode, simple_case, helpers
) -> None:
    if mode in (
        mod_schema.RTExecutionMode.RT_SOLAR_IRRADIANCE,
        mod_schema.RTExecutionMode.RT_LUNAR_IRRADIANCE,
    ):
        pytest.skip("irradiance mode not yet supported")

    input_json = (
        pymod6.input.ModtranInputBuilder()
        .add_case(
            simple_case,
            RTOPTIONS__IEMSCT=mode,
            # RTOPTIONS__IMULT=mod_input.RTMultipleScattering.RT_NO_MULTIPLE_SCATTER,
        )
        .build_json_input(output_legacy=True, binary=True, output_sli=True)
    )
    case_files = helpers.run_single_checked(modtran_exec, input_json, tmp_path)

    # Read SLI spectral library formatted outputs.
    sli_data = pymod6.io.read_sli(case_files.sli_header)

    # Read binary tape7 spectral outputs.
    binary_data = pymod6.io.read_tape7_binary(case_files.tape7_binary)

    for field_name in binary_data.dtype.names:
        if (
            mode == mod_schema.RTExecutionMode.RT_TRANSMITTANCE
            and field_name == "-log combin"
        ):
            # Only present in .tp7 text and binary files. Not included in .csv, SLI, or JSON outputs.
            continue

        sli_name = "wavelength" if field_name == "freq" else field_name

        np.testing.assert_allclose(
            binary_data[field_name], sli_data[sli_name], rtol=1e-8, atol=1e-14
        )

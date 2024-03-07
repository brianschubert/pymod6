from __future__ import annotations

import datetime
from typing import NamedTuple

from typing_extensions import Unpack

from pymod6 import _util
from pymod6.input import _util as _input_util
from pymod6.input import schema as _schema


class ModtranInputBuilder:
    """
    Builder for MODTRAN JSON input structures.

    This class assists with programmatically constructing multi-case MODTRAN inputs.
    It has several advantages over manually constructing input dictionaries:
    * Automatic case naming.
    * Automatic deep copying to prevent object aliasing issues.
    * Runtime validation of cases against the expected schema.
    * Type hints for better static analysis and code completion.
    * Support for defining cases that inherit from a template (`"CASE TEMPLATE": ...`).
    * Streamlined `"FILEOPTIONS"` configuration, ensuring consistent output files across
      all cases.
    """

    _cases: list[_schema.CaseInput]

    _root_name_format: str

    # TODO: per arg?
    _validate: bool

    def __init__(
        self,
        *,
        root_name_format: str = "case{case_index:0{case_digits}}",  # {timestamp:%Y-%m-%dT%H-%M-%S}_
        validate: bool = True,
    ) -> None:
        """
        Create a new `ModtranInputBuilder`.

        Parameters
        ----------
        root_name_format : str
            Format string for the `<ROOTNAME>` of the case output files.
            Accepts the following formatting keyword arguments:
            * `case_index` (int): index of the case.
            * `case_digits` (int): integer number of decimal digits needed to represent all
                case indices.
            * `timestamp` (`datetime.datetime`): timestamp of the input structure
                creation time. Same for all cases.
        validate : bool, optional
            Whether to validate each added case against the expected schema.
            Defaults to `True`.
        """
        self._cases = []
        self._root_name_format = root_name_format
        self._validate = validate

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(<{len(self._cases)} cases>)"

    def add_case(
        self,
        case_input: _schema.CaseInput,
        **kwargs: Unpack[_schema.CaseInput],
    ) -> ModtranInputBuilder:
        """
        Add a new case to this builder.

        Parameters
        ----------
        case_input : pymod6.input.schema.ModtranInput
            Case input dictionary. Defines the base input values.
            Entries can be added/overriden by passing additional keyword arguments.
            Pass an empty dictionary if all input values are defined with keywords
            arguments.
        make_copy : bool, optional
            Whether to make a copy of the passed `case_input` dictionary.
            Defaults to `True`.
            This method mutates the passed dictionary in-place, so this option should
            always be set to `True` unless you are certain that the input dictionary
            is not referenced elsewhere. Setting this option to `False` can
            provide a performance advantage when it is safe to modify the passed
            dictionary in-place.
        **kwargs : dunder-delimited keywords
            JSON input keyword-value pairs to be applied in addition to those specified
            in the `case_input` dictionary. Keyword nesting is indicated by a
            double-underscore `__`. For example, the JSON input keyword
            `SPECTRAL.V1` can be specified by passing the keyword argument
            `SPECTRAL__V1`.

        Returns
        -------
        Self
            This builder object to support method chaining.

        Examples
        --------

        Create an input structure with a single case that uses the default options:
        >>> import pymod6
        >>> builder = pymod6.input.ModtranInputBuilder()
        >>> builder.add_case({})
        ModtranInputBuilder(<1 cases>)
        >>> builder.build_json_input()
        {'MODTRAN': [{'MODTRANINPUT': {'NAME': 'case0', 'CASE': 0, ...}}]}
        """
        _handle = self.add_template_case(case_input, **kwargs)
        return self

    def add_template_case(
        self,
        case_input: _schema.CaseInput,
        **kwargs: Unpack[_schema.CaseInput],
    ) -> TemplateCaseHandle:
        """
        Add a new template case to this builder.

        Exactly the same as `add_case`, but returns a case handle object instead of the
        builder object. This handle object can be used to define new cases that use the
        case added by this method as a template.

        .. note::
            Template cases are ordinary cases, and are run by MODTRAN like any other
            case.

        Returns
        -------
        handle : pymod6.input.TemplateCaseHandle
            Handle object referencing the added case.

        Examples
        --------

        >>> import pymod6
        >>> builder = pymod6.input.ModtranInputBuilder()
        >>> handle = builder.add_template_case({})
        >>> print(handle)
        TemplateCaseHandle(builder=ModtranInputBuilder(<1 cases>), case_index=0)
        """

        case_input = _input_util.merge_case_parts(
            case_input,
            _input_util.make_case(**kwargs),
            allow_override=True,
        )

        if self._validate:
            case_input = _util.make_adapter(_schema.CaseInput).validate_python(
                case_input
            )

        index = self._register_case(case_input)
        return TemplateCaseHandle(self, index)

    def build_json_input(
        self,
        *,
        output_legacy: bool = False,
        output_sli: bool = False,
        output_csv: bool = False,
        outupt_corrk: bool = False,
        binary: bool = False,
        json_opt: _schema.JSONPrintOpt = _schema.JSONPrintOpt.WRT_STAT_INPUT,
        unify_json: bool = False,
        unify_csv: bool = False,
    ) -> _schema.JSONInput:
        """
        Construct a complete JSON input structure.

        Parameters
        ----------
        output_legacy : bool, optional
            Whether to output legacy output files (tape7, acd, ...).
            Controls `FILEOPTIONS.NOFILE`.
        output_sli : bool, optional
            Whether to write spectra outputs to ENVI spectral library files.
            Controls `FILEOPTIONS.SLIPRNT`.
        output_csv : bool, optional
            Whether to write spectra outputs to CSV files.
            Controls `FILEOPTIONS.CSVPRNT`.
        outupt_corrk : bool, optional
            Whether to output correlated-k / line-by-line files.
            Controls `FILEOPTIONS.CKPRNT`.
            Note that correlated-k / line-by-line must be enabled by other options
            in order for these files to be generated.
        binary : bool, optional
            Whether to generate legacy and correlated-k output files in binary format.
            Controls `FILEOPTIONS.BINARY`.
        json_opt : bool, optional
            Type of JSON output. Controls `FILEOPTIONS.JSONOPT`.
        unify_json : bool, optional
            If set to `True`, all JSON outputs will be written to a single
            `all_cases.json` file. Otherwise, individual `<ROOTNAME>.JSON` files will
            be generated for each case.
        unify_csv : bool, optional
            If set to `True`, all CSV outputs will be written to a single
            `all_cases[_<suffix>].csv` file. Otherwise, individual
            `<ROOTNAME>[_<suffix>].csv` files will be generated for each case.

        Returns
        -------
        pymod6.input.schema.JSONInput
            Complete JSON input structure.
        """
        case_digits = _util.num_digits(len(self._cases) - 1)

        for case in self._cases:
            root_name = self._root_name_format.format(
                case_index=case["CASE"],
                case_digits=case_digits,
                timestamp=datetime.datetime.now(),
            )

            case.setdefault("NAME", root_name)

            file_options: _schema.FileOptions = case.setdefault("FILEOPTIONS", {})
            file_options["FLROOT"] = root_name

            file_options["JSONPRNT"] = (
                "all_cases.json" if unify_json else f"{root_name}.json"
            )
            file_options["JSONOPT"] = json_opt

            file_options["NOFILE"] = 0 if output_legacy else 2

            if output_sli:
                file_options["SLIPRNT"] = root_name

            if output_csv:
                file_options["CSVPRNT"] = (
                    "all_cases.csv" if unify_csv else f"{root_name}.csv"
                )

            file_options["BINARY"] = binary
            file_options["CKPRNT"] = outupt_corrk

        input_json: _schema.JSONInput = _input_util.input_from_cases(self._cases)
        if self._validate:
            return _util.make_adapter(_schema.JSONInput).validate_python(input_json)

        return input_json

    def _next_index(self) -> int:
        return len(self._cases)

    def _register_case(self, case: _schema.CaseInput) -> int:
        index = self._next_index()
        case["CASE"] = index
        self._cases.append(case)
        return index


class TemplateCaseHandle(NamedTuple):
    """Handle object for a case added to a `ModtranInputBuilder`."""

    builder: ModtranInputBuilder
    """Builder object this case handle is associated with."""

    case_index: int
    """Index of this case in the builder's case sequence."""

    def extend(
        self,
        case_extension: _schema.CaseInput | None = None,
        **kwargs: Unpack[_schema.CaseInput],
    ) -> TemplateCaseHandle:
        """
        Add a new case to the associated builder using this case as a template.

        Parameters have the same meaning as in `ModtranInputBuilder.add_case`.
        """
        if case_extension is None:
            case_extension = {}

        case_extension = _input_util.merge_case_parts(
            case_extension, _input_util.make_case(**kwargs)
        )

        case_extension["CASE TEMPLATE"] = self.case_index
        self.builder.add_case(case_extension)
        return self

    def finish_template(self) -> ModtranInputBuilder:
        """
        Return the associated builder object.

        Call to finish a sequence `extend` invocations when using
        method chaining to build a multi-case input structure in a single statement.

        Returns
        -------
        ModtranInputBuilder
            Associated builder object.
        """
        return self.builder

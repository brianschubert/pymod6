"""
Misc utilities for handling case inputs.
"""

from __future__ import annotations

import copy
import itertools
from collections.abc import Collection
from typing import Any, Iterable, Iterator, cast

import numpy as np
import pydantic

from pymod6 import _util
from pymod6.input import schema as _schema


def make_case(
    *,
    validate: bool = True,
    **kwargs: Any,
) -> _schema.CaseInput:
    """
    Construct a case-input dictionary from keyword-value pairs.

    Nested case-input keywords are specified using double-underscore (`__`)
    delimited keyword arguments. For example, the JSON input keyword
    `SPECTRAL.V1` can be specified by passing the keyword argument
    `SPECTRAL__V1`.

    Parameters
    ----------
    validate : bool, optional
        Whether to validate the constructed case against the expected schema before
        returning. Defaults to `True`.
    **kwargs : dunder-delimited keywords
        Case-input keyword-value pairs. Keyword nesting is indicated by a
        double-underscore `__`.

    Returns
    -------
    pymod6.input.schema.CaseInput
        Case input dictionary

    Examples
    --------
    >>> make_case(NAME="foo", SPECTRAL__V1=4000.0, SPECTRAL__V2=5000.0)
    {'NAME': 'foo', 'SPECTRAL': {'V1': 4000.0, 'V2': 5000.0}}

    """
    case_dict: _schema.CaseInput = {}
    for key, value in kwargs.items():
        _util.assign_nested_mapping(
            cast("dict[str, Any]", case_dict), key.split("__"), value
        )

    if validate:
        case_dict = _util.make_adapter(_schema.CaseInput).validate_python(case_dict)

    return case_dict


def merge_case_parts(
    *case_inputs: _schema.CaseInput,
    validate: bool = True,
    allow_override: bool = False,
) -> _schema.CaseInput:
    """
    Combine partially-specified case-input dictionaries.

    This function merges togethor partially-specified case-input dictionaries
    into a single case-input dictionary. The partial case-input dictionaries can be
    given either as dictionary objects passed as positional arguments or can be
    specified using keyword arguments with dunder-delimited nested keywords.

    By default, this function requires all input keywords to be specified uniquely.
    This can be overriden by passing `allow_override=True`, in which case the last
    definition of each input keyword will take effect.

    Parameters
    ----------
    *case_inputs : pymod6.input.schema.CaseInput
        Partial case-input dictionaries. These dictionaries are recursively merged
        together to form the total case input dictionary. Often, these will include
        one or more base cases from `pymod6.input.basecases`.
        Additional entries can be added or overriden by passing keyword arguments.
    validate : bool, optional
        Whether to validate the constructed case against the expected schema before
        returning. Defaults to `True`.
    allow_override : bool, optional
        When `False`, each input keyword must be specified uniquely among all arguments.
        Otherwise, a `ValueError` is raised. When `True`, the last definition of each
        input keyword among all arguments will be used, where the `case_inputs` are
        processed in the order they are passed and the keyword arguments are processed
        last.


    Returns
    -------
    pymod6.input.schema.CaseInput
        Case input dictionary.

    Examples
    --------

    You can merge a collection of partially-specified case-input dictionaries by
    passing them as positional arguments:
    >>> part_1 = {"NAME": "foo"}
    >>> part_2 = {"SPECTRAL": {"V1": 4000.0, "V2": 5000.0},}
    >>> part_3 = {"SPECTRAL": {"DV": 1.0, "FWHM": 2.0}}
    >>> merge_case_parts(part_1, part_2, part_3)
    {'NAME': 'foo', 'SPECTRAL': {'V1': 4000.0, 'V2': 5000.0, 'DV': 1.0, 'FWHM': 2.0}}

    You can combine custom case-input dictionaries with base cases from
    `pymod6.input.basecases`:
    >>> from pymod6.input import basecases
    >>> my_case = {"NAME": "foo"}
    >>> merge_case_parts(my_case, basecases.SPECTRAL_SWIR)
    {'NAME': 'foo', 'SPECTRAL': {'V1': 4000.0, 'V2': 7143.0}}

    By default, multiple definitions of an input keywords are not permitted:
    >>> merge_case_parts(
    ...     basecases.SPECTRAL_SWIR,  # specifies SPECTRAL.{V1,V2}
    ...     make_case(SPECTRAL__V2=5000.0),      # attempts to override SPECTRAL.V2
    ... )
    Traceback (most recent call last):
    ...
    ValueError: found multiple definitions for ('SPECTRAL', 'V2'). Pass allow_override=True to suppress this error and have the last definition take effect.

    To allow duplicate defintiions to override previous ones, pass `allow_override=True`:
    >>> merge_case_parts(
    ...     basecases.SPECTRAL_SWIR,  # specifies SPECTRAL.{V1,V2}
    ...     make_case(SPECTRAL__V2=5000.0),      # attempts to override SPECTRAL.V2
    ...     allow_override=True,
    ... )
    {'SPECTRAL': {'V1': 4000.0, 'V2': 5000.0}}

    Constructed cases are validated against the expected schema by default:
    >>> merge_case_parts({"SPECTRAL": {"V1": "bad type", "V3": "extraneous"}})
    Traceback (most recent call last):
    ...
    pydantic_core._pydantic_core.ValidationError: 2 validation errors for typed-dict
    SPECTRAL.V1
      Input should be a valid number, unable to parse string as a number [type=float_parsing, input_value='bad type', input_type=str]
        ...
    SPECTRAL.V3
      Extra inputs are not permitted [type=extra_forbidden, input_value='extraneous', input_type=str]
        ...

    Pass `validate=False` to disable validation:
    >>> merge_case_parts({"SPECTRAL": {"V1": "bad type", "V3": "extraneous"}}, validate=False)
    {'SPECTRAL': {'V1': 'bad type', 'V3': 'extraneous'}}
    """

    case: _schema.CaseInput = {}
    try:
        _util.merge_nested_mappings(
            cast("dict[str, Any]", case),
            *case_inputs,
            allow_override=allow_override,
        )
    except _util.MappingMergeError as ex:
        raise ValueError(
            f"found multiple definitions for {ex.key_path}."
            f" Pass allow_override=True to suppress this error and have the last"
            f" definition take effect."
        ) from ex

    if validate:
        case = _util.make_adapter(_schema.CaseInput).validate_python(case)

    return case


def input_from_cases(cases: Iterable[_schema.CaseInput]) -> _schema.JSONInput:
    """
    Create a complete JSON input dictionary from a series of input cases.

    This function *does not* validate the provided case-input dictionaries against
    the expected schema.

    Parameters
    ----------
    cases : iterable of pymod6.input.schema.CaseInput
        Iterable of case inputs.

    Returns
    -------
    pymod6.input.schema.JSONInput
            Complete JSON input structure.

    Examples
    --------
    >>> case_0 = {"NAME": "case 0"}
    >>> case_1 = {"NAME": "case 1"}
    >>> input_from_cases([case_0, case_1])
    {'MODTRAN': [{'MODTRANINPUT': {'NAME': 'case 0'}}, {'MODTRANINPUT': {'NAME': 'case 1'}}]}
    """
    if isinstance(cases, dict):
        raise TypeError(
            "expected iterable of dicts, got single dict."
            " Pass a list of length 1 to create a JSON input with a single case."
        )
    return {"MODTRAN": [{"MODTRANINPUT": c} for c in cases]}


def generate_grid_sweep(
    base: _schema.CaseInput,
    sweep_axes: Iterable[tuple[str | tuple[str, ...], Collection[Any]]],
) -> Iterator[tuple[tuple[int, ...], _schema.CaseInput]]:
    """
    Generate variations of a base case by sweeping through a Cartesian product
    of possible parameter values.

    Parameters
    ----------
    base : pymod6.input.schema.CaseInput
        Base input case.
    sweep_axes : iterable of tuples
        Iterable of tuples describing the input keywords to be swept.
        The first element should be the input keyword, given either as a tuple of
        strings or as a dunder-delimianted string. The second element should be an
        iterable of values that the input keyword should taken on during the sweep.

    Returns
    -------
    iterator of tuples
        Iterator yielding tuples of sweep index and input dictionary values.


    Examples
    --------
    >>> import pprint
    >>> base_case = {"NAME": "foo"}
    >>> sweep_axes = [
    ...     ("ATMOSPHERE__H2OSTR", [1, 2]),
    ...     ("ATMOSPHERE__O3STR", [1, 2]),
    ... ]
    >>> sweep_inputs = list(generate_grid_sweep(base_case,  sweep_axes))
    >>> pprint.pprint(sweep_inputs, sort_dicts=False)
    [((0, 0), {'NAME': 'foo', 'ATMOSPHERE': {'H2OSTR': 1, 'O3STR': 1}}),
     ((0, 1), {'NAME': 'foo', 'ATMOSPHERE': {'H2OSTR': 1, 'O3STR': 2}}),
     ((1, 0), {'NAME': 'foo', 'ATMOSPHERE': {'H2OSTR': 2, 'O3STR': 1}}),
     ((1, 1), {'NAME': 'foo', 'ATMOSPHERE': {'H2OSTR': 2, 'O3STR': 2}})]
    """

    sweep_keys, sweep_values = zip(*sweep_axes)
    sweep_keys = [k.split("__") if isinstance(k, str) else k for k in sweep_keys]
    shape = tuple(map(len, sweep_values))

    for index, values in zip(np.ndindex(shape), itertools.product(*sweep_values)):
        case = copy.deepcopy(base)
        for key, val in zip(sweep_keys, values):
            _util.assign_nested_mapping(cast("dict[str, Any]", case), key, val)
        yield index, case

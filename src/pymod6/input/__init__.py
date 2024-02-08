"""
Input file construction and handling.

* `pymod6.input.basecases` - Prototypes for common input cases.
* `pymod6.input.schema` - JSON input file schema.

See Also
--------
pymod6.io.read_json_input : Reading inputs from JSON strings.
pymod6.io.load_input_defaults : Load input keyword defaults.
"""

from . import basecases, schema
from ._builder import ModtranInputBuilder, TemplateCaseHandle
from ._util import input_from_cases, make_case, merge_case_parts

__all__ = [
    "basecases",
    "schema",
    # Utilities
    "make_case",
    "merge_case_parts",
    "input_from_cases",
    # Builder
    "ModtranInputBuilder",
    "TemplateCaseHandle",
]

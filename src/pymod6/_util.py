import io
from typing import Any, BinaryIO, TextIO

from typing_extensions import TypeGuard


def is_binary_io(obj: Any) -> TypeGuard[BinaryIO]:
    return isinstance(obj, (io.RawIOBase, io.BufferedIOBase))


def is_text_io(obj: Any) -> TypeGuard[TextIO]:
    return isinstance(obj, io.TextIOBase)

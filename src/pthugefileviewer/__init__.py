"""A console regular expression editor"""

import importlib.metadata

from .hugefilevieweruicontrol import (
    HugeFileViewerRegexUIControl,
    HugeFileViewerUIControl,
)


def version() -> str:
    return importlib.metadata.version("pthugefileviewer")


__all__ = [
    "version",
    "HugeFileViewerUIControl",
    "HugeFileViewerRegexUIControl",
]

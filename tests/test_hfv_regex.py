"""HugeFileViewerRegexUIControl tests"""

import re
import tempfile
import unittest
from typing import List

from pthugefileviewer.hugefilevieweruicontrol import HugeFileViewerRegexUIControl


def tobytes(lines: List[str]) -> List[bytes]:
    return [bytes(line, "ascii") for line in lines]


class Base:
    def controlFor(self, height: int, contents: bytes) -> HugeFileViewerRegexUIControl:
        with tempfile.TemporaryFile() as fd:
            fd.write(contents)
            fd.flush()
            control = HugeFileViewerRegexUIControl(fd)
            control.height = height
            return control

    def controlLines(
        self, height: int, lines: List[str], newlines: int = 0
    ) -> HugeFileViewerRegexUIControl:
        suffix = b"\n" * newlines
        return self.controlFor(height, b"\n".join(tobytes(lines)) + suffix)

    def controlNums(
        self, height: int, limit: int, newlines: int = 0
    ) -> HugeFileViewerRegexUIControl:
        return self.controlLines(height, [f"{i}" for i in range(limit)], newlines)


class TestBasic(unittest.TestCase, Base):
    def test_matchnone(self) -> None:
        control = self.controlLines(2, ["abc", "def", "ghi"], 0)
        self.assertEqual(control.get_lines_style(), [[("", "abc")], [("", "def")]])

    def test_matchall_oneline(self) -> None:
        control = self.controlLines(2, ["abc", "def", "ghi"], 0)
        control.use_regex(re.compile(b"abc"))
        self.assertEqual(
            control.get_lines_style(),
            [[("class:match", "abc")], [("", "def")]],
        )

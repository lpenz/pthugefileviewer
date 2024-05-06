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

    def test_matchall_lines(self) -> None:
        control = self.controlLines(2, ["abc", "def", "ghi"], 0)
        control.use_regex(re.compile(b"abc"))
        self.assertEqual(
            control.get_lines_style(),
            [[("class:match", "abc")], [("", "def")]],
        )

    def test_matchall_line2(self) -> None:
        control = self.controlLines(2, ["abc", "def", "ghi"], 0)
        control.use_regex(re.compile(b"def"))
        self.assertEqual(
            control.get_lines_style(),
            [[("", "abc")], [("class:match", "def")]],
        )

    def test_matchall_line3(self) -> None:
        control = self.controlLines(2, ["abc", "def", "ghi"], 0)
        control.use_regex(re.compile(b"ghi"))
        self.assertEqual(
            control.get_lines_style(),
            [[("", "abc")], [("", "def")]],
        )

    def test_matchall_line_mid(self) -> None:
        control = self.controlLines(3, ["abc", "def", "ghi", "jkl"], 0)
        control.use_regex(re.compile(b"def"))
        self.assertEqual(
            control.get_lines_style(),
            [[("", "abc")], [("class:match", "def")], [("", "ghi")]],
        )

    def test_matchall_char0(self) -> None:
        control = self.controlLines(2, ["abc", "def", "ghi"], 0)
        control.use_regex(re.compile(b"a"))
        self.assertEqual(
            control.get_lines_style(),
            [[("class:match", "a"), ("", "bc")], [("", "def")]],
        )

    def test_matchall_char1(self) -> None:
        control = self.controlLines(2, ["abc", "def", "ghi"], 0)
        control.use_regex(re.compile(b"b"))
        self.assertEqual(
            control.get_lines_style(),
            [[("", "a"), ("class:match", "b"), ("", "c")], [("", "def")]],
        )

    def test_matchall_char2(self) -> None:
        control = self.controlLines(2, ["abc", "def", "ghi"], 0)
        control.use_regex(re.compile(b"c"))
        self.assertEqual(
            control.get_lines_style(),
            [[("", "ab"), ("class:match", "c")], [("", "def")]],
        )

    def test_matchall_char3(self) -> None:
        control = self.controlLines(2, ["abc", "def", "ghi"], 0)
        control.use_regex(re.compile(b"d"))
        self.assertEqual(
            control.get_lines_style(),
            [[("", "abc")], [("class:match", "d"), ("", "ef")]],
        )

    def test_matchall_char4(self) -> None:
        control = self.controlLines(2, ["abc", "def", "ghi"], 0)
        control.use_regex(re.compile(b"f"))
        self.assertEqual(
            control.get_lines_style(),
            [[("", "abc")], [("", "de"), ("class:match", "f")]],
        )

    def test_matchall_linecross(self) -> None:
        control = self.controlLines(2, ["abc", "def", "ghi"], 0)
        control.use_regex(re.compile(b"c.?d", re.DOTALL))
        self.assertEqual(
            control.get_lines_style(),
            [[("", "ab"), ("class:match", "c")], [("class:match", "d"), ("", "ef")]],
        )

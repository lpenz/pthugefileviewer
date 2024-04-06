"""hugefilevieweruicontrol tests"""

import tempfile
import unittest
from typing import List

from pthugefileviewer.hugefilevieweruicontrol import HugeFileViewerUIControl


def tobytes(lines: List[str]) -> List[bytes]:
    return [bytes(line, "ascii") for line in lines]


class Base:
    def controlFor(self, height: int, contents: bytes) -> HugeFileViewerUIControl:
        with tempfile.TemporaryFile() as fd:
            fd.write(contents)
            fd.flush()
            control = HugeFileViewerUIControl(fd)
            control.height = height
            return control

    def controlLines(
        self, height: int, lines: List[str], newlines: int = 0
    ) -> HugeFileViewerUIControl:
        suffix = b"\n" * newlines
        return self.controlFor(height, b"\n".join(tobytes(lines)) + suffix)

    def controlNums(
        self, height: int, limit: int, newlines: int = 0
    ) -> HugeFileViewerUIControl:
        return self.controlLines(height, [f"{i}" for i in range(limit)], newlines)


class TestBasic(unittest.TestCase, Base):
    newlines = 0

    def test_no_lstrip(self) -> None:
        lines = ["    after spaces"]
        control = self.controlLines(1, lines, self.newlines)
        self.assertEqual(control.get_lines(), tobytes(lines))

    def test_too_high(self) -> None:
        control = self.controlNums(3, 1, self.newlines)
        self.assertEqual(control.get_lines(), [b"0"])

    def test_updown(self) -> None:
        control = self.controlNums(3, 5, self.newlines)
        self.assertEqual(control.get_lines(), [b"0", b"1", b"2"])
        self.assertEqual(control.get_lines(), [b"0", b"1", b"2"])
        control.go_down()
        self.assertEqual(control.get_lines(), [b"1", b"2", b"3"])
        control.go_down()
        self.assertEqual(control.get_lines(), [b"2", b"3", b"4"])
        control.go_up()
        self.assertEqual(control.get_lines(), [b"1", b"2", b"3"])
        control.go_down()
        self.assertEqual(control.get_lines(), [b"2", b"3", b"4"])
        control.go_down()
        self.assertEqual(control.get_lines(), [b"2", b"3", b"4"])
        control.go_down()
        control.go_down()
        self.assertEqual(control.get_lines(), [b"2", b"3", b"4"])

    def test_pgupdn(self) -> None:
        control = self.controlNums(3, 12, self.newlines)
        self.assertEqual(control.get_lines(), [b"0", b"1", b"2"])
        control.go_pagedown()
        self.assertEqual(control.get_lines(), [b"3", b"4", b"5"])
        control.go_pagedown()
        self.assertEqual(control.get_lines(), [b"6", b"7", b"8"])
        control.go_pagedown()
        self.assertEqual(control.get_lines(), [b"9", b"10", b"11"])
        control.go_pageup()
        self.assertEqual(control.get_lines(), [b"6", b"7", b"8"])
        control.go_pageup()
        self.assertEqual(control.get_lines(), [b"3", b"4", b"5"])
        control.go_down()
        self.assertEqual(control.get_lines(), [b"4", b"5", b"6"])
        control.go_pageup()
        self.assertEqual(control.get_lines(), [b"1", b"2", b"3"])

    def test_bottom(self) -> None:
        control = self.controlNums(3, 12, self.newlines)
        control.go_bottom()
        self.assertEqual(control.get_lines(), [b"9", b"10", b"11"])
        control.go_pageup()
        self.assertEqual(control.get_lines(), [b"6", b"7", b"8"])
        control.go_up()
        self.assertEqual(control.get_lines(), [b"5", b"6", b"7"])
        control.go_pagedown()
        self.assertEqual(control.get_lines(), [b"8", b"9", b"10"])
        control.go_pageup()
        self.assertEqual(control.get_lines(), [b"5", b"6", b"7"])
        control.go_pagedown()
        self.assertEqual(control.get_lines(), [b"8", b"9", b"10"])
        control.go_pagedown()
        self.assertEqual(control.get_lines(), [b"9", b"10", b"11"])
        control.go_pagedown()
        self.assertEqual(control.get_lines(), [b"9", b"10", b"11"])
        control.go_down()
        self.assertEqual(control.get_lines(), [b"9", b"10", b"11"])


class TestBasicNewlineAtEnd(TestBasic):
    newlines = 1


class TestGap(unittest.TestCase, Base):
    newlines = 0

    def test_updown(self) -> None:
        lines = [f"{i}" for i in range(7)]
        # Add a gap at "4"
        lines[3] = ""
        control = self.controlLines(3, lines, self.newlines)
        self.assertEqual(control.get_lines(), [b"0", b"1", b"2"])
        control.go_down()
        self.assertEqual(control.get_lines(), [b"1", b"2", b""])
        control.go_down()
        self.assertEqual(control.get_lines(), [b"2", b"", b"4"])
        control.go_down()
        self.assertEqual(control.get_lines(), [b"", b"4", b"5"])
        control.go_down()
        self.assertEqual(control.get_lines(), [b"4", b"5", b"6"])
        control.go_down()
        self.assertEqual(control.get_lines(), [b"4", b"5", b"6"])
        control.go_up()
        self.assertEqual(control.get_lines(), [b"", b"4", b"5"])
        control.go_up()
        self.assertEqual(control.get_lines(), [b"2", b"", b"4"])
        control.go_up()
        self.assertEqual(control.get_lines(), [b"1", b"2", b""])
        control.go_up()
        self.assertEqual(control.get_lines(), [b"0", b"1", b"2"])

    def test_pgupdn(self) -> None:
        lines = [f"{i}" for i in range(7)]
        # Add a gap at "4"
        lines[3] = ""
        control = self.controlLines(3, lines, self.newlines)
        self.assertEqual(control.get_lines(), [b"0", b"1", b"2"])
        control.go_pagedown()
        self.assertEqual(control.get_lines(), [b"", b"4", b"5"])
        control.go_pageup()
        self.assertEqual(control.get_lines(), [b"0", b"1", b"2"])
        control.go_down()
        self.assertEqual(control.get_lines(), [b"1", b"2", b""])
        control.go_pagedown()
        self.assertEqual(control.get_lines(), [b"4", b"5", b"6"])
        control.go_pageup()
        self.assertEqual(control.get_lines(), [b"1", b"2", b""])

    def test_bottom(self) -> None:
        lines = [f"{i}" for i in range(7)]
        # Add a gap at "4"
        lines[3] = ""
        control = self.controlLines(3, lines, self.newlines)
        control.go_bottom()
        self.assertEqual(control.get_lines(), [b"4", b"5", b"6"])
        control.go_pageup()
        self.assertEqual(control.get_lines(), [b"1", b"2", b""])
        control.go_pagedown()
        self.assertEqual(control.get_lines(), [b"4", b"5", b"6"])


class TestGapNewlineAtEnd(unittest.TestCase, Base):
    newlines = 1


class TestNewlineTopBottom(unittest.TestCase, Base):
    def test_updown(self) -> None:
        lines = [""] + [f"{i}" for i in range(7)]
        control = self.controlLines(3, lines, 3)
        self.assertEqual(control.get_lines(), [b"", b"0", b"1"])
        control.go_bottom()
        self.assertEqual(control.get_lines(), [b"6", b"", b""])
        control.go_up()
        self.assertEqual(control.get_lines(), [b"5", b"6", b""])
        control.go_down()
        self.assertEqual(control.get_lines(), [b"6", b"", b""])
        control.go_pageup()
        self.assertEqual(control.get_lines(), [b"3", b"4", b"5"])
        control.go_pagedown()
        self.assertEqual(control.get_lines(), [b"6", b"", b""])
        control.go_pageup()
        self.assertEqual(control.get_lines(), [b"3", b"4", b"5"])
        control.go_bottom()
        self.assertEqual(control.get_lines(), [b"6", b"", b""])

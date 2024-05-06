"""Control for the huge file widget"""

import io
import mmap
import re
from contextlib import contextmanager
from enum import Enum
from typing import TYPE_CHECKING, Generator, Iterator, List, Optional  # noqa: I101

from prompt_toolkit.formatted_text import StyleAndTextTuples
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.key_bindings import KeyBindingsBase
from prompt_toolkit.key_binding.key_processor import KeyPressEvent
from prompt_toolkit.layout.controls import UIContent, UIControl
from prompt_toolkit.mouse_events import MouseEvent, MouseEventType

if TYPE_CHECKING:
    from prompt_toolkit.key_binding.key_bindings import NotImplementedOrNone

E = KeyPressEvent

MAX_LINES = 1000


class HugeFileViewerUIControl(UIControl):
    """UIControl optimized for huge file visualization"""

    def __init__(self, fd: io.BufferedReader):
        self._fd = fd
        self._mm = mmap.mmap(self._fd.fileno(), 0, access=mmap.ACCESS_READ)
        self._size = self._mm.size()
        self._offset_max = 0
        self._lines: List[StyleAndTextTuples] = []
        self._height = 0
        self.update_lines()

    def close(self) -> None:
        self._mm.close()

    @property
    def offset(self) -> int:
        return self._mm.tell()

    @offset.setter
    def offset(self, offset: int) -> None:
        if offset < 0:
            offset = 0
        if offset >= self._offset_max:
            self._offset = self._offset_max
        assert (
            offset == 0 or self.get_char(offset - 1) == b"\n"
        ), f"offset {offset} char {self.get_char(offset - 1)!r}"
        self._mm.seek(offset)
        self.update_lines()

    @property
    def height(self) -> int:
        return self._height

    @height.setter
    def height(self, height: int) -> None:
        if height == self._height:
            return
        with self.tmp_offset():
            # Update self._offset_max:
            offset = self._size - 1
            for i in range(height):
                # Look at the last 2-3 pages:
                offset = self.find_prev_newline(offset)
                if offset == -1:
                    self._offset_max = 0
                    break
                self._offset_max = offset + 1
        self._height = height
        self.update_lines()

    @contextmanager
    def tmp_offset(self) -> Generator[None, None, None]:
        offset = self._mm.tell()
        try:
            yield
        finally:
            self._mm.seek(offset)

    def find_prev_newline(self, offset: int) -> int:
        start_offset = (self._size % mmap.PAGESIZE) - 2 * mmap.PAGESIZE
        return self._mm.rfind(b"\n", max(0, start_offset), offset)

    def get_lines(self) -> Iterator[bytes]:
        with self.tmp_offset():
            for _ in range(self._height):
                line = self._mm.readline()
                if not line:
                    break
                yield line.rstrip()

    def get_lines_style(self) -> List[StyleAndTextTuples]:
        return [
            [("", line.decode("utf-8", errors="replace"))] for line in self.get_lines()
        ]

    def update_lines(self) -> None:
        self._lines = self.get_lines_style()
        if self.height > len(self._lines) and self.offset < self._offset_max:
            self.go_up(self._height - len(self._lines))

    def get_char(self, offset: Optional[int] = None) -> bytes:
        with self.tmp_offset():
            if offset is not None:
                self._mm.seek(offset)
            return self._mm.read(1)

    # Implement UIControl methods:

    def _get_line(self, lineno: int) -> StyleAndTextTuples:
        if lineno >= len(self._lines):
            return [("", "")]
        return self._lines[lineno]

    def create_content(self, width: int, height: int) -> UIContent:
        self.height = height
        return UIContent(
            get_line=self._get_line,
            line_count=height,
            show_cursor=False,
        )

    def get_key_bindings(self) -> Optional[KeyBindingsBase]:
        kb = KeyBindings()
        kb.add("home")(lambda _: self.go_top())
        kb.add("c-home")(lambda _: self.go_top())
        kb.add("escape", "home")(lambda _: self.go_top())
        kb.add("end")(lambda _: self.go_bottom())
        kb.add("c-end")(lambda _: self.go_bottom())
        kb.add("escape", "end")(lambda _: self.go_bottom())
        kb.add("up")(lambda _: self.go_up())
        kb.add("down")(lambda _: self.go_down())
        kb.add("pageup")(lambda _: self.go_pageup())
        kb.add("pagedown")(lambda _: self.go_pagedown())
        return kb

    def is_focusable(self) -> bool:
        return True

    def mouse_handler(self, mouse_event: MouseEvent) -> "NotImplementedOrNone":
        if mouse_event.event_type == MouseEventType.SCROLL_UP:
            self.go_up()
        elif mouse_event.event_type == MouseEventType.SCROLL_DOWN:
            self.go_down()
        else:
            return NotImplemented
        return None

    # Exported utility functions:

    def go_line_offset(self, offset: int) -> None:
        if offset == 0 or self.get_char(offset - 1) == b"\n":
            self.offset = offset
            return
        offset = self.find_prev_newline(offset)
        if offset != -1:
            self.offset = offset + 1

    def go_top(self) -> None:
        self.offset = 0
        self.update_lines()

    def go_bottom(self) -> None:
        self.offset = self._offset_max
        self.update_lines()

    def go_up(self, lines: int = 1) -> None:
        offset = self.offset
        for i in range(lines):
            if offset == 0:
                break
            offset = self.find_prev_newline(offset - 1)
            if offset == -1:
                self.offset = 0
                break
            self.offset = offset + 1  # at the start of the next line
        self.update_lines()

    def go_down(self, lines: int = 1) -> None:
        offset = self.offset
        for _ in range(lines):
            if self.offset >= self._offset_max:
                break
            offset = self._mm.find(b"\n", offset)
            if offset == -1:
                break
            offset += 1
            self.offset = offset
        self.update_lines()

    def go_pageup(self) -> None:
        self.go_up(self.height)

    def go_pagedown(self) -> None:
        self.go_down(self.height)


OffsetEvent = Enum("OffsetEvent", ["RE_START", "RE_END", "NEWLINE", "END"])


class HugeFileViewerRegexUIControl(HugeFileViewerUIControl):
    def __init__(self, fd: io.BufferedReader):
        self.regex: Optional[re.Pattern[bytes]] = None
        self.regex_ok: Optional[re.Pattern[bytes]] = None
        HugeFileViewerUIControl.__init__(self, fd)

    def re_search(
        self, regex: re.Pattern[bytes], offset: Optional[int] = None
    ) -> Optional[re.Match[bytes]]:
        offset = offset or 0
        with self.tmp_offset():
            return regex.search(bytes(self._mm), offset)

    def use_regex(self, regex: Optional[re.Pattern[bytes]]) -> None:
        self.regex = regex
        self.update_lines()

    def search_down(self) -> None:
        if self.regex is None:
            return
        with self.tmp_offset():
            self.go_pagedown()
            offset = self.offset
        m = self.re_search(self.regex, offset)
        if m:
            self.go_line_offset(m.end())
            self.go_down(1)
        else:
            self.update_lines()

    def get_lines_style(self) -> List[StyleAndTextTuples]:
        contents = b"\n".join(self.get_lines())
        matches = []
        if self.regex is not None:
            matches = list(self.regex.finditer(contents))
        if matches:
            self.regex_ok = self.regex
            re_style = "class:match"
        elif not matches and self.regex_ok is not None:
            matches = list(self.regex_ok.finditer(contents))
            re_style = "class:oldmatch"
        else:
            re_style = ""
        offsetList = []
        for m in matches:
            offsetList.append((m.start(), OffsetEvent.RE_START))
            offsetList.append((m.end(), OffsetEvent.RE_END))
        o = 0
        while (newline := contents.find(b"\n", o)) != -1:
            offsetList.append((newline, OffsetEvent.NEWLINE))
            o = newline + 1
        offsetList.append((len(contents), OffsetEvent.END))
        offsetList.sort(key=lambda x: x[0])
        offsets: dict[int, set[OffsetEvent]] = {}
        for offset, what in offsetList:
            events = offsets.setdefault(offset, set())
            events.add(what)
            if OffsetEvent.RE_START in events and OffsetEvent.RE_END in events:
                events.remove(OffsetEvent.RE_START)
                events.remove(OffsetEvent.RE_END)
            if not events:
                offsets.pop(offset)
        linestyle = []
        current: StyleAndTextTuples = []
        styles: set[str] = set()
        o_curr = 0
        for o_next, events in offsets.items():
            if o_next > o_curr:
                current.append(
                    (" ".join(styles), contents[o_curr:o_next].decode("utf-8"))
                )
            if OffsetEvent.RE_START in events:
                styles.add(re_style)
                o_curr = o_next
            if OffsetEvent.RE_END in events:
                styles.remove(re_style)
                o_curr = o_next
            if OffsetEvent.NEWLINE in events or OffsetEvent.END in events:
                linestyle.append(current)
                current = []
                o_curr = o_next + 1
        return linestyle

"""
Parse link destination
"""

from markdown_it.common.utils import charCodeAt, unescapeAll


class _Result:
    __slots__ = ("ok", "pos", "lines", "str")

    def __init__(self):
        self.ok = False
        self.pos = 0
        self.lines = 0
        self.str = ""


def parseLinkDestination(string: str, pos: int, maximum: int) -> _Result:
    lines = 0
    start = pos
    result = _Result()

    while pos < maximum:
        code = charCodeAt(string, pos)

        if code == 0x7C: # |
            break

        if code == 0x20:
            break

        # ascii control characters
        if code < 0x20 or code == 0x7F:
            break

        if code == 0x5C and pos + 1 < maximum:      # \
            if charCodeAt(string, pos + 1) == 0x20:
                break
            pos += 2
            continue

        pos += 1

    if start == pos:
        return result

    result.str = unescapeAll(string[start:pos])
    result.lines = lines
    result.pos = pos
    result.ok = True
    return result
